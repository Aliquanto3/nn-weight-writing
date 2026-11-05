"""Évaluation hors séance (AD-9) : refus sans gel ou sur empreinte divergente, déterminisme, CLI."""

from __future__ import annotations

import json

import pytest
from conftest import BLOCKS, write_literal_network

from nn_weight_writing.cli import main
from nn_weight_writing.evaluation.verify import EvalRefusalCode, EvaluationRefused, evaluate
from nn_weight_writing.network import io as netio
from nn_weight_writing.session.refusals import EndReason


@pytest.fixture
def frozen_run(make_service):
    service = make_service("A-literal")
    write_literal_network(service)
    assert service.call("freeze", {"blocks": BLOCKS}) == {"frozen": True}
    return service.run_dir


def load_eval(run_dir):
    return json.loads((run_dir / "eval.json").read_text("utf-8"))


def test_evaluation_is_deterministic(frozen_run):
    evaluate(frozen_run)
    first = load_eval(frozen_run)
    evaluate(frozen_run)
    second = load_eval(frozen_run)
    assert first.pop("ts") and second.pop("ts")
    assert first == second
    assert first["kind"] == "session" and first["valid"] is True
    assert first["run"] == frozen_run.name
    assert sorted(first["files"]) == ["manifest.json", "weights.npz"]
    assert first["tree_sha256"] == netio.tree_sha256(first["files"])
    assert first["metrics"] == {}


def test_evaluation_never_writes_the_journal(frozen_run):
    journal = frozen_run / "journal.jsonl"
    before = journal.read_bytes()
    evaluate(frozen_run)
    assert journal.read_bytes() == before


def test_refused_on_modified_file(frozen_run):
    weights = frozen_run / "frozen" / "weights.npz"
    data = bytearray(weights.read_bytes())
    data[-1] ^= 0xFF
    weights.write_bytes(bytes(data))
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(frozen_run)
    assert exc.value.code == EvalRefusalCode.FINGERPRINT_MISMATCH
    assert "weights.npz" in exc.value.detail
    assert not (frozen_run / "eval.json").exists()


def test_refused_on_extra_or_missing_file(frozen_run):
    (frozen_run / "frozen" / "notes.txt").write_text("ajout", "utf-8")
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(frozen_run)
    assert exc.value.code == EvalRefusalCode.UNEXPECTED_FILE
    (frozen_run / "frozen" / "notes.txt").unlink()
    (frozen_run / "frozen" / "manifest.json").unlink()
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(frozen_run)
    assert exc.value.code == EvalRefusalCode.MISSING_FILE


def test_refused_on_tampered_tree_digest(frozen_run):
    journal = frozen_run / "journal.jsonl"
    lines = journal.read_text("utf-8").splitlines()
    for i, line in enumerate(lines):
        record = json.loads(line)
        if record["type"] == "freeze":
            record["tree_sha256"] = "0" * 64
            lines[i] = json.dumps(record)
    journal.write_text("\n".join(lines) + "\n", "utf-8")
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(frozen_run)
    assert exc.value.code == EvalRefusalCode.FINGERPRINT_MISMATCH


def test_refused_without_freeze(make_service, tmp_path):
    service = make_service("B")
    service.end(EndReason.PASS_BUDGET)
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(service.run_dir)
    assert exc.value.code == EvalRefusalCode.NO_FREEZE_RECORD
    empty = tmp_path / "vide"
    empty.mkdir()
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(empty)
    assert exc.value.code == EvalRefusalCode.NO_FREEZE_RECORD


def test_baseline_run_json(tmp_path):
    run_dir = tmp_path / "toy-C-n100-s0"
    (run_dir / "frozen").mkdir(parents=True)
    (run_dir / "frozen" / "a.bin").write_bytes(b"abc")
    files = {"a.bin": netio.sha256_bytes(b"abc")}
    record = {
        "run_id": run_dir.name,
        "baseline": "C",
        "n": 100,
        "seed": 0,
        "files": files,
        "tree_sha256": netio.tree_sha256(files),
    }
    (run_dir / "run.json").write_text(json.dumps(record), "utf-8")
    assert load_eval(evaluate(run_dir).parent)["kind"] == "baseline"


def test_cli_evaluate(frozen_run, capsys):
    assert main(["evaluate", str(frozen_run)]) == 0
    assert capsys.readouterr().out.strip().endswith("eval.json")
    (frozen_run / "frozen" / "manifest.json").write_text("{}", "utf-8")
    assert main(["evaluate", str(frozen_run)]) == 1
    assert "fingerprint_mismatch" in capsys.readouterr().err
