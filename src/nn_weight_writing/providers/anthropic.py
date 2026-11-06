"""Adaptateur `anthropic` (AD-10) : SDK `anthropic`, cache de prompt ; repli du pilote Claude Code.

Points de cache : le prompt système, le dernier outil et le dernier bloc de la conversation.
Aucune nouvelle tentative par défaut (`max_retries=0`) : un délai dépassé ou une erreur après envoi
peut avoir été facturé sans `model_call` ni coût journalisé ; la séance finit en `error`.
"""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic

from nn_weight_writing.providers.types import (
    ChatRequest,
    ChatResponse,
    ImagePart,
    Message,
    ProviderError,
    TextPart,
    ToolCall,
)
from nn_weight_writing.providers.usage import parse_messages_usage, to_usage

KEY_VAR = "ANTHROPIC_API_KEY"
CACHE = {"type": "ephemeral"}


def _blocks(message: Message) -> list[dict]:
    blocks: list[dict] = []
    for part in message.content:
        if isinstance(part, ImagePart):
            source = {"type": "base64", "media_type": part.media_type, "data": part.data_b64}
            blocks.append({"type": "image", "source": source})
        elif part.text:
            blocks.append({"type": "text", "text": part.text})
    return blocks


def _tool_input(arguments: str) -> object:
    try:
        value = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def to_anthropic_messages(messages: tuple[Message, ...]) -> list[dict]:
    """Les résultats d'outils consécutifs forment un seul message `user` de blocs `tool_result`."""
    out: list[dict] = []
    for message in messages:
        if message.role == "tool":
            block = {
                "type": "tool_result",
                "tool_use_id": message.tool_call_id,
                "content": message.text,
            }
            if out and out[-1]["role"] == "user" and out[-1].get("_tool_results"):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block], "_tool_results": True})
        elif message.role == "assistant":
            blocks = _blocks(message)
            blocks += [
                {"type": "tool_use", "id": c.id, "name": c.name, "input": _tool_input(c.arguments)}
                for c in message.tool_calls
            ]
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": "user", "content": _blocks(message)})
    for entry in out:
        entry.pop("_tool_results", None)
    return out


def build_params(request: ChatRequest) -> dict:
    """Paramètres complets de `messages.create` (purs, testés sans réseau)."""
    tools = [
        {"name": t.name, "description": t.description, "input_schema": t.input_schema}
        for t in request.tools
    ]
    if tools:
        tools[-1]["cache_control"] = CACHE
    messages = to_anthropic_messages(request.messages)
    if messages and messages[-1]["content"]:
        messages[-1]["content"][-1] = {**messages[-1]["content"][-1], "cache_control": CACHE}
    params: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens,
        "system": [{"type": "text", "text": request.system, "cache_control": CACHE}],
        "tools": tools,
        "messages": messages,
        **request.sampling,
    }
    if request.effort:
        params["output_config"] = {"effort": request.effort}
    return params


def parse_response(data: dict) -> ChatResponse:
    text_parts: list[TextPart] = []
    calls: list[ToolCall] = []
    for block in data.get("content") or []:
        if block.get("type") == "text" and block.get("text"):
            text_parts.append(TextPart(block["text"]))
        elif block.get("type") == "tool_use":
            arguments = json.dumps(block.get("input") or {}, ensure_ascii=False)
            calls.append(ToolCall(str(block.get("id")), str(block.get("name")), arguments))
    return ChatResponse(
        message=Message("assistant", tuple(text_parts), tuple(calls)),
        usage=to_usage(parse_messages_usage(data.get("usage"))),
        stop_reason=data.get("stop_reason"),
    )


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        http_client: Any = None,
        max_retries: int = 0,
        timeout_s: float = 600.0,
        base_url: str | None = None,
    ) -> None:
        key = api_key or os.environ.get(KEY_VAR)
        if not key:
            raise ProviderError(f"{KEY_VAR} absente de l'environnement")
        self.timeout_s = timeout_s
        self._client = anthropic.Anthropic(
            api_key=key,
            http_client=http_client,
            max_retries=max_retries,
            timeout=timeout_s,
            base_url=base_url,
        )

    def complete(self, request: ChatRequest) -> ChatResponse:
        try:
            response = self._client.messages.create(**build_params(request))
        except anthropic.AnthropicError as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
        return parse_response(response.model_dump())
