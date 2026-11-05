"""Sonde OpenRouter pour MiMo-V2.6-Pro (story 1-2).

Lancer : ``uv run python -m nn_weight_writing.providers.probe`` (appels payants, clé dans
``OPENROUTER_API_KEY``) ou ``... --models-only`` (gratuit). Imprime un résumé JSON sans secret.
Le réseau (``urllib``) est séparé des fonctions pures de lecture des réponses.
"""

from __future__ import annotations

import base64
import json
import os
import re
import struct
import sys
import urllib.error
import urllib.request
import zlib
from collections.abc import Callable
from typing import Any

BASE_URL = "https://openrouter.ai/api/v1"
MODEL_ID = "xiaomi/mimo-v2.6-pro"
KEY_VAR = "OPENROUTER_API_KEY"
MAX_PROBE_USD = 0.50


# --- fonctions pures -------------------------------------------------------------------------


def find_model(models_response: dict[str, Any], model_id: str) -> dict[str, Any] | None:
    """Renvoie l'entrée de ``/models`` dont l'identifiant est exactement ``model_id``."""
    for model in models_response.get("data", []):
        if model.get("id") == model_id:
            return model
    return None


def _per_mtok(price: str | None) -> float | None:
    """Prix par jeton (chaîne OpenRouter) -> USD par million de jetons."""
    if price is None:
        return None
    return round(float(price) * 1_000_000, 6)


def summarize_model(model: dict[str, Any]) -> dict[str, Any]:
    """Prix (USD/Mtok), outils, vision et endpoints annoncés pour une entrée de ``/models``."""
    pricing = model.get("pricing", {})
    params = model.get("supported_parameters", [])
    modalities = model.get("architecture", {}).get("input_modalities", [])
    return {
        "id": model.get("id"),
        "canonical_slug": model.get("canonical_slug"),
        "context_length": model.get("context_length"),
        "input_per_mtok_usd": _per_mtok(pricing.get("prompt")),
        "output_per_mtok_usd": _per_mtok(pricing.get("completion")),
        "cache_read_per_mtok_usd": _per_mtok(pricing.get("input_cache_read")),
        "cache_write_per_mtok_usd": _per_mtok(pricing.get("input_cache_write")),
        "tools": "tools" in params and "tool_choice" in params,
        "vision": "image" in modalities,
        "input_modalities": modalities,
        "endpoints": model.get("endpoints", []),
    }


def parse_chat_usage(usage: dict[str, Any] | None) -> dict[str, Any]:
    """Lit le ``usage`` de chat completions. Champs absents : 0 ; ``cost`` absent : ``None``.

    ``prompt_tokens`` inclut les jetons lus et écrits en cache : ``input`` les retire, pour
    avoir la même sémantique que ``input_tokens`` de Messages (``Usage`` de AD-10).
    """
    usage = usage or {}
    details = usage.get("prompt_tokens_details") or {}
    cost = usage.get("cost")
    cache_read = details.get("cached_tokens", 0) or 0
    cache_write = details.get("cache_write_tokens", 0) or 0
    prompt = usage.get("prompt_tokens", 0) or 0
    return {
        "input": max(prompt - cache_read - cache_write, 0),
        "output": usage.get("completion_tokens", 0) or 0,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "cost": float(cost) if cost is not None else None,
    }


def parse_messages_usage(usage: dict[str, Any] | None) -> dict[str, Any]:
    """Lit le ``usage`` de l'endpoint Messages (compatible Anthropic)."""
    usage = usage or {}
    cost = usage.get("cost")
    return {
        "input": usage.get("input_tokens", 0) or 0,
        "output": usage.get("output_tokens", 0) or 0,
        "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
        "cache_write": usage.get("cache_creation_input_tokens", 0) or 0,
        "cost": float(cost) if cost is not None else None,
    }


def total_cost(parsed_usages: list[dict[str, Any]]) -> tuple[float, int]:
    """Somme des ``cost`` connus et nombre d'appels dont le coût est absent."""
    known = [u["cost"] for u in parsed_usages if u["cost"] is not None]
    return round(sum(known), 8), len(parsed_usages) - len(known)


def mentions_word(text: str, *words: str) -> bool:
    """Vrai si l'un des mots figure en mot entier (``red`` ne compte pas dans ``hundred``)."""
    return any(re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE) for w in words)


def redact(text: str, secret: str | None) -> str:
    """Retire toute occurrence du secret d'un texte destiné à la sortie."""
    return text.replace(secret, "[CLE]") if secret else text


def make_png(width: int = 16, height: int = 16, rgb: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    """PNG RGB uni, en bibliothèque standard."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


# --- réseau ----------------------------------------------------------------------------------


def _request(path: str, body: dict[str, Any] | None, key: str | None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if path == "/messages":
        # Cet en-tête fait basculer /models au format Anthropic : seulement pour /messages.
        headers["anthropic-version"] = "2023-06-01"
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        text = redact(err.read().decode("utf-8", "replace"), key)
        return {"_error": {"status": err.code, "body": text[:500]}}


_SYSTEM = "Tu es un assistant concis. " + "Contexte de remplissage pour le cache. " * 400
_ADD_TOOL = {
    "name": "add",
    "description": "Additionne deux entiers.",
    "input_schema": {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    },
}
_QUESTION = "Utilise l'outil add pour calculer 17 + 25, puis donne le résultat."


Request = Callable[[str, dict[str, Any] | None, str | None], dict[str, Any]]


def _chat_call(
    messages: list[dict[str, Any]], key: str, tools: bool, request: Request
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": MODEL_ID, "max_tokens": 1500, "messages": messages}
    body["usage"] = {"include": True}
    if tools:
        body["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": _ADD_TOOL["name"],
                    "description": _ADD_TOOL["description"],
                    "parameters": _ADD_TOOL["input_schema"],
                },
            }
        ]
    return request("/chat/completions", body, key)


def _summarize_call(resp: dict[str, Any], parser: Any) -> dict[str, Any]:
    if "_error" in resp:
        return {"error": resp["_error"], "usage": parser(None)}
    # ``provider`` : fournisseur sous-jacent choisi par le routage OpenRouter (chat completions).
    return {"provider": resp.get("provider"), "usage": parser(resp.get("usage"))}


def _chat_text(resp: dict[str, Any]) -> str:
    return (resp.get("choices") or [{}])[0].get("message", {}).get("content") or ""


def run_paid_probe(key: str, request: Request | None = None) -> dict[str, Any]:
    """Appels payants (6 au plus) : texte, outil (aller-retour), vision, outil via Messages.

    Pire cas borné : 6 × (1500 jetons de sortie + ~4,2 k d'entrée), soit 0,02 USD au tarif
    Xiaomi et 0,18 USD chez le fournisseur le plus cher ; ``budget_ok`` vient après coup.
    """
    request = request or _request
    out: dict[str, Any] = {}
    usages: list[dict[str, Any]] = []
    sys_msg = {"role": "system", "content": _SYSTEM}

    r = _chat_call([sys_msg, {"role": "user", "content": "Réponds : OK."}], key, False, request)
    out["chat_text"] = _summarize_call(r, parse_chat_usage)
    usages.append(out["chat_text"]["usage"])

    msgs: list[dict[str, Any]] = [sys_msg, {"role": "user", "content": _QUESTION}]
    r1 = _chat_call(msgs, key, True, request)
    step1 = _summarize_call(r1, parse_chat_usage)
    usages.append(step1["usage"])
    calls = (r1.get("choices") or [{}])[0].get("message", {}).get("tool_calls") or []
    step1["tool_called"] = bool(calls)
    out["chat_tool_step1"] = step1
    if calls:
        msg = r1["choices"][0]["message"]
        args = json.loads(calls[0]["function"]["arguments"])
        msgs.append(
            {
                "role": "assistant",
                "content": msg.get("content") or "",
                "tool_calls": msg["tool_calls"],
            }
        )
        msgs.append(
            {
                "role": "tool",
                "tool_call_id": calls[0]["id"],
                "content": str(args.get("a", 0) + args.get("b", 0)),
            }
        )
        r2 = _chat_call(msgs, key, True, request)
        step2 = _summarize_call(r2, parse_chat_usage)
        step2["answer_has_42"] = mentions_word(_chat_text(r2), "42")
        out["chat_tool_step2"] = step2
        usages.append(step2["usage"])

    png = base64.b64encode(make_png()).decode()
    img = {
        "role": "user",
        "content": [
            {"type": "text", "text": "Quelle est la couleur de cette image ? Un mot."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png}"}},
        ],
    }
    r = _chat_call([img], key, False, request)
    vis = _summarize_call(r, parse_chat_usage)
    vis["answer_mentions_red"] = mentions_word(_chat_text(r), "rouge", "red")
    out["chat_vision"] = vis
    usages.append(vis["usage"])

    # Endpoint Messages (compatible Anthropic), même boucle d'outil, avec cache_control.
    system = [{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}]
    amsgs: list[dict[str, Any]] = [{"role": "user", "content": _QUESTION}]
    base = {"model": MODEL_ID, "max_tokens": 1500, "system": system, "tools": [_ADD_TOOL]}
    a1 = request("/messages", {**base, "messages": amsgs}, key)
    astep1 = _summarize_call(a1, parse_messages_usage)
    usages.append(astep1["usage"])
    blocks = a1.get("content") or []
    tool_use = next((b for b in blocks if b.get("type") == "tool_use"), None)
    astep1["tool_called"] = tool_use is not None
    out["messages_tool_step1"] = astep1
    if tool_use:
        inp = tool_use["input"]
        amsgs.append({"role": "assistant", "content": blocks})
        amsgs.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use["id"],
                        "content": str(inp.get("a", 0) + inp.get("b", 0)),
                    }
                ],
            }
        )
        a2 = request("/messages", {**base, "messages": amsgs}, key)
        astep2 = _summarize_call(a2, parse_messages_usage)
        txt = "".join(b.get("text", "") for b in a2.get("content") or [])
        astep2["answer_has_42"] = mentions_word(txt, "42")
        out["messages_tool_step2"] = astep2
        usages.append(astep2["usage"])

    cost, missing = total_cost(usages)
    out["paid_calls"] = len(usages)
    out["total_billed_usd"] = cost
    out["calls_without_cost"] = missing
    out["budget_ok"] = cost <= MAX_PROBE_USD
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    key = os.environ.get(KEY_VAR)
    summary: dict[str, Any] = {"model_id": MODEL_ID}
    models = _request("/models", None, None)
    model = find_model(models, MODEL_ID)
    summary["model"] = summarize_model(model) if model else None
    status = 0
    if model is None:
        # Sans l'entrée du modèle, aucun appel payant : l'identifiant ou le réseau est en cause.
        summary["error"] = models.get("_error") or f"{MODEL_ID} absent de /models"
        status = 1
    elif "--models-only" not in args:
        if not key:
            summary["error"] = f"{KEY_VAR} absente"
            status = 1
        else:
            summary["probe"] = run_paid_probe(key)
    # ASCII : la console Windows (cp1252) ne lève pas d'erreur sur un corps d'erreur exotique.
    print(redact(json.dumps(summary, indent=2), key))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
