"""Adaptateur `openrouter` (AD-10) : chat completions compatible OpenAI, SDK `openai`, `base_url`.

Le fournisseur sous-jacent est fixé (`provider.order`, `allow_fallbacks: false`) pour garder le
cache et un prix stable (constat 1-2). Les nouvelles tentatives sur erreur transitoire (429, 5xx,
réseau) sont celles du SDK (`max_retries`).
"""

from __future__ import annotations

import json
import os
from typing import Any

import openai

from nn_weight_writing.providers.types import (
    ChatRequest,
    ChatResponse,
    ImagePart,
    Message,
    ProviderError,
    TextPart,
    ToolCall,
)
from nn_weight_writing.providers.usage import parse_chat_usage, to_usage

BASE_URL = "https://openrouter.ai/api/v1"
KEY_VAR = "OPENROUTER_API_KEY"


def _content(message: Message) -> str | list[dict]:
    if all(isinstance(part, TextPart) for part in message.content):
        return message.text
    parts: list[dict] = []
    for part in message.content:
        if isinstance(part, ImagePart):
            url = f"data:{part.media_type};base64,{part.data_b64}"
            parts.append({"type": "image_url", "image_url": {"url": url}})
        else:
            parts.append({"type": "text", "text": part.text})
    return parts


def to_openai_messages(request: ChatRequest) -> list[dict]:
    out: list[dict] = [{"role": "system", "content": request.system}]
    for message in request.messages:
        if message.role == "tool":
            out.append(
                {"role": "tool", "tool_call_id": message.tool_call_id, "content": message.text}
            )
        elif message.role == "assistant":
            entry: dict[str, Any] = {"role": "assistant", "content": message.text or None}
            if message.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.name, "arguments": call.arguments},
                    }
                    for call in message.tool_calls
                ]
            out.append(entry)
        else:
            out.append({"role": "user", "content": _content(message)})
    return out


def build_body(request: ChatRequest, provider_order: tuple[str, ...]) -> dict:
    """Corps complet de la requête chat completions (pur, testé sans réseau)."""
    body: dict[str, Any] = {
        "model": request.model,
        "messages": to_openai_messages(request),
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in request.tools
        ],
        "max_tokens": request.max_tokens,
        "usage": {"include": True},
        **request.sampling,
    }
    if provider_order:
        body["provider"] = {"order": list(provider_order), "allow_fallbacks": False}
    if request.seed is not None:
        body["seed"] = request.seed
    if request.effort:
        body["reasoning"] = {"effort": request.effort}
    return body


def parse_response(data: dict) -> ChatResponse:
    """Réponse chat completions (dictionnaire) -> `ChatResponse` normalisée."""
    choices = data.get("choices") or []
    if not choices:
        raise ProviderError(f"réponse sans choix : {json.dumps(data.get('error'))[:500]}")
    choice = choices[0]
    message = choice.get("message") or {}
    calls = tuple(
        ToolCall(
            id=str(call.get("id") or f"call_{i}"),
            name=str((call.get("function") or {}).get("name") or ""),
            arguments=(call.get("function") or {}).get("arguments") or "",
        )
        for i, call in enumerate(message.get("tool_calls") or [])
    )
    text = message.get("content") or ""
    return ChatResponse(
        message=Message("assistant", (TextPart(text),) if text else (), calls),
        usage=to_usage(parse_chat_usage(data.get("usage"))),
        stop_reason=choice.get("finish_reason"),
        served_by=data.get("provider"),
    )


class OpenRouterProvider:
    name = "openrouter"

    def __init__(
        self,
        *,
        provider_order: tuple[str, ...] = (),
        api_key: str | None = None,
        base_url: str = BASE_URL,
        http_client: Any = None,
        max_retries: int = 3,
        timeout_s: float = 600.0,
    ) -> None:
        key = api_key or os.environ.get(KEY_VAR)
        if not key:
            raise ProviderError(f"{KEY_VAR} absente de l'environnement")
        self.provider_order = tuple(provider_order)
        self._client = openai.OpenAI(
            api_key=key,
            base_url=base_url,
            http_client=http_client,
            max_retries=max_retries,
            timeout=timeout_s,
        )

    def complete(self, request: ChatRequest) -> ChatResponse:
        body = build_body(request, self.provider_order)
        core = {key: body.pop(key) for key in ("model", "messages", "tools")}
        try:
            response = self._client.chat.completions.create(**core, extra_body=body)
        except openai.OpenAIError as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
        return parse_response(response.model_dump())
