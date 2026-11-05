"""Configuration du protocole (D9) : un seul lecteur de `config/protocol.toml`."""

from __future__ import annotations

import hashlib

import pytest

from nn_weight_writing.config import PROTOCOL_PATH, load_protocol


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
