"""Porte R4 (story 1-12, D7, P0, AC14)."""

from __future__ import annotations

import pytest

from nn_weight_writing.datasets.legal_r.gate import (
    dominant_family,
    family_of,
    family_shares,
    gate,
    leave_one_out,
    wilson,
)


def test_wilson_values():
    low, high = wilson(90, 300)
    assert (round(low, 4), round(high, 4)) == (0.2509, 0.3541)
    assert wilson(0, 10)[0] == 0.0 and round(wilson(0, 10)[1], 4) == 0.2775
    assert wilson(10, 10)[1] == pytest.approx(1.0) and round(wilson(10, 10)[0], 4) == 0.7225
    assert tuple(round(x, 4) for x in wilson(57, 60)) == (0.8630, 0.9829)
    with pytest.raises(ValueError):
        wilson(1, 0)
    with pytest.raises(ValueError):
        wilson(5, 4)


def test_decision_and_tight():
    at = gate(90, 210)
    assert (at.p, at.decision, at.tight, at.n, at.k) == (0.30, "comparatif", True, 300, 90)
    below = gate(89, 211)
    assert (below.decision, below.tight) == ("plafond", True)
    clear = gate(120, 180)
    assert (clear.p, clear.decision, clear.tight) == (0.4, "comparatif", False)
    far = gate(10, 290)
    assert (far.decision, far.tight) == ("plafond", False)


def test_zero_denominator():
    with pytest.raises(ValueError, match="Anaël"):
        gate(0, 0)


def test_leave_one_family_out():
    assert family_of("qwen3.5:0.8b") == "qwen3.5" and family_of("lfm3:1.7b-q4_K_M") == "lfm3"
    q, g, m = frozenset({"qwen3.5"}), frozenset({"gemma4"}), frozenset({"ministral-3"})
    both = frozenset({"qwen3.5", "gemma4"})
    units = [(True, q)] * 4 + [(False, g)] * 4 + [(False, m)] * 1 + [(True, both)] * 1
    shares = family_shares(units)
    assert shares == {"gemma4": 0.45, "ministral-3": 0.1, "qwen3.5": 0.45}
    loo = leave_one_out(units, ("qwen3.5", "gemma4", "ministral-3", "lfm3"))
    assert loo["qwen3.5"].p == pytest.approx(1 / 6)  # 1 incohérente sur 6
    assert loo["gemma4"].p == pytest.approx(5 / 6)
    assert loo["lfm3"].p == pytest.approx(0.5)
    reference = gate(5, 5)
    # Sans qwen3.5, p passe sous 30 % : famille dominante.
    assert dominant_family(reference, units) == "qwen3.5"
    balanced = [(True, q), (False, q), (True, g), (False, g), (True, m), (False, m)]
    assert dominant_family(gate(3, 3), balanced) is None
    assert dominant_family(gate(3, 1), [(True, q)] * 3 + [(False, g)]) == "qwen3.5"
