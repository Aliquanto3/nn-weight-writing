"""Registre budgétaire (AD-11) : format, déduplication, plafonds, verrou et réconciliation."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from nn_weight_writing.budget import ledger
from nn_weight_writing.budget.ledger import BudgetRefused, LedgerRow, Status

ROOT = Path(__file__).parents[1]


def closed(session: str, billed: float, lot: int = 1) -> LedgerRow:
    return LedgerRow("2026-11-05T00:00:00Z", session, lot, Status.CLOSED, billed_usd=billed)


def test_line_format_without_header(tmp_path):
    path = tmp_path / "ledger.csv"
    row = LedgerRow("2026-11-05T10:00:00Z", "s1", 1, Status.CLOSED, 0.0, 0.0081621, 0.1)
    ledger.append(row, path)
    assert (
        path.read_text("utf-8") == "2026-11-05T10:00:00Z,s1,1,closed,0.000000,0.008162,0.100000\n"
    )


def test_reads_deduplicate_by_session_and_status(tmp_path):
    path = tmp_path / "ledger.csv"
    path.write_text(
        "t1,s1,1,reserved,5.000000,0.000000,0.000000\n"
        "t1,s1,1,reserved,5.000000,0.000000,0.000000\n"
        "\n"
        "t2,s1,1,closed,0.000000,1.250000,1.250000\n"
        "t3,s1,1,closed,0.000000,1.250000,1.250000\n"
        "t4,s2,2,reserved,5.000000,0.000000,0.000000\n",
        "utf-8",
    )
    rows = ledger.read(path)
    assert [(r.session_id, r.status) for r in rows] == [
        ("s1", "reserved"),
        ("s1", "closed"),
        ("s2", "reserved"),
    ]
    assert ledger.spend(rows) == ledger.Spend(billed_usd=1.25, reserved_open_usd=5.0)
    assert ledger.spend(rows, lot=1) == ledger.Spend(billed_usd=1.25, reserved_open_usd=0.0)


def test_malformed_line_is_an_error(tmp_path):
    path = tmp_path / "ledger.csv"
    path.write_text("t,s1,1,closed\n", "utf-8")
    with pytest.raises(ValueError, match="ligne 1 : 4 champs"):
        ledger.read(path)


def test_reserve_checks_lot_and_project_caps(tmp_path, protocol):
    path = tmp_path / "ledger.csv"
    ledger.append(closed("a", 95.0, lot=1), path)
    # 95 + 5 = 100 : à la limite, admis.
    ledger.reserve("s1", 1, 5.0, protocol, path)
    with pytest.raises(BudgetRefused, match=r"plafond lot 1 : 95\.000000 facturés \+ 5\.000000"):
        ledger.reserve("s2", 1, 5.0, protocol, path)
    # Le lot 2 a de la marge, le projet aussi (95 + 5 + 5 ≤ 200).
    ledger.reserve("s3", 2, 5.0, protocol, path)
    ledger.append(closed("b", 91.0, lot=2), path)
    with pytest.raises(BudgetRefused) as refused:
        ledger.reserve("s4", 3, 5.0, protocol, path)
    # 95 + 91 facturés, 5 + 5 réservés : 196 + 5 > 200 ; le lot 3 (25 $) a de la marge.
    assert str(refused.value) == (
        "plafond projet : 186.000000 facturés + 10.000000 réservés + 5.000000 > 200.00 $ : "
        "décision d'Anaël requise"
    )


def test_reserve_refuses_known_session_and_unknown_lot(tmp_path, protocol):
    path = tmp_path / "ledger.csv"
    ledger.reserve("s1", 1, 0.0, protocol, path)
    with pytest.raises(BudgetRefused, match="déjà inscrite"):
        ledger.reserve("s1", 1, 0.0, protocol, path)
    with pytest.raises(ValueError, match="lot 9 sans plafond"):
        ledger.reserve("s9", 9, 1.0, protocol, path)


def test_parallel_reservations_see_each_other(tmp_path, protocol):
    path = tmp_path / "ledger.csv"
    ledger.append(closed("a", 92.0), path)
    results: list[str] = []
    barrier = threading.Barrier(4)

    def attempt(n: int) -> None:
        barrier.wait()
        try:
            ledger.reserve(f"s{n}", 1, 5.0, protocol, path)
            results.append("ok")
        except BudgetRefused:
            results.append("refusé")

    threads = [threading.Thread(target=attempt, args=(n,)) for n in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    # 92 + 5 ≤ 100 pour une seule séance : les trois autres voient sa réservation.
    assert sorted(results) == ["ok", "refusé", "refusé", "refusé"]
    assert not path.with_name("ledger.csv.lock").exists()


def test_reconcile_closes_orphans_from_journals(tmp_path):
    path = tmp_path / "ledger.csv"
    runs = tmp_path / "runs"
    for session in ("with-journal", "without-journal", "done"):
        ledger.append(LedgerRow("t", session, 1, Status.RESERVED, reserved_usd=5.0), path)
    ledger.append(closed("done", 1.0), path)
    journal = runs / "1" / "with-journal" / "journal.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        '{"type": "open"}\n'
        '{"type": "model_call", "billed_usd": 0.25, "cost_equiv_usd": 0.25}\n'
        '{"type": "model_call", "billed_usd": 0.5, "cost_equiv_usd": 0.5}\n',
        "utf-8",
    )
    written = ledger.reconcile(runs, path)
    assert [(r.session_id, r.billed_usd) for r in written] == [
        ("with-journal", 0.75),
        ("without-journal", 0.0),
    ]
    assert ledger.reconcile(runs, path) == []
    assert ledger.spend(ledger.read(path)) == ledger.Spend(billed_usd=1.75, reserved_open_usd=0.0)


def test_repository_ledger_holds_the_probe_line():
    rows = ledger.read(ledger.LEDGER_PATH)
    probe = [r for r in rows if r.session_id == "probe-1-2"]
    assert [(r.status, r.lot, r.billed_usd, r.cost_equiv_usd) for r in probe] == [
        ("closed", 1, 0.008162, 0.008162)
    ]
    assert not ledger.LEDGER_PATH.read_text("utf-8").startswith("ts,")


def test_ledger_merges_by_union():
    attributes = (ROOT / ".gitattributes").read_text("utf-8").splitlines()
    assert "budget/ledger.csv merge=union" in attributes
