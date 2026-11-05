"""`nnww session` et `nnww ledger reconcile` (CLI), avec le faux `claude`."""

from __future__ import annotations

import json
import sys

from conftest import EXAMPLES, FAKE_CLAUDE, TASK, scenario, write_examples

from nn_weight_writing import cli
from nn_weight_writing.budget import ledger
from nn_weight_writing.tasks import registry


def args(tmp_path, *extra: str) -> list[str]:
    return [
        "session",
        "--task",
        "toy",
        "--dataset",
        "toy-dev",
        "--method",
        "B",
        "--attempt",
        "1",
        "--seed",
        "7",
        "--lot",
        "1",
        "--data-dir",
        str(tmp_path / "data"),
        "--runs-dir",
        str(tmp_path / "runs"),
        "--ledger",
        str(tmp_path / "ledger.csv"),
        "--claude-command",
        json.dumps([sys.executable, str(FAKE_CLAUDE)]),
        *extra,
    ]


def setup(tmp_path, monkeypatch, cwd_root):
    monkeypatch.setitem(registry.TASKS, "toy", TASK)
    examples = tmp_path / "data" / "toy" / "toy-dev" / "examples.jsonl"
    examples.parent.mkdir(parents=True)
    write_examples(examples, EXAMPLES)
    config_dir = tmp_path / "claude-config"
    config_dir.mkdir()
    monkeypatch.setenv("NNWW_CLAUDE_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("NNWW_CLAUDE_CWD_ROOT", str(cwd_root))


def test_session_command_runs_claude_code_session(tmp_path, monkeypatch, capsys, claude_cwd_root):
    setup(tmp_path, monkeypatch, claude_cwd_root)
    rules = {"code": 'def predict(raw):\n    return "ok"\n'}
    calls = [["submit_rules", rules], ["freeze", {}]]
    turns = [{"id": "m1", "usage": {"input_tokens": 1000}, "calls": calls}]
    scenario(monkeypatch, tmp_path, {"turns": turns})
    assert cli.main(args(tmp_path, "--model", "sonnet-5.5")) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["reason"] == "frozen"
    assert summary["session_id"].startswith("toy-B-sonnet-5.5-t1-")
    # 1000 jetons d'entrée × 2 $/Mtok (Sonnet 5.5), 0 $ facturé.
    assert (summary["billed_usd"], summary["cost_equiv_usd"]) == (0.0, 0.002)
    rows = ledger.read(tmp_path / "ledger.csv")
    assert [r.status for r in rows] == ["reserved", "closed"]


def test_session_command_refused_by_cap(tmp_path, monkeypatch, capsys, claude_cwd_root):
    setup(tmp_path, monkeypatch, claude_cwd_root)
    path = tmp_path / "ledger.csv"
    ledger.append(ledger.LedgerRow("t", "x", 1, ledger.Status.CLOSED, billed_usd=99.0), path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-0000000000")
    assert cli.main(args(tmp_path, "--model", "mimo-v2.6-pro")) == 3
    err = capsys.readouterr().err
    assert err.startswith("séance refusée : plafond lot 1 : 99.000000 facturés")
    assert len(ledger.read(path)) == 1


def test_session_command_unknown_task_or_model(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(registry, "TASKS", {})
    assert cli.main(args(tmp_path, "--model", "sonnet-5.5")) == 2
    assert "tâche inconnue : toy" in capsys.readouterr().err
    assert cli.main(args(tmp_path, "--model", "gpt-9")) == 2
    assert capsys.readouterr().err.startswith("modèle inconnu : gpt-9")


def test_ledger_reconcile_command(tmp_path, capsys):
    path = tmp_path / "ledger.csv"
    ledger.append(ledger.LedgerRow("t", "s1", 1, ledger.Status.RESERVED, reserved_usd=5.0), path)
    argv = ["ledger", "reconcile", "--runs-dir", str(tmp_path / "runs"), "--ledger", str(path)]
    assert cli.main(argv) == 0
    assert capsys.readouterr().out.splitlines() == [
        "s1 clos : 0.000000 $ facturés",
        "1 réservation(s) orpheline(s) close(s)",
    ]
