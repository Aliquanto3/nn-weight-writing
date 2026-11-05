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
    assert probe.parse_chat_usage(usage) == {
        "input": 4180,
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
    assert probe.main([]) == 0
    assert json.loads(capsys.readouterr().out)["error"] == "OPENROUTER_API_KEY absente"
