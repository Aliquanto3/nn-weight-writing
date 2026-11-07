"""Schémas de `eval.json` et `run.json`, importés par producteurs et lecteurs."""

from __future__ import annotations

from dataclasses import dataclass, field

EVAL_SCHEMA_VERSION = 2  # 2 : champ `target` et mesures (story 1-14)
RUN_SCHEMA_VERSION = 1

# Noms de fichiers d'un dossier gelé (AD-12), partagés par `evaluation`, `report` et `publish`.
JOURNAL_FILE = "journal.jsonl"
RUN_FILE = "run.json"
FROZEN_DIR = "frozen"
EVAL_FILE = "eval.json"
EVAL_CROSS_PREFIX = "eval-cross-"  # eval-cross-<tâche>-<jeu>.json


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
    task: str = ""  # tâche du réseau gelé (contrôle de l'évaluation, 1-9 O4)


@dataclass(frozen=True)
class EvalRecord:
    """`eval.json` : empreintes vérifiées, jeu évalué (`target`) et mesures agrégées.

    `metrics` vide et `target` vide : vérification seule (aucun jeu réservé donné). Sinon
    `metrics` porte `accuracy`, `by_label`, `by_type`, `held_out_types`, `ood`, `ablation`,
    `error` (story 1-14) ; `target` : `task`, `dataset`, `examples_sha256`, `labels_sha256`,
    `written_task`, `cross`.
    """

    run: str
    kind: str
    files: dict
    tree_sha256: str
    valid: bool | None
    ts: str
    metrics: dict = field(default_factory=dict)
    schema_version: int = EVAL_SCHEMA_VERSION
    target: dict = field(default_factory=dict)
