"""Configuration du protocole (D9) : un seul lecteur de `config/protocol.toml`."""

from __future__ import annotations

import hashlib

import pytest

from nn_weight_writing.config import PROTOCOL_PATH, load_models, load_pricing, load_protocol


def test_protocol_values():
    config = load_protocol()
    assert (
        config.pass_budget,
        config.turn_limit,
        config.exec_timeout_s,
        config.max_freeze_attempts,
        config.journal_schema_version,
    ) == (20, 200, 60.0, 3, 1)
    assert config.protocol_sha256 == hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()


@pytest.mark.parametrize("value", ["0", "-1", "true", '"20"'])
def test_invalid_values_refused(tmp_path, value):
    text = PROTOCOL_PATH.read_text("utf-8").replace("pass_budget = 20", f"pass_budget = {value}")
    path = tmp_path / "protocol.toml"
    path.write_text(text, "utf-8")
    with pytest.raises(ValueError, match="pass_budget"):
        load_protocol(path)


def test_budget_caps():
    config = load_protocol()
    assert (config.max_session_usd, config.project_cap_usd) == (5.0, 200.0)
    assert config.lot_caps_usd == {1: 100.0, 2: 75.0, 3: 25.0}
    assert config.lot_cap_usd(1) == 100.0


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("max_session_usd = 5.0", "max_session_usd = 0", "max_session_usd"),
        ("max_session_usd = 5.0", "max_session_usd = 30.0", "dépasse un plafond de lot"),
        ("project_cap_usd = 200.0", "project_cap_usd = 150.0", "somme des plafonds"),
        ("1 = 100.0", "un = 100.0", "lot_caps_usd"),
    ],
)
def test_invalid_budget_refused(tmp_path, old, new, message):
    path = tmp_path / "protocol.toml"
    path.write_text(PROTOCOL_PATH.read_text("utf-8").replace(old, new), "utf-8")
    with pytest.raises(ValueError, match=message):
        load_protocol(path)


def test_models_config():
    models = load_models()
    assert {name: (m.driver, m.provider, m.id) for name, m in models.items()} == {
        "sonnet-5.5": ("claude_code", "subscription", "claude-sonnet-5-5"),
        "fable-5.1": ("claude_code", "subscription", "claude-fable-5-1"),
        "mimo-v2.6-pro": ("api", "openrouter", "xiaomi/mimo-v2.6-pro"),
        "sonnet-5.5-api": ("api", "anthropic", "claude-sonnet-5-5"),
        "fable-5.1-api": ("api", "anthropic", "claude-fable-5-1"),
    }
    assert models["mimo-v2.6-pro"].provider_order == ("xiaomi",)
    assert not models["sonnet-5.5"].billed and models["sonnet-5.5-api"].billed


def test_models_config_rejects_claude_code_billed(tmp_path):
    path = tmp_path / "models.toml"
    path.write_text(
        '[models.x]\ndriver = "claude_code"\nprovider = "anthropic"\nid = "m"\n', "utf-8"
    )
    with pytest.raises(ValueError, match="claude_code va avec subscription"):
        load_models(path)


def test_pricing_requires_date_and_source(tmp_path):
    path = tmp_path / "pricing.toml"
    path.write_text("[models.m]\ninput = 1\noutput = 1\ncache_read = 0\ncache_write = 0\n", "utf-8")
    with pytest.raises(ValueError, match="date et source"):
        load_pricing(path)
    path.write_text("[models.m]\ninput = -1\noutput = 1\ncache_read = 0\ncache_write = 0\n")
    with pytest.raises(ValueError, match="input invalide"):
        load_pricing(path)
