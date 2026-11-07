"""Découverte et lecture des artefacts d'un lot : `runs/<N>/` selon AD-12.

Seuls fichiers ouverts : `<séance>/journal.jsonl`, `<séance>/eval*.json`,
`**/train/<run_id>/run.json`, `.../eval*.json` et `.../frozen/manifest.json`. Tout le reste
(`bundle/`, `courbe-c-f.jsonl`, `reentrainement.jsonl`…) est ignoré. Chaque fichier lu entre
dans l'empreinte des entrées.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from nn_weight_writing.evaluation.schema import (
    EVAL_CROSS_PREFIX,
    EVAL_FILE,
    EVAL_SCHEMA_VERSION,
    FROZEN_DIR,
    JOURNAL_FILE,
    RUN_FILE,
)
from nn_weight_writing.journal.reader import JournalError, read_records

CONFIG_FIELDS = (
    "driver",
    "provider",
    "effort",
    "max_tokens",
    "pass_budget",
    "protocol_sha256",
    "system_prompt_sha256",
    "sampling",
)
COST_FIELDS = (
    "billed_usd",
    "cost_equiv_usd",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def config_id(open_record: dict) -> tuple[str, dict]:
    """8 premiers caractères du sha256 du JSON canonique des champs de configuration."""
    fields = {name: open_record.get(name) for name in CONFIG_FIELDS}
    return hashlib.sha256(canonical(fields)).hexdigest()[:8], fields


@dataclass
class Inputs:
    """Fichiers lus : chemin relatif (POSIX) -> sha256."""

    files: dict[str, str] = field(default_factory=dict)

    def read_bytes(self, path: Path, label: str) -> bytes:
        data = path.read_bytes()
        self.files[label] = hashlib.sha256(data).hexdigest()
        return data

    def read_json(self, path: Path, label: str) -> object:
        return json.loads(self.read_bytes(path, label).decode("utf-8"))

    def fingerprint(self) -> str:
        lines = "".join(f"{p} {d}\n" for p, d in sorted(self.files.items()))
        return hashlib.sha256(lines.encode("utf-8")).hexdigest()


@dataclass
class Evaluation:
    """`eval.json` ou `eval-cross-*.json` v2 ; `metrics` vide ou version 1 : non évalué."""

    target: dict
    metrics: dict
    tree_sha256: str

    @property
    def evaluated(self) -> bool:
        return bool(self.metrics) and bool(self.target)


@dataclass
class Session:
    id: str
    path: str  # relatif à runs/<N>/
    open: dict
    config: str
    freeze: dict | None
    end: dict | None
    costs: dict
    turns: int
    refusals: list[str]
    script_runs: int
    flags: dict  # kind -> {"script_runs", "count", "example_ids"}
    native: Evaluation | None
    cross: dict[str, Evaluation]  # "tâche:jeu" -> évaluation

    @property
    def frozen(self) -> bool:
        return bool(self.freeze) and self.freeze.get("valid") is True


@dataclass
class Baseline:
    id: str
    path: str
    chemin: str  # sous-dossier de runs/<N>/ avant train/ ("" ou "annexe-fields1")
    run: dict
    encoder: str | None
    native: Evaluation | None
    cross: dict[str, Evaluation]

    @property
    def retrained_from(self) -> str | None:
        origin = (self.run.get("dataset") or {}).get("retrained_from")
        return origin.get("session") if isinstance(origin, dict) else None


@dataclass
class Lot:
    sessions: list[Session]
    baselines: list[Baseline]
    inputs: Inputs
    warnings: list[str]


def _evaluations(
    run_dir: Path, rel: str, inputs: Inputs
) -> tuple[Evaluation | None, dict[str, Evaluation]]:
    native = None
    cross: dict[str, Evaluation] = {}
    for path in sorted(run_dir.glob("eval*.json")):
        if path.name != EVAL_FILE and not path.name.startswith(EVAL_CROSS_PREFIX):
            continue
        data = inputs.read_json(path, f"{rel}/{path.name}")
        if data.get("schema_version", 1) < EVAL_SCHEMA_VERSION:
            evaluation = Evaluation({}, {}, data.get("tree_sha256", ""))
        else:
            evaluation = Evaluation(
                data.get("target") or {}, data.get("metrics") or {}, data.get("tree_sha256", "")
            )
        if path.name == EVAL_FILE:
            native = evaluation
        elif evaluation.evaluated:
            cross[f"{evaluation.target['task']}:{evaluation.target['dataset']}"] = evaluation
    return native, cross


def _session(run_dir: Path, rel: str, inputs: Inputs) -> Session:
    inputs.read_bytes(run_dir / JOURNAL_FILE, f"{rel}/{JOURNAL_FILE}")  # empreinte
    tmp = list(read_records(run_dir / JOURNAL_FILE))
    opened = next(r for r in tmp if r["type"] == "open")
    freeze = end = None
    costs: dict = dict.fromkeys(COST_FIELDS, 0)
    turns = script_runs = 0
    refusals: list[str] = []
    flags: dict[str, dict] = {}
    for record in tmp:
        kind = record["type"]
        if kind == "freeze":
            freeze = record
        elif kind == "end":
            end = record
        elif kind == "refusal":
            refusals.append(record["code"])
        elif kind == "model_call":
            turns += 1
            for name in COST_FIELDS:
                costs[name] += record.get(name) or 0
        elif kind == "script_run":
            script_runs += 1
            for flag in record.get("flags") or []:
                entry = flags.setdefault(
                    flag.get("kind", "?"), {"script_runs": 0, "count": 0, "example_ids": []}
                )
                entry["script_runs"] += 1
                entry["count"] = max(entry["count"], int(flag.get("count") or 0))
                ids = set(entry["example_ids"]) | set(flag.get("example_ids") or [])
                entry["example_ids"] = sorted(ids)
    costs["billed_usd"] = round(float(costs["billed_usd"]), 6)
    costs["cost_equiv_usd"] = round(float(costs["cost_equiv_usd"]), 6)
    costs["duration_s"] = round(float(((end or {}).get("totals") or {}).get("duration_s") or 0), 3)
    native, cross = _evaluations(run_dir, rel, inputs)
    cid, _ = config_id(opened)
    return Session(
        id=opened["session_id"],
        path=rel,
        open=opened,
        config=cid,
        freeze=freeze,
        end=end,
        costs=costs,
        turns=turns,
        refusals=refusals,
        script_runs=script_runs,
        flags=dict(sorted(flags.items())),
        native=native,
        cross=cross,
    )


def _baseline(run_dir: Path, lot_dir: Path, inputs: Inputs) -> Baseline:
    rel = run_dir.relative_to(lot_dir).as_posix()
    run = inputs.read_json(run_dir / RUN_FILE, f"{rel}/{RUN_FILE}")
    manifest_path = run_dir / FROZEN_DIR / "manifest.json"
    encoder = None
    if manifest_path.is_file():
        encoder = inputs.read_json(manifest_path, f"{rel}/{FROZEN_DIR}/manifest.json")["encoder"]
    parts = Path(rel).parts
    chemin = "/".join(parts[: parts.index("train")]) if "train" in parts else ""
    native, cross = _evaluations(run_dir, rel, inputs)
    return Baseline(run["run_id"], rel, chemin, run, encoder, native, cross)


def collect(lot_dir: Path) -> Lot:
    lot_dir = Path(lot_dir)
    inputs = Inputs()
    warnings: list[str] = []
    sessions: list[Session] = []
    for run_dir in sorted(p for p in lot_dir.iterdir() if (p / JOURNAL_FILE).is_file()):
        try:
            sessions.append(_session(run_dir, run_dir.name, inputs))
        except (JournalError, json.JSONDecodeError, StopIteration) as exc:
            warnings.append(f"journal illisible : {run_dir.name} ({exc})")
    baselines = [
        _baseline(p.parent, lot_dir, inputs) for p in sorted(lot_dir.glob(f"**/train/*/{RUN_FILE}"))
    ]
    return Lot(sessions, baselines, inputs, warnings)
