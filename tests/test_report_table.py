"""`nnww table` (CAP-12, story 1-14) : tableau régénéré depuis les seuls artefacts."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from artefacts import (
    TYPED_ROWS,
    typed_network,
    typed_spec,
    write_baseline,
    write_heldout,
    write_session,
)

from nn_weight_writing.budget.ledger import LedgerRow, Status
from nn_weight_writing.cli import main
from nn_weight_writing.evaluation.verify import evaluate
from nn_weight_writing.report.decisions import DecisionsError, read_decisions
from nn_weight_writing.report.table import build
from nn_weight_writing.tasks.registry import TASKS

FLAG = {"kind": "fragment_overlap", "count": 4, "example_ids": ["typed-s001"], "samples": ["xx"]}
BLOCKS = [
    {"rule": "A", "types": ["t01"], "units": [[0, 0]]},
    {"rule": "B", "types": ["t02"], "units": [[0, 1]]},
]


def half_network():
    """Ne voit plus B : 4/6 sur TYPED_ROWS."""
    manifest, weights = typed_network()
    weights["L0.W"][1, 1] = 0.0
    return manifest, weights


@pytest.fixture
def root(tmp_path, monkeypatch):
    """Lot de test : t1 rejouée (non gelée puis gelée), t2 gelée à 4/6, t3 non gelée et à
    drapeaux, un témoin C sur deux graines, un réentraînement de la séance t1."""
    monkeypatch.setitem(TASKS, "typed", typed_spec())
    root = tmp_path / "artefacts"
    heldout = root / "heldout"
    write_heldout(heldout, "typed", "eval", TYPED_ROWS)
    lot = root / "runs" / "1"
    write_session(lot, attempt=1, stamp="20261107T010000Z", frozen=False, equiv=0.5)
    t1 = write_session(lot, attempt=1, stamp="20261107T020000Z", blocks=BLOCKS, equiv=0.25)
    t2 = write_session(lot, attempt=2, stamp="20261107T030000Z", network=half_network())
    write_session(lot, attempt=3, stamp="20261107T040000Z", frozen=False, flags=[FLAG])
    flagged = write_session(lot, method="A-program", stamp="20261107T050000Z", flags=[FLAG])
    for seed in (0, 1):
        write_baseline(lot, n=64, seed=seed, network=typed_network() if seed else half_network())
    write_baseline(lot, n=8192, seed=0, retrained_from=t1.name, network=half_network())
    for run_dir in (t1, t2, flagged):
        evaluate(run_dir, heldout)
    for run_dir in sorted(lot.glob("train/*")):
        evaluate(run_dir, heldout)
    return root


def case(table, method="A-literal") -> dict:
    return next(c for c in table.data["cases"] if c["method"] == method)


def write_decisions(path: Path, text: str) -> Path:
    path.write_text(text, "utf-8")
    return path


def test_table_is_byte_reproducible(root, tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    assert main(["table", "--lot", "1", "--root", str(root), "--out", str(first)]) == 0
    assert main(["table", "--lot", "1", "--root", str(root), "--out", str(second)]) == 0
    for name in ("lot1.md", "lot1.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    text = (first / "lot1.md").read_text("utf-8")
    assert "Généré par `nnww table --lot 1` ; ne pas éditer." in text
    assert str(root) not in text  # aucun chemin absolu


def test_table_counts_latest_session_per_attempt(root):
    table = build(root, 1)
    agg = case(table)["after_decisions"]
    assert [(a["attempt"], a["state"]) for a in agg["attempts"]] == [
        (1, "ok"),
        (2, "ok"),
        (3, "unfrozen"),
    ]
    statuses = {s["session"][-16:]: s["status"] for s in table.data["sessions"]}
    assert statuses["20261107T010000Z"] == "replayed"
    assert statuses["20261107T020000Z"] == "counted"
    assert case(table)["replayed"] == {"n": 1, "billed_sum": 0.0}


def test_latest_frozen_session_counts_over_a_later_failure(tmp_path, monkeypatch):
    """Décision Q12 : la dernière séance gelée d'une tentative compte si elle existe."""
    monkeypatch.setitem(TASKS, "typed", typed_spec())
    lot = tmp_path / "runs" / "1"
    write_session(lot, attempt=1, stamp="20261107T010000Z")
    write_session(lot, attempt=1, stamp="20261107T020000Z", frozen=False)
    statuses = {s["session"][-16:]: s["status"] for s in build(tmp_path, 1).data["sessions"]}
    assert statuses == {"20261107T010000Z": "counted", "20261107T020000Z": "replayed"}


def test_unfrozen_attempt_counts_zero_in_main_mean(root):
    """Décision Q7 : moyenne principale (1 + 4/6 + 0) / 3 ; gelées seules (1 + 4/6) / 2."""
    agg = case(build(root, 1))["after_decisions"]
    assert agg["accuracy_mean"] == round((1 + 4 / 6 + 0) / 3, 6)
    assert agg["accuracy_frozen_mean"] == round((1 + 4 / 6) / 2, 6)
    assert agg["accuracy_range"] == [0.0, 1.0]
    assert (agg["frozen"], agg["n"]) == (2, 3)
    assert agg["legibility"] == 1.0  # seule t1 déclare des blocs


def test_table_separates_billed_and_equiv(root, tmp_path):
    lot = root / "runs" / "1"
    write_session(
        lot, method="B", model="api-model", rules=None, billed=0.1, equiv=0.3, driver="api"
    )
    ledger = tmp_path / "ledger.csv"
    rows = [
        LedgerRow("t", "absent-du-lot", 1, Status.CLOSED, 0.0, 0.05, 0.05),
        LedgerRow("t", "autre-lot", 2, Status.CLOSED, 0.0, 9.0, 9.0),
    ]
    ledger.write_text("".join(r.to_line() for r in rows), "utf-8")
    table = build(root, 1, ledger_path=ledger)
    api = next(c for c in table.data["cases"] if c["model"] == "api-model")["after_decisions"]
    assert (api["billed_sum"], api["equiv_sum"]) == (0.1, 0.3)
    costs = table.data["costs"]
    assert costs["billed_usd"] == 0.1
    assert costs["cost_equiv_usd"] == round(0.5 + 0.25 + 0.25 + 0.25 + 0.25 + 0.3, 6)
    assert costs["ledger_billed_usd"] == 0.05 and costs["gap_billed_usd"] == 0.05
    assert costs["only_in_ledger"] == ["absent-du-lot"]
    assert len(costs["only_in_journals"]) == 6
    assert costs["lot_cap_usd"] == 100.0 and costs["billed_share_of_cap"] == 0.001
    md = table.markdown
    assert "Facturé ($, somme ; médiane)" in md and "Équivalent API ($, somme ; médiane)" in md


def test_table_reads_only_runs_and_ledger(root, tmp_path):
    before = build(root, 1)
    lot = root / "runs" / "1"
    (lot / "courbe-c-f.jsonl").write_text("pas du json", "utf-8")
    (lot / "reentrainement.jsonl").write_text("pas du json", "utf-8")
    some = next(p for p in lot.iterdir() if (p / "journal.jsonl").is_file())
    (some / "bundle").mkdir()
    (some / "bundle" / "examples.jsonl").write_text("{", "utf-8")
    (some / "notes.json").write_text("{", "utf-8")
    after = build(root, 1)
    assert after.markdown == before.markdown and after.data == before.data
    files = sorted(after.data["inputs"].items())
    assert files == sorted(before.data["inputs"].items())
    assert after.data["inputs"]["journals"] == 5 and after.data["inputs"]["run_json"] == 3


def test_baselines_and_same_network(root):
    table = build(root, 1)
    [c64] = table.data["baselines"]
    assert (c64["baseline"], c64["n"], c64["seeds"], c64["encoder"]) == (
        "C",
        64,
        [0, 1],
        "typed.ab@1",
    )
    assert c64["accuracy_mean"] == round((4 / 6 + 1) / 2, 6)
    assert c64["accuracy_sd"] is not None and c64["chemin"] == ""
    [same] = table.data["same_network"]
    assert same["session_accuracy"] == 1.0 and same["retrained_mean"] == round(4 / 6, 6)
    assert same["gap"] == round(4 / 6 - 1, 6)


def test_strict_fails_on_unjudged_flagged_session(root, tmp_path, capsys):
    out = tmp_path / "out"
    argv = ["table", "--lot", "1", "--root", str(root), "--out", str(out), "--strict"]
    assert main(argv) == 1
    assert "à juger" in capsys.readouterr().err
    flagged = next(p.name for p in (root / "runs" / "1").iterdir() if "-A-program-" in p.name)
    unjudged_attempt = next(
        p.name for p in (root / "runs" / "1").iterdir() if p.name.endswith("040000Z")
    )
    decisions = write_decisions(
        tmp_path / "d.toml",
        f'[[session]]\nid = "{flagged}"\nstatus = "kept"\naudit = "judged"\n'
        f'date = "2026-11-08"\nreason = "format seul"\nref = "journal"\n',
    )
    # t3 (non gelée, à drapeaux) est comptée : sans jugement, --strict échoue encore.
    assert main([*argv, "--decisions", str(decisions)]) == 1
    decisions.write_text(
        decisions.read_text("utf-8")
        + f'\n[[session]]\nid = "{unjudged_attempt}"\nstatus = "kept"\naudit = "judged"\n'
        f'date = "2026-11-08"\nreason = "aucune recopie"\n',
        "utf-8",
    )
    capsys.readouterr()
    assert main([*argv, "--decisions", str(decisions)]) == 0
    text = (out / "lot1.md").read_text("utf-8")
    assert "maintenue, 2026-11-08 : format seul" in text
    assert "à juger" not in text


def test_pending_decision_keeps_strict_red(root, tmp_path):
    flagged = next(p.name for p in (root / "runs" / "1").iterdir() if "-A-program-" in p.name)
    decisions = write_decisions(
        tmp_path / "d.toml",
        f'[[session]]\nid = "{flagged}"\nstatus = "pending"\ndate = "2026-11-07"\n'
        f'reason = "à juger en 1-14b"\n',
    )
    table = build(root, 1, decisions_path=decisions)
    assert f"décision à juger : session:{flagged}" in table.issues


def test_decision_unknown_id_is_error(root, tmp_path, capsys):
    decisions = write_decisions(
        tmp_path / "d.toml",
        '[[session]]\nid = "inconnue"\nstatus = "excluded"\ndate = "2026-11-08"\nreason = "x"\n',
    )
    argv = ["table", "--lot", "1", "--root", str(root), "--out", str(tmp_path / "o")]
    assert main([*argv, "--decisions", str(decisions)]) == 1
    assert "inconnue" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()
    decisions.write_text(
        '[[group]]\ntask = "absente"\nstatus = "annex"\ndate = "2026-11-08"\nreason = "x"\n',
        "utf-8",
    )
    with pytest.raises(DecisionsError, match="ne vise aucun artefact"):
        build(root, 1, decisions_path=decisions)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('[[session]]\nid = "a"\nstatus = "gardée"\ndate = "d"\nreason = "r"\n', "status"),
        ('[[session]]\nid = "a"\nstatus = "kept"\nreason = "r"\n', "date obligatoire"),
        (
            '[[session]]\nid = "a"\nstatus = "kept"\ndate = "d"\nreason = "r"\nmesure = 1\n',
            "inconnues",
        ),
        ('[[group]]\nstatus = "kept"\ndate = "d"\nreason = "r"\n', "obligatoire"),
        ("[[autre]]\n", "sections inconnues"),
    ],
)
def test_decisions_file_is_validated(tmp_path, text, message):
    with pytest.raises(DecisionsError, match=message):
        read_decisions(write_decisions(tmp_path / "d.toml", text))


def test_excluded_session_leaves_aggregates(root, tmp_path):
    t2 = next(p.name for p in (root / "runs" / "1").iterdir() if p.name.endswith("030000Z"))
    decisions = write_decisions(
        tmp_path / "d.toml",
        f'[[session]]\nid = "{t2}"\nstatus = "excluded"\ndate = "2026-11-08"\n'
        f'reason = "jeu réservé lu"\n',
    )
    table = build(root, 1, decisions_path=decisions)
    row = case(table)
    assert row["all_sessions"]["n"] == 3
    assert row["after_decisions"]["n"] == 2
    assert row["after_decisions"]["accuracy_frozen_mean"] == 1.0
    assert {"path": t2, "status": "excluded", "reason": "jeu réservé lu"} in table.data["removed"]
    session = next(s for s in table.data["sessions"] if s["session"] == t2)
    assert session["status"] == "excluded"
    assert f"{t2} : écartée (jeu réservé lu)" in table.markdown


def test_group_decision_marks_baselines_as_annex(root, tmp_path):
    lot = root / "runs" / "1"
    write_baseline(lot, baseline="F", n=64, seed=0, chemin="annexe-fields1")
    decisions = write_decisions(
        tmp_path / "d.toml",
        '[[group]]\npath = "annexe-fields1"\nstatus = "annex"\ndate = "2026-11-08"\n'
        'reason = "fields@1"\n',
    )
    table = build(root, 1, decisions_path=decisions)
    annex = next(b for b in table.data["baselines"] if b["chemin"] == "annexe-fields1")
    assert annex["status"] == ["annex"]
    assert any(r["status"] == "annex" for r in table.data["removed"])
    assert "annexe-fields1/train/typed-F-n64-s0" in table.data["not_evaluated"]


def test_report_follows_dependency_graph():
    """`report/` n'importe ni session, ni providers, ni sandbox, ni baselines, ni torch."""
    package = Path(__file__).resolve().parents[1] / "src" / "nn_weight_writing" / "report"
    forbidden = ("session", "providers", "sandbox", "baselines", "torch")
    allowed = ("journal", "budget", "config", "report", "evaluation.schema")
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert not any(name.split(".")[0] == f for f in forbidden), (path.name, name)
                if name.startswith("nn_weight_writing."):
                    sub = name.removeprefix("nn_weight_writing.")
                    assert sub.startswith(allowed), (path.name, name)


def test_cli_table_output_is_valid_json(root, tmp_path):
    out = tmp_path / "out"
    assert main(["table", "--lot", "1", "--root", str(root), "--out", str(out)]) == 0
    data = json.loads((out / "lot1.json").read_text("utf-8"))
    assert data["lot"] == 1 and len(data["inputs"]["fingerprint"]) == 64


def test_excluded_baseline_seed_leaves_mean(root, tmp_path):
    """Revue 1-14 : un témoin écarté forme sa propre ligne, hors de la moyenne des graines."""
    decisions = write_decisions(
        tmp_path / "d.toml",
        '[[session]]\nid = "typed-C-n64-s0"\nstatus = "excluded"\ndate = "2026-11-08"\n'
        'reason = "graine invalide"\n',
    )
    table = build(root, 1, decisions_path=decisions)
    rows = {tuple(b["status"]): b for b in table.data["baselines"]}
    assert rows[("counted",)]["seeds"] == [1] and rows[("counted",)]["accuracy_mean"] == 1.0
    assert rows[("excluded",)]["seeds"] == [0]


def test_excluded_retrained_seed_leaves_same_network(root, tmp_path):
    t1 = next(s for s in build(root, 1).data["same_network"])["session"]
    decisions = write_decisions(
        tmp_path / "d.toml",
        f'[[session]]\nid = "{t1}-retrain-n8192-s0"\nstatus = "excluded"\n'
        'date = "2026-11-08"\nreason = "graine invalide"\n',
    )
    [same] = build(root, 1, decisions_path=decisions).data["same_network"]
    assert same["retrained_mean"] is None and same["removed_seeds"] == [0]


def test_fingerprint_ignores_eval_timestamp(root):
    """Revue 1-14 : relancer `nnww evaluate` (seul `ts` change) ne change pas le tableau."""
    first = build(root, 1)
    heldout = root / "heldout"
    for run_dir in sorted((root / "runs" / "1").glob("train/*")):
        path = run_dir / "eval.json"
        data = json.loads(path.read_text("utf-8"))
        data["ts"] = "2099-01-01T00:00:00Z"
        path.write_text(json.dumps(data), "utf-8")
    assert heldout.is_dir()
    assert build(root, 1).markdown == first.markdown
