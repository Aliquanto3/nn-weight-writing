"""Schémas de `eval.json` et `run.json`, importés par producteurs et lecteurs."""

from __future__ import annotations

from dataclasses import dataclass, field

EVAL_SCHEMA_VERSION = 1
RUN_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RunRecord:
    """`run.json` d'un témoin (AD-17) : enregistrement de gel d'un entraînement."""

    run_id: str
    baseline: str
    n: int
    seed: int
    files: dict
    tree_sha256: str
    schema_version: int = RUN_SCHEMA_VERSION
    dataset: dict = field(default_factory=dict)  # jeu d'entraînement : chemin relatif et sha256


@dataclass(frozen=True)
class EvalRecord:
    """`eval.json` : empreintes vérifiées et mesures agrégées (mesures : story 1-14)."""

    run: str
    kind: str
    files: dict
    tree_sha256: str
    valid: bool | None
    ts: str
    metrics: dict = field(default_factory=dict)
    schema_version: int = EVAL_SCHEMA_VERSION
