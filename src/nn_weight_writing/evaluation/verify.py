"""Évaluation hors séance (AD-9) : enregistrement de gel, empreintes, `eval.json`.

Lit le journal sans y écrire. La commande refuse tout dossier sans gel ou à l'empreinte
divergente, puis écrit un `eval.json` déterministe (au champ `ts` près). Avec une racine de
jeux réservés explicite (`heldout_root`, décision Q9 de 1-14), il porte les mesures
(`evaluation/measures.py`) ; sans elle, vérification seule et `metrics` vide.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from enum import StrEnum
from pathlib import Path

from nn_weight_writing import network
from nn_weight_writing.evaluation.schema import (
    EVAL_CROSS_PREFIX,
    EVAL_FILE,
    FROZEN_DIR,
    JOURNAL_FILE,
    RUN_FILE,
    EvalRecord,
    RunRecord,
)
from nn_weight_writing.journal.reader import JournalError, find_last
from nn_weight_writing.journal.writer import utc_now
from nn_weight_writing.network import io as netio

# JOURNAL_FILE, RUN_FILE, FROZEN_DIR, EVAL_FILE : définis dans schema, importés d ici aussi.


class EvalRefusalCode(StrEnum):
    NO_FREEZE_RECORD = "no_freeze_record"
    MISSING_FILE = "missing_file"
    UNEXPECTED_FILE = "unexpected_file"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    UNLOADABLE = "unloadable"
    # Mesures sur le jeu réservé (story 1-14).
    NO_HELDOUT = "no_heldout"
    AMBIGUOUS_DATASET = "ambiguous_dataset"
    HELDOUT_FINGERPRINT = "heldout_fingerprint"
    CROSS_SAME_TASK = "cross_same_task"
    ENCODER_MISMATCH = "encoder_mismatch"
    TASK_MISMATCH = "task_mismatch"


class EvaluationRefused(Exception):
    def __init__(self, code: EvalRefusalCode, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _freeze_record(run_dir: Path) -> tuple[str, dict, str, bool | None]:
    journal = run_dir / JOURNAL_FILE
    if journal.is_file():
        try:
            record = find_last(journal, "freeze")
        except (JournalError, json.JSONDecodeError) as exc:
            raise EvaluationRefused(EvalRefusalCode.NO_FREEZE_RECORD, str(exc)) from exc
        if record is None:
            raise EvaluationRefused(EvalRefusalCode.NO_FREEZE_RECORD, "journal sans gel")
        return "session", record["files"], record["tree_sha256"], record["valid"]
    run_json = run_dir / RUN_FILE
    if run_json.is_file():
        data = json.loads(run_json.read_text("utf-8"))
        run = RunRecord(**data)
        return "baseline", run.files, run.tree_sha256, None
    raise EvaluationRefused(EvalRefusalCode.NO_FREEZE_RECORD, f"ni {JOURNAL_FILE} ni {RUN_FILE}")


def verify_frozen(run_dir: Path) -> tuple[str, dict, str, bool | None]:
    """Recalcule les sha256 de `frozen/` et `tree_sha256` ; refuse toute divergence."""
    run_dir = Path(run_dir)
    kind, files, tree, valid = _freeze_record(run_dir)
    frozen = run_dir / FROZEN_DIR
    present = {p.name for p in frozen.iterdir()} if frozen.is_dir() else set()
    missing = sorted(set(files) - present)
    if missing:
        raise EvaluationRefused(EvalRefusalCode.MISSING_FILE, f"absents : {missing}")
    extra = sorted(present - set(files))
    if extra:
        raise EvaluationRefused(EvalRefusalCode.UNEXPECTED_FILE, f"en trop : {extra}")
    for name, digest in files.items():
        actual = netio.sha256_file(frozen / name)
        if actual != digest:
            raise EvaluationRefused(EvalRefusalCode.FINGERPRINT_MISMATCH, f"{name} modifié")
    if netio.tree_sha256(files) != tree:
        raise EvaluationRefused(EvalRefusalCode.FINGERPRINT_MISMATCH, "tree_sha256 divergent")
    if netio.MANIFEST_NAME in files:
        try:
            network.load(frozen)
        except (netio.NetworkError, ValueError, OSError) as exc:
            raise EvaluationRefused(EvalRefusalCode.UNLOADABLE, str(exc)) from exc
    return kind, files, tree, valid


def cross_file(task: str, dataset: str) -> str:
    """`eval-cross-<tâche>-<jeu>.json` (noms validés : le tiret sépare sans ambiguïté)."""
    return f"{EVAL_CROSS_PREFIX}{task}-{dataset}.json"


def evaluate(
    run_dir: Path,
    heldout_root: Path | None = None,
    *,
    dataset: str | None = None,
    on: tuple[str, str] | None = None,
) -> Path:
    """Vérifie le gel puis écrit `eval.json` (ou `eval-cross-*.json` avec `on`) à côté.

    `heldout_root` absent : vérification seule, `metrics` et `target` vides ; un `eval.json`
    déjà mesuré pour ce même gel est alors gardé tel quel (une vérification relancée après les
    mesures ne les efface pas). `on` exige `heldout_root`.
    """
    from nn_weight_writing.evaluation import measures

    run_dir = Path(run_dir)
    kind, files, tree, valid = verify_frozen(run_dir)
    target: dict = {}
    metrics: dict = {}
    name = EVAL_FILE
    if on is not None:
        if heldout_root is None:
            raise ValueError("évaluation croisée : --heldout-root requis")
        task, cross_dataset = on
        heldout_dir = measures.resolve_heldout(heldout_root, task, cross_dataset)
        target, metrics = measures.measure_cross(run_dir, task, heldout_dir)
        name = cross_file(task, heldout_dir.name)
    elif heldout_root is not None:
        from nn_weight_writing.evaluation.score import run_task

        heldout_dir = measures.resolve_heldout(heldout_root, run_task(run_dir), dataset)
        target, metrics = measures.measure(run_dir, heldout_dir)
    elif _measured(run_dir / EVAL_FILE, tree):
        return run_dir / EVAL_FILE
    record = EvalRecord(
        run=run_dir.name,
        kind=kind,
        files=files,
        tree_sha256=tree,
        valid=valid,
        ts=utc_now(),
        metrics=_rounded(metrics),
        target=target,
    )
    out = run_dir / name
    data = json.dumps(asdict(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    netio.atomic_write_bytes(out, data.encode("utf-8"))
    return out


def _measured(path: Path, tree: str) -> bool:
    """`eval.json` v2 déjà mesuré (`metrics` et `target` non vides) pour ce `tree_sha256`."""
    try:
        data = json.loads(path.read_text("utf-8"))
    except OSError, ValueError:
        return False
    return (
        isinstance(data, dict)
        and data.get("tree_sha256") == tree
        and bool(data.get("metrics"))
        and bool(data.get("target"))
    )


def _rounded(value):
    """Flottants arrondis à 6 décimales (déterminisme d'AD-9) ; le reste tel quel."""
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {k: _rounded(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_rounded(v) for v in value]
    return value


def lot_dirs(lot_dir: Path) -> tuple[list[Path], list[Path], list[Path]]:
    """Dossiers d'un lot (AD-12) : séances gelées, séances non gelées, témoins (`**/train/*`)."""
    lot_dir = Path(lot_dir)
    frozen: list[Path] = []
    unfrozen: list[Path] = []
    for path in sorted(p for p in lot_dir.iterdir() if (p / JOURNAL_FILE).is_file()):
        try:
            record = find_last(path / JOURNAL_FILE, "freeze")
        except JournalError, json.JSONDecodeError:
            record = {}  # journal illisible : evaluate le refusera (no_freeze_record)
        (frozen if record is not None else unfrozen).append(path)
    baselines = sorted(p.parent for p in lot_dir.glob(f"**/train/*/{RUN_FILE}"))
    return frozen, unfrozen, baselines
