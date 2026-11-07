"""Chargeur de `r_facts.toml` : faits propres à R (story 1-12, D2 et D4).

Même format que `facts.toml` (chaque section porte `status` et `source`). Le chargeur refuse une
section `unverified`. `facts.toml` n'est pas modifié (son empreinte fixe la version de S).
"""

from __future__ import annotations

import hashlib
import tomllib
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from pathlib import Path

R_FACTS_PATH = Path(__file__).with_name("r_facts.toml")
SECTIONS = ("seats", "ecli", "coverage", "disabled_rules", "recall")


def fold(text: str) -> str:
    """Minuscules, sans accents, tirets et apostrophes en espaces, espaces simples."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    for ch in "-'’_":
        text = text.replace(ch, " ")
    return " ".join(text.split())


@dataclass(frozen=True)
class RFacts:
    """Faits de R. Les valeurs par défaut ne servent qu'aux tests (aucune règle mesurée)."""

    seat_aliases: dict[str, str] = field(default_factory=dict)  # forme pliée -> siège
    location_codes: dict[str, str] = field(default_factory=dict)  # code Judilibre -> siège
    ecli_codes: dict[str, frozenset[str]] = field(default_factory=dict)  # juridiction -> codes
    cc_prefixes: dict[str, frozenset[str]] = field(default_factory=dict)  # chambre -> préfixes
    disabled_rules: dict[str, frozenset[str]] = field(default_factory=dict)
    coverage: dict[str, tuple[date, date]] = field(default_factory=dict)
    recall_reliable: dict[str, bool] = field(default_factory=dict)

    def disabled(self, jurisdiction: str | None) -> frozenset[str]:
        return self.disabled_rules.get(jurisdiction or "", frozenset())


def _section(data: dict, name: str) -> dict:
    if name not in data or not isinstance(data[name], dict):
        raise ValueError(f"r_facts.toml : section absente : {name}")
    node = data[name]
    if node.get("status") == "unverified":
        raise ValueError(f"r_facts.toml : section non vérifiée, refusée : {name}")
    if "status" not in node or "source" not in node:
        raise ValueError(f"r_facts.toml : section sans status ou source : {name}")
    return node


def _seats(data: dict) -> tuple[dict[str, str], dict[str, str]]:
    seats = _section(data, "seats")
    aliases = {fold(k): v for k, v in seats.get("aliases", {}).items()}
    return aliases, dict(seats.get("location_codes", {}))


def parse_r_facts(data: dict) -> RFacts:
    for name in data:
        if isinstance(data[name], dict) and data[name].get("status") == "unverified":
            raise ValueError(f"r_facts.toml : section non vérifiée, refusée : {name}")
    aliases, codes = _seats(data)
    ecli = _section(data, "ecli")
    coverage = _section(data, "coverage")
    disabled = _section(data, "disabled_rules")
    recall = _section(data, "recall")
    adopted = ecli.get("adopted", {})
    ecli_codes = (
        {j: frozenset(v) for j, v in ecli.get("codes", {}).items()} if adopted.get("R-E2") else {}
    )
    cc_prefixes = (
        {c: frozenset(v) for c, v in ecli.get("cc_prefixes", {}).items()}
        if adopted.get("R-E5")
        else {}
    )
    disabled_rules = {
        j: frozenset(v)
        for j, v in disabled.items()
        if isinstance(v, dict) and j in {"cc", "ce", "ca"}
    }
    if not adopted.get("R-E4"):
        disabled_rules["ce"] = disabled_rules.get("ce", frozenset()) | {"R-E4"}
    for rule in ("R-E2", "R-E5"):
        if not adopted.get(rule):
            for j in ("cc", "ce", "ca"):
                disabled_rules[j] = disabled_rules.get(j, frozenset()) | {rule}
    windows = {
        j: (date.fromisoformat(w["start"]), date.fromisoformat(w["end"]))
        for j, w in coverage.items()
        if isinstance(w, dict)
    }
    reliable = {j: bool(v["reliable"]) for j, v in recall.items() if isinstance(v, dict)}
    return RFacts(
        seat_aliases=aliases,
        location_codes=codes,
        ecli_codes=ecli_codes,
        cc_prefixes=cc_prefixes,
        disabled_rules=disabled_rules,
        coverage=windows,
        recall_reliable=reliable,
    )


@cache
def _default() -> RFacts:
    with R_FACTS_PATH.open("rb") as handle:
        return parse_r_facts(tomllib.load(handle))


def load_r_facts(path: Path | None = None) -> RFacts:
    """Lit `r_facts.toml` ; refuse une section `unverified` (`ValueError`)."""
    if path is None:
        return _default()
    with Path(path).open("rb") as handle:
        return parse_r_facts(tomllib.load(handle))


@cache
def load_seat_tables() -> tuple[dict[str, str], dict[str, str]]:
    """Alias et codes des sièges seuls (section `seats`, primaire), pour le normaliseur."""
    with R_FACTS_PATH.open("rb") as handle:
        return _seats(tomllib.load(handle))


def r_facts_sha256(path: Path | None = None) -> str:
    """sha256 des octets de `r_facts.toml` (porté par le classement, `versions`)."""
    return hashlib.sha256(Path(path or R_FACTS_PATH).read_bytes()).hexdigest()
