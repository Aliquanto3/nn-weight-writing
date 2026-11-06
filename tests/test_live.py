"""Un seul appel réel par pilote (story 1-6), marqué `live` et désélectionné par défaut.

Lancer un test : `uv run pytest -m live tests/test_live.py -k openrouter`. Le coût facturé de
l'appel OpenRouter ou Anthropic est inscrit au registre `budget/ledger.csv` (lot 1). Aucune clé
n'est affichée ni écrite.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from conftest import TASK, claude_model, read_journal

from nn_weight_writing.budget import ledger
from nn_weight_writing.budget.cost import billed_usd, cost_equiv_usd
from nn_weight_writing.config import load_models, load_pricing
from nn_weight_writing.providers.types import ChatRequest, Message, TextPart
from nn_weight_writing.session.claude_code import DEFAULT_CONFIG_DIR, config_dir_problems
from nn_weight_writing.session.tools import catalogue

pytestmark = pytest.mark.live
MAX_LIVE_USD = 0.05


def one_call(model_name: str, provider) -> None:
    model = load_models()[model_name]
    price = load_pricing()[model.id]
    request = ChatRequest(
        model=model.id,
        system="Réponds en un mot.",
        messages=(Message("user", (TextPart("Quelle couleur a le ciel par beau temps ?"),)),),
        tools=catalogue("B"),
        max_tokens=64,
        effort=model.effort,
    )
    response = provider.complete(request)
    equiv = cost_equiv_usd(response.usage, price)
    billed = billed_usd(model, equiv)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    ledger.append(
        ledger.LedgerRow(
            ledger.utc_now(),
            f"live-1-6-{model_name}-{stamp}",
            1,
            ledger.Status.CLOSED,
            billed_usd=billed,
            cost_equiv_usd=equiv,
        )
    )
    print(f"{model_name} : {response.usage}, servi par {response.served_by}, {billed:.6f} $")
    assert response.usage.input > 0 and response.usage.output > 0
    assert billed <= MAX_LIVE_USD
    if response.usage.provider_cost is not None:
        # Le calcul tarifaire doit retrouver le coût annoncé (contrôle de AD-11).
        assert abs(response.usage.provider_cost - equiv) <= max(0.1 * equiv, 2e-6)


@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY absente")
def test_openrouter_one_real_call():
    from nn_weight_writing.providers.openrouter import OpenRouterProvider

    model = load_models()["mimo-v2.6-pro"]
    one_call("mimo-v2.6-pro", OpenRouterProvider(provider_order=model.provider_order))


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY absente")
def test_anthropic_one_real_call():
    from nn_weight_writing.providers.anthropic import AnthropicProvider

    one_call("sonnet-5.5-api", AnthropicProvider())


@pytest.mark.skipif(
    bool(config_dir_problems(DEFAULT_CONFIG_DIR)),
    reason="~/.nnww/claude-config non prêt : connexion unique d'Anaël requise",
)
def test_claude_code_one_real_session(tmp_path, protocol):
    """Une séance courte (2 tours) par l'abonnement, dans la configuration dédiée."""
    import dataclasses

    from conftest import EXAMPLES, write_examples

    from nn_weight_writing.session.run import run_session

    short = dataclasses.replace(protocol, turn_limit=2)
    outcome = run_session(
        task=TASK,
        dataset="toy",
        examples=write_examples(tmp_path / "examples.jsonl", EXAMPLES),
        method="B",
        model=claude_model(),
        price=load_pricing()["claude-sonnet-5-5"],
        protocol=short,
        attempt=1,
        seed=7,
        lot=1,
        runs_dir=tmp_path / "runs",
        ledger_path=tmp_path / "ledger.csv",
    )
    records = read_journal(outcome.run_dir)
    calls = [r for r in records if r["type"] == "model_call"]
    print(outcome.reason, outcome.detail, outcome.cost_equiv_usd)
    assert not (outcome.detail or "").startswith(("contamination", "configuration"))
    assert calls and all(c["billed_usd"] == 0.0 for c in calls)
    assert outcome.cost_equiv_usd > 0
    assert outcome.reason in {"frozen", "pass_budget", "turn_limit"}
