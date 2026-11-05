"""Pilote API sur le fournisseur `fake`, plafonds, registre et identité du protocole (AD-10, AD-11,
AD-15)."""

from __future__ import annotations

import dataclasses
import json

import pytest
from conftest import (
    EXAMPLES,
    TEST_PRICE,
    claude_model,
    fake_model,
    read_journal,
    scenario,
    write_examples,
)

from nn_weight_writing.budget import ledger
from nn_weight_writing.providers.fake import FakeProvider, reply
from nn_weight_writing.providers.types import ProviderError, Usage
from nn_weight_writing.session import prompt
from nn_weight_writing.session.api_driver import decode_arguments
from nn_weight_writing.session.tools import catalogue
from nn_weight_writing.tasks.io import BundleError

RULES = 'def predict(raw):\n    return "ok"\n'
# 1000 × 1 + 100 × 2 = 1200 µ$ par appel au tarif de test.
CALL_USAGE = Usage(input=1000, output=100, provider_cost=0.0011)


def freeze_script():
    return [
        reply(calls=[("submit_rules", {"code": RULES})], usage=CALL_USAGE),
        reply(calls=[("run_on_examples", {}), ("freeze", {})], usage=CALL_USAGE),
    ]


def test_frozen_session_journal_and_ledger(session_env):
    provider = FakeProvider(freeze_script())
    outcome = session_env.run(fake_model(), method="B", provider=provider)
    assert (outcome.reason, outcome.billed_usd, outcome.cost_equiv_usd) == (
        "frozen",
        0.0024,
        0.0024,
    )
    records = read_journal(outcome.run_dir)
    calls = [r for r in records if r["type"] == "model_call"]
    assert [(c["cost_equiv_usd"], c["billed_usd"], c["provider_cost"]) for c in calls] == [
        (0.0012, 0.0012, 0.0011),
        (0.0012, 0.0012, 0.0011),
    ]
    assert calls[0]["exchange"]["sent"][0]["role"] == "user"
    # Chaque échange porte ce qui a été envoyé depuis la réponse précédente, puis la réponse.
    assert [m["role"] for m in calls[1]["exchange"]["sent"]] == ["tool"]
    assert calls[1]["exchange"]["response"]["tool_calls"][1]["name"] == "freeze"
    assert records[0]["driver"] == "api" and records[0]["provider"] == "fake"
    rows = ledger.read(session_env.ledger)
    assert [(r.status, r.reserved_usd, r.billed_usd) for r in rows] == [
        ("reserved", 5.0, 0.0),
        ("closed", 0.0, 0.0024),
    ]
    # Le résultat d'outil renvoyé au modèle est celui du service.
    second = provider.requests[1].messages
    assert json.loads(second[-1].text) == {"ok": True}


def test_answer_without_tool_call_ends_in_pass_budget(session_env):
    provider = FakeProvider([reply("J'ai fini.")])
    outcome = session_env.run(fake_model(), method="B", provider=provider)
    assert (outcome.reason, outcome.detail) == ("pass_budget", "l'agent a rendu la main sans geler")


@pytest.mark.parametrize("stop", ["length", "max_tokens"])
def test_truncated_answer_is_error_not_pass_budget(session_env, stop):
    provider = FakeProvider([dataclasses.replace(reply(), stop_reason=stop)])
    outcome = session_env.run(fake_model(), method="B", provider=provider)
    assert outcome.reason == "error"
    assert outcome.detail.startswith(f"réponse tronquée ({stop}) à ")


def test_money_budget_stops_at_session_cap(session_env, protocol):
    capped = dataclasses.replace(protocol, max_session_usd=0.003)
    looping = [reply(calls=[("run_on_examples", {})], usage=CALL_USAGE) for _ in range(10)]
    provider = FakeProvider(looping)
    outcome = session_env.run(fake_model(), method="B", provider=provider, protocol=capped)
    assert outcome.reason == "money_budget"
    assert outcome.detail == "plafond de séance 0.003000 $ atteint"
    # 0.0012, 0.0024, 0.0036 : arrêt au troisième appel, sans exécuter ses outils.
    assert len(provider.requests) == 3
    assert outcome.billed_usd == 0.0036
    records = read_journal(outcome.run_dir)
    assert [r["number"] for r in records if r["type"] == "pass"] == [1, 2]
    rows = ledger.read(session_env.ledger)
    assert (rows[0].reserved_usd, rows[-1].status, rows[-1].billed_usd) == (0.003, "closed", 0.0036)


def test_turn_limit(session_env, protocol):
    limited = dataclasses.replace(protocol, turn_limit=3)
    provider = FakeProvider([reply(calls=[("submit_rules", {"code": RULES})]) for _ in range(9)])
    outcome = session_env.run(fake_model(), method="B", provider=provider, protocol=limited)
    assert (outcome.reason, outcome.detail) == ("turn_limit", "3 tours")
    assert len(provider.requests) == 3


@pytest.mark.parametrize("raw", ["{pas du json", "[1, 2]", "42"])
def test_non_json_tool_arguments_are_refused_not_fatal(session_env, raw):
    provider = FakeProvider([reply(calls=[("submit_rules", raw)]), *freeze_script()])
    outcome = session_env.run(fake_model(), method="B", provider=provider)
    assert outcome.reason == "frozen"
    records = read_journal(outcome.run_dir)
    refusals = [r for r in records if r["type"] == "refusal"]
    assert [r["code"] for r in refusals] == ["invalid_arguments"]
    assert refusals[0]["detail"] == "les arguments doivent être un objet"
    first_tool = next(r for r in records if r["type"] == "tool_call")
    assert first_tool["arguments"] == {"invalid": repr(decode_arguments(raw))}


def test_decode_arguments():
    assert decode_arguments("") == {}
    assert decode_arguments('{"a": 1}') == {"a": 1}
    assert decode_arguments("{x") == "{x"
    assert decode_arguments("[" * 100_000) == "[" * 100_000


def test_provider_error_ends_in_error_and_closes_ledger(session_env):
    provider = FakeProvider(
        [
            reply(calls=[("submit_rules", {"code": RULES})], usage=CALL_USAGE),
            ProviderError("APIStatusError: 503 après 3 tentatives"),
        ]
    )
    outcome = session_env.run(fake_model(), method="B", provider=provider)
    assert outcome.reason == "error"
    assert outcome.detail == "fournisseur fake : APIStatusError: 503 après 3 tentatives"
    rows = ledger.read(session_env.ledger)
    assert (rows[-1].status, rows[-1].billed_usd) == ("closed", 0.0012)


def test_closed_line_written_even_when_session_crashes(session_env):
    bad = write_examples(session_env.tmp / "bad.jsonl", [{**EXAMPLES[0], "label": "ok"}])
    with pytest.raises(BundleError):
        session_env.run(fake_model(), method="B", provider=FakeProvider([]), examples=bad)
    rows = ledger.read(session_env.ledger)
    assert [(r.status, r.billed_usd, r.cost_equiv_usd) for r in rows] == [
        ("reserved", 0.0, 0.0),
        ("closed", 0.0, 0.0),
    ]


def test_opening_refused_beyond_billed_cap_reservations_included(session_env, protocol):
    path = session_env.ledger
    ledger.append(ledger.LedgerRow("t", "old", 1, ledger.Status.CLOSED, billed_usd=94.0), path)
    ledger.append(ledger.LedgerRow("t", "open", 1, ledger.Status.RESERVED, reserved_usd=1.5), path)
    with pytest.raises(ledger.BudgetRefused) as refused:
        session_env.run(fake_model(), method="B", provider=FakeProvider(freeze_script()))
    assert str(refused.value) == (
        "plafond lot 1 : 94.000000 facturés + 1.500000 réservés + 5.000000 > 100.00 $ : "
        "décision d'Anaël requise"
    )
    assert len(ledger.read(path)) == 2
    assert not (session_env.tmp / "runs").exists()
    # Sans la réservation ouverte, la séance passe (94 + 5 ≤ 100).
    ledger.append(ledger.LedgerRow("t", "open", 1, ledger.Status.CLOSED), path)
    outcome = session_env.run(fake_model(), method="B", provider=FakeProvider(freeze_script()))
    assert outcome.reason == "frozen"


def test_subscription_session_opens_even_when_cap_is_reached(session_env, monkeypatch):
    path = session_env.ledger
    ledger.append(ledger.LedgerRow("t", "old", 1, ledger.Status.CLOSED, billed_usd=100.0), path)
    scenario(monkeypatch, session_env.tmp, {"result": {"result": "rien"}})
    outcome = session_env.run(claude_model(), method="B")
    assert outcome.reason == "pass_budget"


@pytest.mark.parametrize("method", ["A-literal", "A-program", "B"])
def test_protocol_identity_across_models_and_drivers(session_env, monkeypatch, method):
    """AD-15 : même prompt système, description, outils et budget, quel que soit le modèle."""
    seen = {}
    for model in (
        fake_model(name="mimo-v2.6-pro", id="xiaomi/mimo-v2.6-pro"),
        fake_model(name="sonnet-5.5-api", id="claude-sonnet-5-5", effort="medium"),
    ):
        provider = FakeProvider([reply("fin")])
        outcome = session_env.run(model, method=method, provider=provider)
        request = provider.requests[0]
        assert len(request.messages) == 1
        seen[model.name] = {
            "system": request.system,
            "task": request.messages[0].text,
            "tools": [(t.name, t.description, t.input_schema) for t in request.tools],
            "open": _open(outcome.run_dir),
        }
    capture = scenario(monkeypatch, session_env.tmp, {"result": {"result": "fin"}})
    outcome = session_env.run(claude_model(), method=method)
    claude = json.loads(capture.read_text("utf-8"))
    seen["sonnet-5.5"] = {
        "system": claude["system_prompt"],
        "task": claude["stdin"],
        "tools": [(t["name"], t["description"], t["input_schema"]) for t in claude["tools"]],
        "open": _open(outcome.run_dir),
    }
    reference = seen["sonnet-5.5"]
    assert reference["system"] == prompt.system_prompt(method, 20)
    assert reference["tools"] == [
        (t.name, t.description, t.input_schema) for t in catalogue(method)
    ]
    assert reference["open"] == (20, prompt.sha256_text(reference["system"]))
    for name, values in seen.items():
        assert values == reference, name


def _open(run_dir) -> tuple[int, str]:
    record = read_journal(run_dir)[0]
    return record["pass_budget"], record["system_prompt_sha256"]


def test_no_key_reaches_the_journal(session_env, monkeypatch):
    key = "sk-or-v1-0123456789abcdefghij"
    monkeypatch.setenv("OPENROUTER_API_KEY", key)
    provider = FakeProvider([reply(f"Ma clé est {key}, en-tête Authorization: Bearer {key}")])
    outcome = session_env.run(fake_model(), method="B", provider=provider)
    text = (outcome.run_dir / "journal.jsonl").read_text("utf-8")
    assert key not in text and "[secret masqué]" in text


@pytest.mark.parametrize("task_name", ["parity", "compare", "automaton"])
def test_toy_session_through_api_driver(tmp_path, protocol, task_name):
    """Séance jouet complète (tâche inscrite par 1-7) par le pilote API et le fournisseur `fake` :
    l'agent scripté écrit les poids de la solution à la main, gèle, et le réseau gelé fait 100 %
    sur le jeu réservé par le chemin d'évaluation."""
    from nn_weight_writing.baselines import handmade
    from nn_weight_writing.datasets.toy import generate
    from nn_weight_writing.evaluation.score import score_frozen
    from nn_weight_writing.network import io as netio
    from nn_weight_writing.session.run import run_session
    from nn_weight_writing.tasks.registry import examples_path, get_task

    _, held = generate(task_name, seed=3, n=32, n_heldout=64, root=tmp_path)
    task = get_task(task_name)
    manifest, weights = handmade.build(task_name)
    writes = [
        (
            "write_weights",
            {
                "layer": int(key[1:].split(".")[0]),
                "param": key.split(".")[1],
                "row_start": 0,
                "rows": value.tolist(),
            },
        )
        for key, value in sorted(weights.items())
    ]
    units = sorted([list(u) for u in netio.hidden_units(manifest)])
    types = [entry["id"] for entry in task.vocabulary]
    blocks = [{"rule": "solution écrite à la main", "types": types, "units": units}]
    provider = FakeProvider(
        [
            reply(calls=[("declare_network", {"manifest": manifest}), *writes], usage=CALL_USAGE),
            reply(
                calls=[("run_on_examples", {}), ("freeze", {"blocks": blocks})], usage=CALL_USAGE
            ),
        ]
    )
    outcome = run_session(
        task=task,
        dataset="toy",
        examples=examples_path(task_name, "toy", tmp_path / "data"),
        method="A-literal",
        model=fake_model(),
        price=TEST_PRICE,
        protocol=protocol,
        attempt=1,
        seed=3,
        lot=1,
        runs_dir=tmp_path / "runs",
        ledger_path=tmp_path / "ledger.csv",
        provider=provider,
    )
    assert (outcome.reason, outcome.billed_usd) == ("frozen", 0.0024)
    records = read_journal(outcome.run_dir)
    assert records[0]["task"] == task_name and records[0]["provider"] == "fake"
    assert "heldout" not in json.dumps(records)
    score = score_frozen(
        outcome.run_dir, task.codec, held / "examples.jsonl", held / "labels.jsonl"
    )
    assert (score.n, score.accuracy) == (64, 1.0)
    assert [r.status for r in ledger.read(tmp_path / "ledger.csv")] == ["reserved", "closed"]
