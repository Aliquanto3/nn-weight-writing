"""Port fournisseur normalisé (AD-10) : un seul format de requête et de réponse pour tous les
adaptateurs. Le service d'outils ne branche jamais selon le fournisseur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True)
class TextPart:
    text: str
    type: Literal["text"] = "text"


@dataclass(frozen=True)
class ImagePart:
    """Image en base64 (lot 2)."""

    media_type: str
    data_b64: str
    type: Literal["image"] = "image"


@dataclass(frozen=True)
class ToolCall:
    """Appel d'outil du modèle ; `arguments` est le texte JSON tel que le modèle l'a émis."""

    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant", "tool"]
    content: tuple[TextPart | ImagePart, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None

    @property
    def text(self) -> str:
        return "".join(part.text for part in self.content if isinstance(part, TextPart))


@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    input_schema: dict


@dataclass(frozen=True)
class ChatRequest:
    model: str
    system: str
    messages: tuple[Message, ...]
    tools: tuple[ToolSchema, ...]
    max_tokens: int
    sampling: dict = field(default_factory=dict)
    effort: str | None = None


@dataclass(frozen=True)
class Usage:
    """Jetons d'entrée hors cache, de sortie, lus et écrits en cache ; coût annoncé ou `None`."""

    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    provider_cost: float | None = None
    # Part de `cache_write` écrite en tranche d'une heure (Claude Code), tarifée à part.
    cache_write_1h: int = 0


@dataclass(frozen=True)
class ChatResponse:
    message: Message
    usage: Usage
    stop_reason: str | None = None
    # Fournisseur sous-jacent annoncé (champ `provider` d'OpenRouter), pour contrôle.
    served_by: str | None = None


class ProviderError(RuntimeError):
    """Échec d'un appel après les nouvelles tentatives de l'adaptateur."""


class ModelProvider(Protocol):
    name: str

    def complete(self, request: ChatRequest) -> ChatResponse: ...


def message_to_json(message: Message) -> dict:
    """Forme journalisée d'un message (contenu de l'échange, AD-7)."""
    out: dict = {"role": message.role}
    parts = []
    for part in message.content:
        if isinstance(part, TextPart):
            parts.append({"type": "text", "text": part.text})
        else:
            parts.append({"type": "image", "media_type": part.media_type})
    out["content"] = parts
    if message.tool_calls:
        out["tool_calls"] = [
            {"id": c.id, "name": c.name, "arguments": c.arguments} for c in message.tool_calls
        ]
    if message.tool_call_id is not None:
        out["tool_call_id"] = message.tool_call_id
    return out
