"""Service d'outils : passes, production, gel, audit et journal (AD-6, AD-7, AD-8, AD-15)."""

from __future__ import annotations

import subprocess

import pytest
from conftest import BLOCKS, MANIFEST, journal_records, write_literal_network

from nn_weight_writing.journal.reader import read_records
from nn_weight_writing.network import io as netio
from nn_weight_writing.session.refusals import EndReason, RefusalCode

RULES = """import re

def predict(raw):
    return "ok" if re.search(r"[0-9]", raw) else "err"
"""

SCRIPT = """import numpy as np

def build():
    return {
        "L0.W": np.array([[1, 0, 0.5], [0, 1, 0.5]]),
        "L0.b": np.zeros(3),
        "L1.W": np.array([[1], [1], [-1]]),
        "L1.b": np.array([0.25]),
    }
"""


def refusals(service) -> list[str]:
    return [r["code"] for r in journal_records(service) if r["type"] == "refusal"]


def test_budget_of_twenty_then_pass_refused(make_service, protocol):
    assert protocol.pass_budget == 20
    service = make_service("A-literal")
    write_literal_network(service)
    for n in range(1, 21):
        result = service.call("run_on_examples")
        assert (result["pass"], result["remaining"], result["valid"]) == (n, 20 - n, True)
        assert set(result) == {"pass", "remaining", "valid", "outputs", "error"}
    refused = service.call("run_on_examples")
    assert refused["refused"] == RefusalCode.PASS_BUDGET_EXHAUSTED
    assert service.passes_used == 20
    passes = [r for r in journal_records(service) if r["type"] == "pass"]
    assert [p["number"] for p in passes] == list(range(1, 21))
    assert refusals(service) == ["pass_budget_exhausted"]


def test_pass_returns_outputs_never_a_score(make_service):
    service = make_service("A-literal")
    write_literal_network(service)
    result = service.call("run_on_examples")
    # e2 = "CE, 3 juin 2020" : x = [1.5, 0.5] ; h = [1.5, 0.5, 1.0] ; y = 1.5 + 0.5 - 1 + 0.25.
    by_id = {o["id"]: o for o in result["outputs"]}
    assert by_id["e2"] == {"id": "e2", "output": [1.25], "label": "ok"}
    assert [o["id"] for o in result["outputs"]] == ["e1", "e2", "e3"]
    text = str(result).lower()
    assert "score" not in text and "accuracy" not in text and "correct" not in text


def test_invalid_pass_is_counted(make_service):
    service = make_service("A-literal")
    result = service.call("run_on_examples")
    assert (result["pass"], result["remaining"], result["valid"]) == (1, 19, False)
    assert result["outputs"] == []
    service.call("declare_network", {"manifest": MANIFEST})
    half = service.call("run_on_examples")  # poids incomplets : invalide, décomptée
    assert (half["pass"], half["valid"]) == (2, False)
    b = make_service("B")
    no_rules = b.call("run_on_examples")
    assert (no_rules["pass"], no_rules["valid"], no_rules["error"]) == (
        1,
        False,
        "aucune règle soumise",
    )


def test_only_freeze_after_last_pass(make_service):
    service = make_service("A-literal")
    write_literal_network(service)
    for _ in range(20):
        service.call("run_on_examples")
    assert service.call("declare_network", {"manifest": MANIFEST})["refused"] == (
        RefusalCode.MUTATION_AFTER_BUDGET
    )
    write = {"layer": 0, "param": "b", "row_start": 0, "rows": [1, 1, 1]}
    assert service.call("write_weights", write)["refused"] == RefusalCode.MUTATION_AFTER_BUDGET
    assert service.call("run_on_examples")["refused"] == RefusalCode.PASS_BUDGET_EXHAUSTED
    assert service.call("freeze", {"blocks": BLOCKS}) == {"frozen": True}
    assert service.passes_used == 20


def test_rules_refused_after_last_pass(make_service):
    service = make_service("B")
    for _ in range(20):
        service.call("run_on_examples")
    result = service.call("submit_rules", {"code": RULES})
    assert result["refused"] == RefusalCode.MUTATION_AFTER_BUDGET
    assert service.rules is None


def test_literal_freeze_writes_frozen_and_ends(make_service):
    service = make_service("A-literal")
    write_literal_network(service)
    assert service.call("freeze", {"blocks": BLOCKS}) == {"frozen": True}
    assert service.passes_used == 0  # le contrôle de validité ne consomme pas de passe
    records = journal_records(service)
    freeze = next(r for r in records if r["type"] == "freeze")
    frozen = service.run_dir / "frozen"
    assert sorted(p.name for p in frozen.iterdir()) == ["manifest.json", "weights.npz"]
    for name, digest in freeze["files"].items():
        assert netio.sha256_file(frozen / name) == digest
    assert freeze["tree_sha256"] == netio.tree_sha256(freeze["files"])
    assert freeze["valid"] is True
    assert freeze["size_nominal"] == 2 * 3 + 3 + 3 * 1 + 1
    assert freeze["size_script_bytes"] == 0
    assert freeze["size_weights_zlib"] > 0
    manifest, weights = netio.load(frozen)
    assert manifest["blocks"] == BLOCKS
    assert weights["L1.b"].tolist() == [0.25]
    assert [r["type"] for r in records[-3:]] == ["freeze", "tool_call", "end"]
    assert records[-1]["reason"] == EndReason.FROZEN
    assert service.call("run_on_examples")["refused"] == RefusalCode.SESSION_CLOSED


@pytest.mark.parametrize(
    ("blocks", "code"),
    [
        (None, RefusalCode.INVALID_BLOCKS),
        ([{"rule": "r", "types": ["T1"], "units": [[0, 0], [0, 1]]}], RefusalCode.INVALID_BLOCKS),
        (
            [
                {"rule": "r", "types": ["T1"], "units": [[0, 0], [0, 1], [0, 2]]},
                {"rule": "s", "types": ["T2"], "units": [[0, 2]]},
            ],
            RefusalCode.INVALID_BLOCKS,
        ),
        (
            [{"rule": "r", "types": ["T1"], "units": [[0, 0], [0, 1], [0, 2], [1, 0]]}],
            RefusalCode.INVALID_BLOCKS,
        ),
        (
            [{"rule": "r", "types": ["T9"], "units": [[0, 0], [0, 1], [0, 2]]}],
            RefusalCode.TYPE_NOT_IN_VOCABULARY,
        ),
        (
            [{"rule": " ", "types": ["T1"], "units": [[0, 0], [0, 1], [0, 2]]}],
            RefusalCode.INVALID_BLOCKS,
        ),
        (
            [{"rule": "r", "types": [], "units": [[0, 0], [0, 1], [0, 2]]}],
            RefusalCode.INVALID_BLOCKS,
        ),
    ],
    ids=[
        "absent",
        "incomplet",
        "doublon",
        "unite-de-sortie",
        "type-inconnu",
        "sans-regle",
        "sans-type",
    ],
)
def test_freeze_refused_on_bad_blocks(make_service, blocks, code):
    service = make_service("A-literal")
    write_literal_network(service)
    args = {} if blocks is None else {"blocks": blocks}
    assert service.call("freeze", args)["refused"] == code
    assert not (service.run_dir / "frozen").exists()
    assert not service.ended


def test_freeze_attempts_capped_at_three(make_service, protocol):
    assert protocol.max_freeze_attempts == 3
    service = make_service("A-literal")
    write_literal_network(service)
    for _ in range(3):
        assert service.call("freeze", {})["refused"] == RefusalCode.INVALID_BLOCKS
    result = service.call("freeze", {"blocks": BLOCKS})
    assert result["refused"] == RefusalCode.FREEZE_ATTEMPTS_EXHAUSTED


def test_third_freeze_attempt_still_allowed(make_service):
    service = make_service("A-literal")
    write_literal_network(service)
    service.call("freeze", {})
    service.call("freeze", {"blocks": BLOCKS[:1]})
    assert service.call("freeze", {"blocks": BLOCKS}) == {"frozen": True}


def test_freeze_refused_without_production(make_service):
    literal = make_service("A-literal")
    assert literal.call("freeze", {"blocks": BLOCKS})["refused"] == RefusalCode.NO_PRODUCTION
    literal.call("declare_network", {"manifest": MANIFEST})
    assert literal.call("freeze", {"blocks": BLOCKS})["refused"] == RefusalCode.WEIGHTS_INCOMPLETE
    b = make_service("B")
    assert b.call("freeze")["refused"] == RefusalCode.NO_PRODUCTION


def test_rules_session_end_to_end(make_service, monkeypatch):
    service = make_service("B")
    assert service.call("submit_rules", {"code": RULES}) == {"ok": True}
    spawned = []
    real_run = subprocess.run

    def counting_run(*args, **kwargs):
        spawned.append(args[0])
        return real_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", counting_run)
    result = service.call("run_on_examples")
    assert len(spawned) == 1  # un seul sous-processus par passe (D5)
    assert result["valid"] is True
    assert [o["label"] for o in result["outputs"]] == ["ok", "ok", "err"]
    assert service.call("freeze", {"blocks": []})["refused"] == RefusalCode.INVALID_BLOCKS
    assert service.call("freeze") == {"frozen": True}
    freeze = next(r for r in journal_records(service) if r["type"] == "freeze")
    assert list(freeze["files"]) == ["rules.py"]
    assert freeze["size_script_bytes"] == len(RULES.encode("utf-8"))
    assert (freeze["size_nominal"], freeze["size_weights_zlib"], freeze["blocks"]) == (0, 0, None)


def test_program_session(make_service):
    service = make_service("A-program")
    assert service.call("submit_script", {"code": SCRIPT})["refused"] == (
        RefusalCode.NO_NETWORK_DECLARED
    )
    service.call("declare_network", {"manifest": MANIFEST})
    wrong = SCRIPT.replace('"L1.b": np.array([0.25])', '"L1.b": np.array([0.25, 1.0])')
    result = service.call("submit_script", {"code": wrong})
    assert result["ok"] is False and "L1.b" in result["error"]
    assert service.weights is None
    fitting = "import numpy as np\nfrom numpy.linalg import lstsq as f\ndef build():\n    return {}"
    assert service.call("submit_script", {"code": fitting})["refused"] == (
        RefusalCode.FITTING_FUNCTION
    )
    assert service.call("submit_script", {"code": SCRIPT}) == {"ok": True, "error": None, "log": ""}
    assert service.passes_used == 0  # soumettre n'est pas une passe
    by_id = {o["id"]: o for o in service.call("run_on_examples")["outputs"]}
    assert by_id["e2"]["output"] == [1.25]
    assert service.call("declare_network", {"manifest": MANIFEST})["refused"] == (
        RefusalCode.NETWORK_HAS_WEIGHTS
    )
    assert service.call("freeze", {"blocks": BLOCKS}) == {"frozen": True}
    records = journal_records(service)
    runs = [r for r in records if r["type"] == "script_run"]
    assert [r["ok"] for r in runs] == [False, False, True]
    freeze = next(r for r in records if r["type"] == "freeze")
    assert sorted(freeze["files"]) == ["manifest.json", "script.py", "weights.npz"]
    assert freeze["size_script_bytes"] == len(SCRIPT.encode("utf-8"))


def test_audit_flags_logged_without_refusal(make_service):
    service = make_service("B")
    copied = 'KNOWN = "12 mai 2021, n"\n'  # 14 caractères recopiés de e1
    loop = "for i in range(3):\n    pass\n"
    assert service.call("submit_rules", {"code": copied + loop + RULES}) == {"ok": True}
    run = next(r for r in journal_records(service) if r["type"] == "script_run")
    kinds = {flag["kind"]: flag for flag in run["flags"]}
    assert kinds["fragment_overlap"]["example_ids"] == ["e1"]
    assert kinds["fragment_overlap"]["count"] == 3  # 14 - 12 + 1 fenêtres
    assert kinds["example_sized_loop"]["lines"] == [2]
    assert refusals(service) == []


def test_eleven_chars_raise_no_flag(make_service):
    service = make_service("B")
    service.call("submit_rules", {"code": 'K = "12 mai 2021"\n' + RULES})
    run = next(r for r in journal_records(service) if r["type"] == "script_run")
    assert run["flags"] == []


def test_catalogue_refusals(make_service):
    service = make_service("B")
    assert service.call("read_heldout")["refused"] == RefusalCode.UNKNOWN_TOOL
    write = {"layer": 0, "param": "W", "row_start": 0, "rows": [[1]]}
    assert service.call("write_weights", write)["refused"] == RefusalCode.METHOD_NOT_ALLOWED
    assert service.call("submit_rules", {"code": 3})["refused"] == RefusalCode.INVALID_ARGUMENTS
    assert service.call("submit_rules", {"code": "x", "extra": 1})["refused"] == (
        RefusalCode.INVALID_ARGUMENTS
    )
    assert service.call("run_on_examples", [1])["refused"] == RefusalCode.INVALID_ARGUMENTS
    assert service.call("submit_rules", {"code": "import os\n"})["refused"] == (
        RefusalCode.FORBIDDEN_IMPORT
    )
    assert service.passes_used == 0


def test_network_declaration_refusals(make_service):
    service = make_service("A-literal")
    bad = {**MANIFEST, "encoder": "autre@1"}
    assert service.call("declare_network", {"manifest": bad})["refused"] == (
        RefusalCode.ENCODER_MISMATCH
    )
    broken = {"encoder": MANIFEST["encoder"], "layers": [{"type": "conv", "in": 2, "out": 1}]}
    assert service.call("declare_network", {"manifest": broken})["refused"] == (
        RefusalCode.INVALID_MANIFEST
    )
    service.call("declare_network", {"manifest": MANIFEST})
    too_many = {"layer": 0, "param": "W", "row_start": 1, "rows": [[1, 1, 1], [1, 1, 1]]}
    assert service.call("write_weights", too_many)["refused"] == RefusalCode.INVALID_WEIGHTS
    nan = {"layer": 0, "param": "b", "row_start": 0, "rows": [1, float("nan"), 1]}
    assert service.call("write_weights", nan)["refused"] == RefusalCode.INVALID_WEIGHTS
    ok = {"layer": 0, "param": "b", "row_start": 0, "rows": [1, 2, 3]}
    assert service.call("write_weights", ok) == {"written": 3, "rows_remaining": 6}
    assert service.call("declare_network", {"manifest": MANIFEST})["refused"] == (
        RefusalCode.NETWORK_HAS_WEIGHTS
    )


def test_journal_envelope_and_open_event(make_service, protocol):
    service = make_service("A-literal")
    write_literal_network(service)
    service.call("run_on_examples")
    service.end(EndReason.PASS_BUDGET)
    records = list(read_records(service.run_dir / "journal.jsonl"))
    assert [r["seq"] for r in records] == list(range(len(records)))
    assert all(r["schema_version"] == 1 and r["ts"].endswith("Z") for r in records)
    opening = records[0]
    assert opening["type"] == "open"
    assert opening["pass_budget"] == 20
    assert opening["protocol_sha256"] == protocol.protocol_sha256
    assert (opening["driver"], opening["provider"], opening["model"]) == (
        "test-driver",
        "test-provider",
        "test-model",
    )
    assert opening["sampling"] == {"temperature": 1.0} and opening["effort"] == "medium"
    assert records[-1]["type"] == "end" and records[-1]["reason"] == "pass_budget"
    assert records[-1]["passes_used"] == 1
    with pytest.raises(RuntimeError):
        service.end(EndReason.ERROR)


def test_no_key_pattern_in_journal(make_service, monkeypatch):
    secret = "sk-or-v1-0123456789abcdef0123456789abcdef"
    monkeypatch.setenv("OPENROUTER_API_KEY", "valeur-secrete-de-test-123")
    service = make_service("B")
    code = (
        f"# {secret}\n# Authorization: Bearer abcdefgh12345678\n"
        f"# valeur-secrete-de-test-123\n# sk-ant-api03-ABCDEFGHIJKLMNOP\n{RULES}"
    )
    service.call("submit_rules", {"code": code})
    service.end(EndReason.ERROR)
    text = (service.run_dir / "journal.jsonl").read_text("utf-8")
    for needle in ("sk-or-", "sk-ant-", "Bearer abcdefgh", "valeur-secrete", "Authorization:"):
        assert needle not in text
    assert "[secret masqué]" in text


@pytest.mark.parametrize(
    "rows",
    [[[10**400, 1, 1]], [["1.0", 1, 1]], [[True, 1, 1]], [[None, 1, 1]], [[[1], 1, 1]]],
    ids=["entier-hors-float", "chaine", "booleen", "none", "imbrique"],
)
def test_write_weights_refuses_non_numbers_without_crashing(make_service, rows):
    service = make_service("A-literal")
    service.call("declare_network", {"manifest": MANIFEST})
    write = {"layer": 0, "param": "W", "row_start": 0, "rows": rows}
    assert service.call("write_weights", write)["refused"] == RefusalCode.INVALID_WEIGHTS
    calls = [r for r in journal_records(service) if r["type"] == "tool_call"]
    assert calls[-1]["tool"] == "write_weights"
    assert refusals(service) == ["invalid_weights"]


@pytest.mark.parametrize("tool", ["submit_rules", "submit_script"])
def test_too_complex_code_is_refused_not_raised(make_service, tool):
    service = make_service("B" if tool == "submit_rules" else "A-program")
    service.call("declare_network", {"manifest": MANIFEST}) if tool == "submit_script" else None
    code = "x = " + "+".join(["1"] * 60_000)
    assert service.call(tool, {"code": code})["refused"] == RefusalCode.CODE_TOO_COMPLEX
