"""Adaptateur `fake` (AD-10) : réponses scriptées pour les tests, sans réseau."""

from __future__ import annotations

import json
from collections.abc import Iterable

from nn_weight_writing.providers.types import (
    ChatRequest,
    ChatResponse,
    Message,
    TextPart,
    ToolCall,
    Usage,
)


def reply(
    text: str = "",
    calls: Iterable[tuple[str, object]] = (),
    usage: Usage | None = None,
) -> ChatResponse:
    """Réponse scriptée ; un argument déjà textuel est transmis tel quel (JSON invalide permis)."""
    tool_calls = tuple(
        ToolCall(
            id=f"call_{i}",
            name=name,
            arguments=args if isinstance(args, str) else json.dumps(args, ensure_ascii=False),
        )
        for i, (name, args) in enumerate(calls)
    )
    content = (TextPart(text),) if text else ()
    return ChatResponse(
        message=Message("assistant", content, tool_calls),
        usage=usage or Usage(input=100, output=20),
        stop_reason="tool_use" if tool_calls else "end_turn",
    )


class FakeProvider:
    """Rend les réponses dans l'ordre ; une exception du script est levée à son tour."""

    name = "fake"

    def __init__(self, script: Iterable[ChatResponse | Exception]) -> None:
        self._script = iter(script)
        self.requests: list[ChatRequest] = []

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        item = next(self._script, None)
        if item is None:
            return reply("fin du script")
        if isinstance(item, Exception):
            raise item
        return item
