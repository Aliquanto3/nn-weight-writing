"""Porte R4 (story 1-12, D7 et P0) : part d'incohérentes, intervalle de Wilson, décision.

p = incohérentes / (incohérentes + cohérentes absentes) ; comparatif si p >= 0,30, plafond
sinon ; « serrée » si l'intervalle à 95 % contient 0,30. La porte se décide sur p_d1 (P0).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

THRESHOLD = 0.30
Z95 = 1.959963984540054
LOW_N = 100


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("intervalle de Wilson : effectif nul")
    if not 0 <= k <= n:
        raise ValueError("intervalle de Wilson : k hors de [0, n]")
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


@dataclass(frozen=True)
class GateResult:
    k: int  # incohérentes
    n: int  # dénominateur
    p: float
    low: float
    high: float
    decision: str  # "comparatif" ou "plafond"
    tight: bool

    @property
    def side(self) -> bool:
        return self.p >= THRESHOLD


def gate(incoherent: int, coherent_absent: int) -> GateResult:
    """R4 sur des effectifs ; `ValueError` si le dénominateur est nul (décision à Anaël)."""
    n = incoherent + coherent_absent
    if n == 0:
        raise ValueError("porte R4 : dénominateur nul, décision à Anaël")
    p = incoherent / n
    low, high = wilson(incoherent, n)
    return GateResult(
        k=incoherent,
        n=n,
        p=p,
        low=low,
        high=high,
        decision="comparatif" if p >= THRESHOLD else "plafond",
        tight=low <= THRESHOLD <= high,
    )


def maybe_gate(incoherent: int, coherent_absent: int) -> GateResult | None:
    return gate(incoherent, coherent_absent) if incoherent + coherent_absent else None


def family_of(model: str) -> str:
    """Famille d'un modèle : préfixe du nom avant `:` (`qwen3.5:2b` -> `qwen3.5`)."""
    return model.split(":", 1)[0]


def family_shares(units: Sequence[tuple[bool, frozenset[str]]]) -> dict[str, float]:
    """Part du dénominateur par famille ; une unité citée par k familles compte 1/k pour chacune."""
    totals: dict[str, float] = {}
    for _incoherent, families in units:
        for fam in families:
            totals[fam] = totals.get(fam, 0.0) + 1 / len(families)
    n = len(units)
    return {fam: value / n for fam, value in sorted(totals.items())} if n else {}


def leave_one_out(
    units: Sequence[tuple[bool, frozenset[str]]], families: Iterable[str] | None = None
) -> dict[str, GateResult | None]:
    """p sans les unités citées par cette seule famille, pour chaque famille."""
    names = sorted(families or {f for _, fams in units for f in fams})
    out: dict[str, GateResult | None] = {}
    for fam in names:
        kept = [inc for inc, fams in units if fams != frozenset({fam})]
        out[fam] = maybe_gate(sum(kept), len(kept) - sum(kept))
    return out


def dominant_family(
    reference: GateResult, units: Sequence[tuple[bool, frozenset[str]]]
) -> str | None:
    """Famille qui domine (part > 50 % ou p sans elle de l'autre côté de 30 %), sinon None."""
    for fam, share in family_shares(units).items():
        if share > 0.5:
            return fam
    for fam, result in leave_one_out(units).items():
        if result is not None and result.side != reference.side:
            return fam
    return None
