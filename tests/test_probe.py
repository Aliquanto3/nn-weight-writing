import json
import zlib

from nn_weight_writing.providers import probe

MODELS = {
    "data": [
        {"id": "xiaomi/mimo-v2.6-flash", "pricing": {"prompt": "0.00000014"}},
        {
            "id": "xiaomi/mimo-v2.6-pro",
            "canonical_slug": "xiaomi/mimo-v2.6-pro-20260921",
            "context_length": 1050000,
            "architecture": {"input_modalities": ["text", "image"]},
            "pricing": {
                "prompt": "0.000000435",
                "completion": "0.00000087",
                "input_cache_read": "0.0000000036",
            },
            "supported_parameters": ["tools", "tool_choice", "temperature"],
            "endpoints": ["/api/v1/chat/completions", "/api/v1/messages"],
        },
    ]
}


def test_find_model_exact_id():
    assert probe.find_model(MODELS, "xiaomi/mimo-v2.6-pro")["context_length"] == 1050000
    assert probe.find_model(MODELS, "xiaomi/mimo-v2.6") is None
    assert probe.find_model({}, "x") is None


def test_summarize_model_prices_and_capabilities():
    s = probe.summarize_model(probe.find_model(MODELS, "xiaomi/mimo-v2.6-pro"))
    assert s["input_per_mtok_usd"] == 0.435
    assert s["output_per_mtok_usd"] == 0.87
    assert s["cache_read_per_mtok_usd"] == 0.0036
    assert s["cache_write_per_mtok_usd"] is None
    assert s["tools"] is True
    assert s["vision"] is True
    assert s["endpoints"] == ["/api/v1/chat/completions", "/api/v1/messages"]


def test_summarize_model_missing_fields():
    s = probe.summarize_model({"id": "m", "supported_parameters": ["tools"]})
    assert s["tools"] is False  # tool_choice absent
    assert s["vision"] is False
    assert s["input_per_mtok_usd"] is None
    assert s["endpoints"] == []


def test_parse_chat_usage_full():
    usage = {
        "prompt_tokens": 4180,
        "completion_tokens": 32,
        "prompt_tokens_details": {"cached_tokens": 4096, "cache_write_tokens": 7},
        "cost": 6.0573e-05,
    }
    # prompt_tokens inclut le cache : input = 4180 - 4096 lus - 7 écrits.
    assert probe.parse_chat_usage(usage) == {
        "input": 77,
        "output": 32,
        "cache_read": 4096,
        "cache_write": 7,
        "cost": 6.0573e-05,
    }


def test_parse_chat_usage_absent_fields():
    expected = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "cost": None}
    assert probe.parse_chat_usage(None) == expected
    assert probe.parse_chat_usage({"prompt_tokens_details": None}) == expected
    only = probe.parse_chat_usage({"prompt_tokens": 5, "completion_tokens": 2})
    assert only["input"] == 5 and only["cost"] is None


def test_parse_chat_usage_zero_cost_is_not_absent():
    assert probe.parse_chat_usage({"cost": 0})["cost"] == 0.0


def test_parse_messages_usage():
    usage = {
        "input_tokens": 85,
        "output_tokens": 27,
        "cache_read_input_tokens": 4096,
        "cache_creation_input_tokens": None,
        "cost": 5.7e-05,
    }
    assert probe.parse_messages_usage(usage) == {
        "input": 85,
        "output": 27,
        "cache_read": 4096,
        "cache_write": 0,
        "cost": 5.7e-05,
    }
    assert probe.parse_messages_usage({})["cost"] is None


def test_total_cost_skips_absent():
    usages = [{"cost": 0.001}, {"cost": None}, {"cost": 0.0025}]
    assert probe.total_cost(usages) == (0.0035, 1)
    assert probe.total_cost([]) == (0, 0)


def test_redact():
    assert probe.redact("a SECRET b SECRET", "SECRET") == "a [CLE] b [CLE]"
    assert probe.redact("rien", None) == "rien"


def test_make_png_is_valid_png():
    png = probe.make_png(2, 3)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert png[12:16] == b"IHDR"
    assert int.from_bytes(png[16:20], "big") == 2
    assert int.from_bytes(png[20:24], "big") == 3
    idat = png.index(b"IDAT")
    length = int.from_bytes(png[idat - 4 : idat], "big")
    raw = zlib.decompress(png[idat + 4 : idat + 4 + length])
    assert raw == (b"\x00" + b"\xff\x00\x00" * 2) * 3


def test_main_output_has_no_key(monkeypatch, capsys):
    fake_key = "sk-or-FAKEKEY-1234567890"
    monkeypatch.setenv(probe.KEY_VAR, fake_key)
    monkeypatch.setattr(probe, "_request", lambda path, body, key: MODELS)
    monkeypatch.setattr(
        probe, "run_paid_probe", lambda key: {"echo": f"fuite {key}", "total_billed_usd": 0.0}
    )
    assert probe.main([]) == 0
    out = capsys.readouterr().out
    assert fake_key not in out
    assert "[CLE]" in out
    assert json.loads(out.replace("[CLE]", "x"))["model"]["input_per_mtok_usd"] == 0.435


def test_main_models_only_makes_no_paid_call(monkeypatch, capsys):
    monkeypatch.delenv(probe.KEY_VAR, raising=False)
    monkeypatch.setattr(probe, "_request", lambda path, body, key: MODELS)

    def boom(key):
        raise AssertionError("appel payant")

    monkeypatch.setattr(probe, "run_paid_probe", boom)
    assert probe.main(["--models-only"]) == 0
    assert "probe" not in json.loads(capsys.readouterr().out)


def test_main_without_key_reports_error(monkeypatch, capsys):
    monkeypatch.delenv(probe.KEY_VAR, raising=False)
    monkeypatch.setattr(probe, "_request", lambda path, body, key: MODELS)
    assert probe.main([]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "OPENROUTER_API_KEY absente"


def test_main_models_failure_makes_no_paid_call(monkeypatch, capsys):
    monkeypatch.setenv(probe.KEY_VAR, "sk-or-x")
    err = {"_error": {"status": 503, "body": "indisponible"}}
    monkeypatch.setattr(probe, "_request", lambda path, body, key: err)

    def boom(key):
        raise AssertionError("appel payant")

    monkeypatch.setattr(probe, "run_paid_probe", boom)
    assert probe.main([]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["model"] is None and out["error"]["status"] == 503


def test_chat_and_messages_input_have_same_meaning():
    """Même requête vue par les deux API : ``input`` exclut le cache des deux côtés."""
    chat = probe.parse_chat_usage(
        {
            "prompt_tokens": 4181,
            "completion_tokens": 9,
            "prompt_tokens_details": {"cached_tokens": 4096},
        }
    )
    msgs = probe.parse_messages_usage(
        {"input_tokens": 85, "output_tokens": 9, "cache_read_input_tokens": 4096}
    )
    assert chat == msgs


def test_mentions_word():
    assert probe.mentions_word("La réponse est 42.", "42")
    assert not probe.mentions_word("1420", "42")
    assert probe.mentions_word("Rouge", "rouge", "red")
    assert not probe.mentions_word("one hundred", "rouge", "red")


class ScriptedOpenRouter:
    """Doublure de la frontière HTTP : réponses scriptées, requêtes enregistrées."""

    def __init__(self, tool_calls=True, tool_use=True, cost=0.001):
        self.calls = []
        self.tool_calls = tool_calls
        self.tool_use = tool_use
        self.cost = cost

    def __call__(self, path, body, key):
        self.calls.append((path, body))
        usage_chat = {"prompt_tokens": 10, "completion_tokens": 2, "cost": self.cost}
        if path == "/chat/completions":
            last = body["messages"][-1]
            if "tools" in body and last["role"] == "user" and self.tool_calls:
                call = {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "add", "arguments": '{"a": 17, "b": 25}'},
                }
                msg = {"role": "assistant", "content": None, "tool_calls": [call]}
            elif last["role"] == "tool":
                msg = {"role": "assistant", "content": "Le résultat est 42."}
            elif isinstance(last["content"], list):
                msg = {"role": "assistant", "content": "Rouge."}
            else:
                msg = {"role": "assistant", "content": "OK."}
            return {"provider": "Xiaomi", "choices": [{"message": msg}], "usage": usage_chat}
        assert path == "/messages"
        usage = {"input_tokens": 10, "output_tokens": 2, "cost": None}
        last = body["messages"][-1]
        if isinstance(last["content"], list):
            return {"content": [{"type": "text", "text": "42"}], "usage": usage}
        if not self.tool_use:
            return {"content": [{"type": "text", "text": "?"}], "usage": usage}
        block = {"type": "tool_use", "id": "t1", "name": "add", "input": {"a": 17, "b": 25}}
        return {"content": [block], "usage": usage}


def test_run_paid_probe_tool_loops_and_cost():
    fake = ScriptedOpenRouter()
    out = probe.run_paid_probe("sk-or-x", request=fake)
    assert [p for p, _ in fake.calls] == ["/chat/completions"] * 4 + ["/messages"] * 2
    # Le retour d'outil renvoyé au modèle porte la somme et l'identifiant de l'appel.
    tool_msg = fake.calls[2][1]["messages"][-1]
    assert tool_msg == {"role": "tool", "tool_call_id": "c1", "content": "42"}
    result = fake.calls[5][1]["messages"][-1]["content"][0]
    assert result == {"type": "tool_result", "tool_use_id": "t1", "content": "42"}
    assert out["chat_tool_step1"]["tool_called"] and out["chat_tool_step2"]["answer_has_42"]
    assert out["messages_tool_step2"]["answer_has_42"]
    assert out["chat_vision"]["answer_mentions_red"]
    assert out["chat_text"]["provider"] == "Xiaomi"
    assert out["paid_calls"] == 6
    assert out["total_billed_usd"] == 0.004  # 4 appels chat à 0,001 ; Messages sans coût
    assert out["calls_without_cost"] == 2
    assert out["budget_ok"] is True


def test_run_paid_probe_without_tool_call_stops_loops():
    fake = ScriptedOpenRouter(tool_calls=False, tool_use=False, cost=0.3)
    out = probe.run_paid_probe("sk-or-x", request=fake)
    assert len(fake.calls) == 4  # texte, outil sans appel, vision, Messages sans tool_use
    assert "chat_tool_step2" not in out and "messages_tool_step2" not in out
    assert out["chat_tool_step1"]["tool_called"] is False
    assert out["paid_calls"] == 4
    assert out["budget_ok"] is False  # 3 × 0,3 > 0,50


def test_run_paid_probe_http_error_keeps_going():
    def failing(path, body, key):
        return {"_error": {"status": 402, "body": "crédit insuffisant"}}

    out = probe.run_paid_probe("sk-or-x", request=failing)
    assert out["chat_text"]["error"]["status"] == 402
    assert out["calls_without_cost"] == out["paid_calls"] == 4


def test_request_network_error_becomes_error_entry(monkeypatch):
    def down(req, timeout):
        raise probe.urllib.error.URLError("hors ligne")

    monkeypatch.setattr(probe.urllib.request, "urlopen", down)
    out = probe._request("/chat/completions", {"x": 1}, "sk-or-x")
    assert out == {"_error": {"status": None, "body": "<urlopen error hors ligne>"}}
