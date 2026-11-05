"""Adaptateurs `openrouter` et `anthropic` (AD-10) : vrais SDK, réseau remplacé par un transport
simulé ; normalisation de l'usage et formule de coût (AD-11)."""

from __future__ import annotations

import json

import httpx2
import pytest
from conftest import TEST_PRICE, claude_model, fake_model

from nn_weight_writing.budget.cost import billed_usd, cost_equiv_usd
from nn_weight_writing.config import load_models, load_pricing
from nn_weight_writing.providers import anthropic as anthropic_adapter
from nn_weight_writing.providers import openrouter
from nn_weight_writing.providers.anthropic import AnthropicProvider
from nn_weight_writing.providers.openrouter import OpenRouterProvider
from nn_weight_writing.providers.types import (
    ChatRequest,
    Message,
    ProviderError,
    TextPart,
    ToolCall,
    Usage,
)
from nn_weight_writing.session.tools import catalogue

KEY = "sk-or-v1-test-0000000000000000"


def request(**overrides) -> ChatRequest:
    messages = (
        Message("user", (TextPart("tâche"),)),
        Message("assistant", (), (ToolCall("c1", "run_on_examples", "{}"),)),
        Message("tool", (TextPart('{"pass": 1}'),), tool_call_id="c1"),
    )
    values = {
        "model": "xiaomi/mimo-v2.6-pro",
        "system": "système",
        "messages": messages,
        "tools": catalogue("B"),
        "max_tokens": 1000,
    }
    return ChatRequest(**{**values, **overrides})


def chat_completion(usage: dict, **message) -> dict:
    return {
        "id": "gen-1",
        "object": "chat.completion",
        "created": 1,
        "model": "xiaomi/mimo-v2.6-pro",
        "provider": "Xiaomi",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "message": {"role": "assistant", "content": None, **message},
            }
        ],
        "usage": usage,
    }


def transport(responses: list[tuple[int, dict]], seen: list):
    queue = iter(responses)

    def handler(req: httpx2.Request) -> httpx2.Response:
        seen.append(req)
        status, body = next(queue)
        return httpx2.Response(status, json=body)

    return httpx2.Client(transport=httpx2.MockTransport(handler))


def test_openrouter_body_pins_provider_and_requests_cost():
    body = openrouter.build_body(request(sampling={"temperature": 1.0}), ("xiaomi",))
    assert body["provider"] == {"order": ["xiaomi"], "allow_fallbacks": False}
    assert body["usage"] == {"include": True}
    assert (body["max_tokens"], body["temperature"]) == (1000, 1.0)
    assert body["messages"] == [
        {"role": "system", "content": "système"},
        {"role": "user", "content": "tâche"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "run_on_examples", "arguments": "{}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "c1", "content": '{"pass": 1}'},
    ]
    assert [t["function"]["name"] for t in body["tools"]] == [
        "submit_rules",
        "run_on_examples",
        "freeze",
    ]
    assert "reasoning" not in body
    assert openrouter.build_body(request(effort="high"), ())["reasoning"] == {"effort": "high"}
    assert "provider" not in openrouter.build_body(request(), ())


def test_openrouter_call_through_sdk_normalizes_usage():
    usage = {
        "prompt_tokens": 4180,
        "completion_tokens": 45,
        "total_tokens": 4225,
        "cost": 0.00005013,
        "prompt_tokens_details": {"cached_tokens": 4096, "cache_write_tokens": 0},
    }
    call = {"id": "t1", "type": "function", "function": {"name": "freeze", "arguments": "{}"}}
    seen: list = []
    client = transport([(200, chat_completion(usage, tool_calls=[call]))], seen)
    provider = OpenRouterProvider(provider_order=("xiaomi",), api_key=KEY, http_client=client)
    response = provider.complete(request())
    assert response.usage == Usage(
        input=84, output=45, cache_read=4096, cache_write=0, provider_cost=0.00005013
    )
    assert response.message.tool_calls == (ToolCall("t1", "freeze", "{}"),)
    assert (response.served_by, response.stop_reason) == ("Xiaomi", "tool_calls")
    sent = json.loads(seen[0].content)
    assert str(seen[0].url) == "https://openrouter.ai/api/v1/chat/completions"
    assert sent["provider"] == {"order": ["xiaomi"], "allow_fallbacks": False}
    assert sent["usage"] == {"include": True} and sent["model"] == "xiaomi/mimo-v2.6-pro"


def test_openrouter_retries_transient_errors_in_the_adapter():
    seen: list = []
    ok = chat_completion({"prompt_tokens": 10, "completion_tokens": 2}, content="fin")
    client = transport([(503, {"error": {"message": "surcharge"}}), (200, ok)], seen)
    provider = OpenRouterProvider(api_key=KEY, http_client=client, max_retries=1)
    response = provider.complete(request())
    assert len(seen) == 2
    assert response.message.text == "fin"
    assert response.usage == Usage(input=10, output=2)


def test_openrouter_failure_after_retries_is_a_provider_error():
    seen: list = []
    client = transport([(400, {"error": {"message": "mauvais modèle"}})], seen)
    provider = OpenRouterProvider(api_key=KEY, http_client=client, max_retries=0)
    with pytest.raises(ProviderError, match="BadRequestError"):
        provider.complete(request())


def test_openrouter_response_without_choices():
    with pytest.raises(ProviderError, match="réponse sans choix"):
        openrouter.parse_response({"error": {"message": "x"}})


def test_missing_keys_raise(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="OPENROUTER_API_KEY absente"):
        OpenRouterProvider()
    with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY absente"):
        AnthropicProvider()


def test_anthropic_params_cache_points_and_tool_results():
    two_results = request(
        messages=(
            Message("user", (TextPart("tâche"),)),
            Message(
                "assistant",
                (TextPart("je lance"),),
                (ToolCall("a", "submit_rules", '{"code": "x"}'), ToolCall("b", "freeze", "{")),
            ),
            Message("tool", (TextPart("r1"),), tool_call_id="a"),
            Message("tool", (TextPart("r2"),), tool_call_id="b"),
        ),
        effort="medium",
    )
    params = anthropic_adapter.build_params(two_results)
    assert params["system"] == [
        {"type": "text", "text": "système", "cache_control": {"type": "ephemeral"}}
    ]
    assert params["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in params["tools"][0]
    assert params["output_config"] == {"effort": "medium"}
    assert params["messages"] == [
        {"role": "user", "content": [{"type": "text", "text": "tâche"}]},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "je lance"},
                {"type": "tool_use", "id": "a", "name": "submit_rules", "input": {"code": "x"}},
                {"type": "tool_use", "id": "b", "name": "freeze", "input": {}},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "a", "content": "r1"},
                {
                    "type": "tool_result",
                    "tool_use_id": "b",
                    "content": "r2",
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        },
    ]


def test_anthropic_call_through_sdk():
    body = {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-5-5",
        "stop_reason": "tool_use",
        "content": [
            {"type": "text", "text": "Je gèle."},
            {"type": "tool_use", "id": "tu1", "name": "freeze", "input": {}},
        ],
        "usage": {
            "input_tokens": 85,
            "output_tokens": 30,
            "cache_read_input_tokens": 4096,
            "cache_creation_input_tokens": 512,
        },
    }
    seen: list = []
    client = transport([(200, body)], seen)
    provider = AnthropicProvider(api_key="sk-ant-test-000000000", http_client=client)
    response = provider.complete(request(model="claude-sonnet-5-5"))
    assert response.usage == Usage(input=85, output=30, cache_read=4096, cache_write=512)
    assert response.message.text == "Je gèle."
    assert response.message.tool_calls == (ToolCall("tu1", "freeze", "{}"),)
    sent = json.loads(seen[0].content)
    assert sent["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert str(seen[0].url).endswith("/v1/messages")


def test_cost_formula_and_billing():
    usage = Usage(input=1_000_000, output=500_000, cache_read=2_000_000, cache_write=400_000)
    # 1 + 1 + 0.2 + 0.5 au tarif de test.
    assert cost_equiv_usd(usage, TEST_PRICE) == 2.7
    assert billed_usd(claude_model(), 2.7) == 0.0
    assert billed_usd(fake_model(), 2.7) == 2.7
    prices = load_pricing()
    # Constat 1-2 : 4126 × 0,435 + 45 × 0,87 = 1833,96 µ$ (Xiaomi).
    mimo = prices["xiaomi/mimo-v2.6-pro"]
    assert cost_equiv_usd(Usage(input=4126, output=45), mimo) == 0.001834
    sonnet = prices["claude-sonnet-5-5"]
    assert (sonnet.input, sonnet.output, sonnet.cache_read, sonnet.cache_write) == (
        2.0,
        10.0,
        0.10,
        2.50,
    )


def test_every_configured_model_has_a_dated_price():
    prices = load_pricing()
    for model in load_models().values():
        assert model.id in prices, model.name
        assert prices[model.id].date and prices[model.id].source
