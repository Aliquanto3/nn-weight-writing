"""Événements du journal de séance (AD-7), importés par l'écrivain et par tous les lecteurs.

Chaque ligne de `journal.jsonl` porte `schema_version`, `seq` (croissant à partir de 0), `ts`
(UTC ISO 8601 avec `Z`) et `type`, puis les champs du dataclass correspondant.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import ClassVar

ENVELOPE = ("schema_version", "seq", "ts", "type")


@dataclass(frozen=True)
class Event:
    TYPE: ClassVar[str] = ""


@dataclass(frozen=True)
class OpenEvent(Event):
    TYPE: ClassVar[str] = "open"
    session_id: str
    task: str
    dataset: str
    dataset_sha256: str
    method: str
    model: str
    driver: str
    provider: str
    attempt: int
    seed: int
    pass_budget: int
    protocol_sha256: str
    system_prompt_sha256: str
    sampling: dict
    effort: str | None


@dataclass(frozen=True)
class ModelCallEvent(Event):
    TYPE: ClassVar[str] = "model_call"
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_equiv_usd: float
    billed_usd: float
    provider_cost: float | None
    duration_s: float
    exchange: dict
    # Part de `cache_write_tokens` en tranche d'une heure (pilote Claude Code) ; optionnel.
    cache_write_1h_tokens: int = 0


@dataclass(frozen=True)
class ToolCallEvent(Event):
    TYPE: ClassVar[str] = "tool_call"
    tool: str
    arguments: dict
    result: dict


@dataclass(frozen=True)
class PassEvent(Event):
    TYPE: ClassVar[str] = "pass"
    number: int
    remaining: int
    valid: bool
    outputs: list
    error: str | None = None


@dataclass(frozen=True)
class ScriptRunEvent(Event):
    TYPE: ClassVar[str] = "script_run"
    tool: str
    code_sha256: str
    ok: bool
    log: str
    flags: list
    duration_s: float
    error: str | None = None


@dataclass(frozen=True)
class RefusalEvent(Event):
    TYPE: ClassVar[str] = "refusal"
    code: str
    detail: str


@dataclass(frozen=True)
class FreezeEvent(Event):
    TYPE: ClassVar[str] = "freeze"
    files: dict
    tree_sha256: str
    valid: bool
    blocks: list | None
    size_nominal: int
    size_script_bytes: int
    size_weights_zlib: int


@dataclass(frozen=True)
class EndEvent(Event):
    TYPE: ClassVar[str] = "end"
    reason: str
    passes_used: int
    totals: dict = field(default_factory=dict)
    # Cause d'une fin `error` (limite d'usage, erreur du fournisseur…) ou précision du motif.
    detail: str | None = None


EVENT_TYPES: dict[str, type[Event]] = {
    cls.TYPE: cls
    for cls in (
        OpenEvent,
        ModelCallEvent,
        ToolCallEvent,
        PassEvent,
        ScriptRunEvent,
        RefusalEvent,
        FreezeEvent,
        EndEvent,
    )
}


# Champs ajoutés après coup, avec valeur par défaut : absents des journaux plus anciens, admis.
OPTIONAL_FIELDS = frozenset({"cache_write_1h_tokens"})


def event_fields(cls: type[Event]) -> tuple[str, ...]:
    return tuple(f.name for f in fields(cls))
