"""Chargeur de `facts.toml` : les faits juridiques du générateur de S (story 1-9, D3)."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path

FACTS_PATH = Path(__file__).with_name("facts.toml")


def _day(text: str) -> date:
    return date.fromisoformat(text)


def _md(text: str) -> tuple[int, int]:
    month, day = text.split("-")
    return int(month), int(day)


@dataclass(frozen=True)
class Facts:
    # dates
    window_start: date
    window_end: date
    corpus_date: date
    future_start: date
    future_end: date
    # fêtes
    holiday_fixed: tuple[tuple[int, int], ...]
    easter_offsets: dict[str, int]
    good_friday_offset: int
    local_fixed: tuple[tuple[int, int], ...]
    t12_excluded: tuple[str, ...]
    # Cour de cassation
    chambers: dict[str, str]
    civil: tuple[str, ...]
    criminal: tuple[str, ...]
    series_exempt: tuple[str, ...]
    nonexistent: tuple[str, ...]
    cc_pattern: str
    criminal_series_min: int
    chamber_weights: dict[str, float]
    cc_gap_weights: tuple[float, ...]
    civil_serial: tuple[int, int]
    criminal_serial: tuple[int, int]
    cc_old_gap: tuple[int, int]
    cc_after_gap: tuple[int, int]
    # Conseil d'État
    ce_assembly: str
    ce_section: str
    ce_numbered_max: int
    subsection_until: date
    chamber_from: date
    ce_pattern: str
    ce_formation_weights: dict[str, float]
    ce_number_range: tuple[int, int]
    # cours d'appel
    all_seats: tuple[str, ...]
    seats_excluded_from_real: tuple[str, ...]
    fake_seats: tuple[str, ...]
    ca_pattern: str
    ca_gap_weights: tuple[float, ...]
    ca_serial: tuple[int, int]
    ca_old_gap: tuple[int, int]
    ca_after_gap: tuple[int, int]


def _section(data: dict, path: str) -> dict:
    node = data
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise ValueError(f"facts.toml : section absente : {path}")
        node = node[part]
    if node.get("status") == "unverified":
        raise ValueError(f"facts.toml : section non vérifiée, refusée : {path}")
    return node


def _pair(values: list) -> tuple[int, int]:
    return int(values[0]), int(values[1])


def parse_facts(data: dict) -> Facts:
    dates = _section(data, "dates")
    holidays = _section(data, "holidays")
    cc = _section(data, "cassation")
    cc_number = _section(data, "cassation.number")
    cc_gen = _section(data, "cassation.generator")
    ce = _section(data, "conseil_etat")
    ce_number = _section(data, "conseil_etat.number")
    ce_gen = _section(data, "conseil_etat.generator")
    ca = _section(data, "cours_appel")
    fake = _section(data, "cours_appel.fake_seats")
    ca_number = _section(data, "cours_appel.number")
    ca_gen = _section(data, "cours_appel.generator")
    return Facts(
        window_start=_day(dates["window_start"]),
        window_end=_day(dates["window_end"]),
        corpus_date=_day(dates["corpus_date"]),
        future_start=_day(dates["future_start"]),
        future_end=_day(dates["future_end"]),
        holiday_fixed=tuple(_md(t) for t in holidays["fixed"]),
        easter_offsets=dict(holidays["easter_offsets"]),
        good_friday_offset=int(holidays["local_excluded"]["good_friday"]),
        local_fixed=tuple(_md(t) for t in holidays["local_excluded"]["fixed"]),
        t12_excluded=tuple(holidays["t12_excluded"]),
        chambers=dict(cc["chambers"]),
        civil=tuple(cc["civil"]),
        criminal=tuple(cc["criminal"]),
        series_exempt=tuple(cc["series_exempt"]),
        nonexistent=tuple(cc["nonexistent"]),
        cc_pattern=cc_number["pattern"],
        criminal_series_min=int(cc_number["criminal_series_min"]),
        chamber_weights=dict(cc_gen["chamber_weights"]),
        cc_gap_weights=tuple(cc_gen["gap_weights"]),
        civil_serial=_pair(cc_gen["civil_serial"]),
        criminal_serial=_pair(cc_gen["criminal_serial"]),
        cc_old_gap=(int(cc_gen["old_gap_min"]), int(cc_gen["old_gap_max"])),
        cc_after_gap=_pair(cc_gen["after_gap"]),
        ce_assembly=ce["assembly"],
        ce_section=ce["section"],
        ce_numbered_max=int(ce["numbered_max"]),
        subsection_until=_day(ce["subsection_until"]),
        chamber_from=_day(ce["chamber_from"]),
        ce_pattern=ce_number["pattern"],
        ce_formation_weights=dict(ce_gen["formation_weights"]),
        ce_number_range=_pair(ce_gen["number_range"]),
        all_seats=tuple(ca["all_seats"]),
        seats_excluded_from_real=tuple(ca["excluded_from_real"]),
        fake_seats=tuple(fake["seats"]),
        ca_pattern=ca_number["pattern"],
        ca_gap_weights=tuple(ca_gen["gap_weights"]),
        ca_serial=_pair(ca_gen["serial"]),
        ca_old_gap=(int(ca_gen["old_gap_min"]), int(ca_gen["old_gap_max"])),
        ca_after_gap=_pair(ca_gen["after_gap"]),
    )


@cache
def _default_facts() -> Facts:
    with FACTS_PATH.open("rb") as handle:
        return parse_facts(tomllib.load(handle))


def load_facts(path: Path | None = None) -> Facts:
    """Lit `facts.toml` ; refuse une section `unverified` lue par le code (`ValueError`)."""
    if path is None:
        return _default_facts()
    with Path(path).open("rb") as handle:
        return parse_facts(tomllib.load(handle))


def facts_sha256() -> str:
    """sha256 des octets de `facts.toml` (porté par `dataset.json`)."""
    return hashlib.sha256(FACTS_PATH.read_bytes()).hexdigest()
