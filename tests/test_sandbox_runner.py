"""Exécuteur du bac à sable : trame à nonce, profils A et B, délai, environnement (AD-5, D1, D5)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from nn_weight_writing.sandbox.runner import (
    FRAME_PREFIX,
    FrameError,
    _spawn,
    child_env,
    decode_weights,
    parse_frames,
    run,
)

NONCE = "ab" * 16


def frame(nonce: str, body: dict) -> bytes:
    return FRAME_PREFIX + nonce.encode() + b" " + json.dumps(body).encode()


def test_build_result_and_log():
    code = (
        "import numpy as np\nprint('bonjour')\n"
        "def build():\n    return {'L0.W': np.arange(6).reshape(2, 3), 'L0.b': [0.5, 1, 2]}\n"
    )
    result = run(code, "A", timeout_s=30)
    assert result.ok is True and result.error is None
    assert result.log == "bonjour\n"
    assert result.value["L0.W"].dtype == np.float32
    assert result.value["L0.W"].tolist() == [[0, 1, 2], [3, 4, 5]]
    assert result.value["L0.b"].tolist() == [0.5, 1.0, 2.0]


@pytest.mark.parametrize(
    ("code", "fragment"),
    [
        ("x = 1", "NameError: le script doit définir build()"),
        ("def build():\n    return 1 / 0", "ZeroDivisionError: division by zero (ligne 2)"),
        ("def build():\n    return [1]", "TypeError: build() doit renvoyer un dict"),
        ("import numpy as np\ndef build():\n    return {'L0.W': np.array([np.inf])}", "non finies"),
    ],
)
def test_build_errors(code, fragment):
    result = run(code, "A", timeout_s=30)
    assert result.ok is False
    assert fragment in result.error


def test_bad_weight_key_rejected_by_parent():
    code = "def build():\n    return {'poids': [1.0]}"
    result = run(code, "A", timeout_s=30)
    assert result.ok is False
    assert result.error.startswith("résultat invalide : clé de poids invalide")


def test_rules_reexecuted_in_fresh_namespace_per_example():
    code = "seen = []\ndef predict(raw):\n    seen.append(raw)\n    return len(seen)\n"
    result = run(code, "B", {"examples": ["a", "b", "c"]}, timeout_s=30)
    assert result.ok is True
    assert result.value == [{"label": 1}, {"label": 1}, {"label": 1}]


def test_module_namespaces_are_fresh_per_example_even_without_filter():
    code = (
        "import re\ndef predict(raw):\n    try:\n        re.memo.append(raw)\n"
        "    except AttributeError:\n        re.memo = [raw]\n    return len(re.memo)\n"
    )
    result = _spawn(code, "B", {"examples": ["a", "b"]}, 30)
    assert result.value == [{"label": 1}, {"label": 1}]


def test_rules_per_example_errors_and_label_types():
    code = (
        "def predict(raw):\n    if raw == 'liste':\n        return [1]\n"
        "    if raw == 'zero':\n        return 1 / 0\n    return raw.upper()\n"
    )
    result = run(code, "B", {"examples": ["ok", "liste", "zero"]}, timeout_s=30)
    assert result.ok is False
    assert result.value[0] == {"label": "OK"}
    assert result.value[1]["error"].startswith("TypeError: label de type non admis : list")
    assert result.value[2]["error"].startswith("ZeroDivisionError")


def test_timeout():
    result = run("while True:\n    pass\n", "B", {"examples": ["a"]}, timeout_s=2)
    assert result.ok is False
    assert result.error == "timeout (2 s)"


def test_child_env_has_no_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    assert set(child_env()) <= {"SYSTEMROOT", "PATH"}


def test_parse_frames_accepts_single_frame_among_noise():
    stdout = b"bruit\n" + frame(NONCE, {"ok": True, "value": 1}) + b"\nautre\n"
    assert parse_frames(stdout, NONCE) == {"ok": True, "value": 1}


@pytest.mark.parametrize(
    ("stdout", "message"),
    [
        (b"rien\n", "aucune trame"),
        (frame("cd" * 16, {"ok": True}), "mauvais nonce"),
        (frame(NONCE, {"ok": True}) + b"\n" + frame(NONCE, {"ok": True}), "en double"),
        (frame(NONCE, {"ok": True}) + b"\n" + frame("00" * 16, {"ok": False}), "mauvais nonce"),
        (FRAME_PREFIX + NONCE.encode() + b" {pas du json", "JSON illisible"),
        (frame(NONCE, {"ok": "oui"}), "mal formée"),
    ],
)
def test_parse_frames_rejects(stdout, message):
    with pytest.raises(FrameError, match=message):
        parse_frames(stdout, NONCE)


@pytest.mark.parametrize(
    "value",
    [
        {"L0.X": {"shape": [1], "dtype": "float32", "data": [1.0]}},
        {"L0.W": {"shape": [1], "dtype": "float64", "data": [1.0]}},
        {"L0.W": {"shape": [2], "dtype": "float32", "data": [1.0]}},
        {"L0.W": {"shape": [1], "dtype": "float32", "data": ["1"]}},
        {"L0.W": {"shape": [-1], "dtype": "float32", "data": []}},
        {"L0.W": {"shape": [1], "dtype": "float32", "data": [1.0], "extra": 1}},
        {},
    ],
)
def test_decode_weights_validates_keys_shape_dtype(value):
    with pytest.raises(FrameError):
        decode_weights(value)
