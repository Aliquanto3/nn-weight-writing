"""Évaluation hors séance (AD-9) : enregistrement de gel, empreintes, `eval.json`.

Lit le journal sans y écrire. Les mesures sur le jeu réservé arrivent en 1-14 ; ici, la
commande refuse tout dossier sans gel ou à l'empreinte divergente, puis écrit un
`eval.json` déterministe (au champ `ts` près).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from enum import StrEnum
from pathlib import Path

from nn_weight_writing import network
from nn_weight_writing.evaluation.schema import EvalRecord, RunRecord
from nn_weight_writing.journal.reader import JournalError, find_last
from nn_weight_writing.journal.writer import utc_now
from nn_weight_writing.network import io as netio

JOURNAL_FILE = "journal.jsonl"
RUN_FILE = "run.json"
FROZEN_DIR = "frozen"
EVAL_FILE = "eval.json"


class EvalRefusalCode(StrEnum):
    NO_FREEZE_RECORD = "no_freeze_record"
    MISSING_FILE = "missing_file"
    UNEXPECTED_FILE = "unexpected_file"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    UNLOADABLE = "unloadable"


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


def evaluate(run_dir: Path) -> Path:
    """Vérifie le gel puis écrit `eval.json` à côté du dossier gelé."""
    run_dir = Path(run_dir)
    kind, files, tree, valid = verify_frozen(run_dir)
    record = EvalRecord(
        run=run_dir.name, kind=kind, files=files, tree_sha256=tree, valid=valid, ts=utc_now()
    )
    out = run_dir / EVAL_FILE
    data = json.dumps(asdict(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    netio.atomic_write_bytes(out, data.encode("utf-8"))
    return out
