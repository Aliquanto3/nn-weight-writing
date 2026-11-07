"""Vérificateur de règles de S (D4) : écrit d'après la colonne « Règle » de D2 seule.

`violations(ref)` renvoie les types `tXX` violés ; une vraie référence en viole aucun, une fausse
exactement le sien. Indépendant du code qui altère (`datasets/legal.py`).
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from nn_weight_writing.tasks.legal.facts import Facts, load_facts
from nn_weight_writing.tasks.legal.reference import Reference

_CE_NUMBERED = re.compile(r"(\d+)(re|e) (ch|sous-sect)\.")
MAX_DAY = {2: 29, 4: 30, 6: 30, 9: 30, 11: 30}


def easter(year: int) -> date:
    """Dimanche de Pâques, comput grégorien (algorithme d'Oudin)."""
    g = year % 19
    c = year // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - (h // 28) * (1 - (h // 28) * (29 // (h + 1)) * ((21 - g) // 11))
    j = (year + year // 4 + i + 2 - c + c // 4) % 7
    offset = i - j
    month = 3 + (offset + 40) // 44
    day = offset + 28 - 31 * (month // 4)
    return date(year, month, day)


def legal_holidays(year: int, facts: Facts | None = None) -> dict[date, str]:
    """Les onze fêtes légales de l'année : date -> nom (fixes `MM-DD`, mobiles par nom)."""
    facts = facts or load_facts()
    out = {date(year, m, d): f"{m:02d}-{d:02d}" for m, d in facts.holiday_fixed}
    sunday = easter(year)
    for name, offset in facts.easter_offsets.items():
        out[sunday + timedelta(days=offset)] = name
    return out


def is_working_day(day: date, facts: Facts | None = None) -> bool:
    """Lundi à vendredi hors fêtes légales, Vendredi saint et 26 décembre (D4)."""
    facts = facts or load_facts()
    if day.weekday() >= 5 or day in legal_holidays(day.year, facts):
        return False
    if day == easter(day.year) + timedelta(days=facts.good_friday_offset):
        return False
    return (day.month, day.day) not in facts.local_fixed


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _valid_date(ref: Reference) -> date | None:
    try:
        return date(ref.year, ref.month, ref.day)
    except ValueError:
        return None


def ce_lexicon(formation: str, facts: Facts) -> str | None:
    """`assembly`, `section`, `ch`, `sous-sect`, `x` (rang hors de [1, 10]) ou None."""
    if formation == facts.ce_assembly:
        return "assembly"
    if formation == facts.ce_section:
        return "section"
    match = _CE_NUMBERED.fullmatch(formation)
    if not match:
        return None
    digits, suffix, kind = match.groups()
    rank = int(digits)
    well_formed = digits == str(rank) and suffix == ("re" if rank == 1 else "e")
    if not (1 <= rank <= facts.ce_numbered_max and well_formed):
        return "x"
    return kind


def number_jurisdictions(number: str, facts: Facts) -> set[str]:
    out = set()
    for jurisdiction, pattern in (
        ("cc", facts.cc_pattern),
        ("ce", facts.ce_pattern),
        ("ca", facts.ca_pattern),
    ):
        if re.fullmatch(pattern, number):
            out.add(jurisdiction)
    return out


def number_year(number: str, decision_year: int) -> int:
    """Année d'un AA : l'unique Y' = AA (mod 100) dans [Y - 50, Y + 49]."""
    aa = int(number[:2])
    return decision_year - 50 + (aa - (decision_year - 50)) % 100


def violations(ref: Reference, facts: Facts | None = None) -> frozenset[str]:
    facts = facts or load_facts()
    found: set[str] = set()
    triplet = (ref.year, ref.month, ref.day)
    real_date = _valid_date(ref)
    kinds = number_jurisdictions(ref.number, facts)

    # Date
    if ref.day > MAX_DAY.get(ref.month, 31):
        found.add("t02")
    if triplet > (facts.corpus_date.year, facts.corpus_date.month, facts.corpus_date.day):
        found.add("t06")
    if ref.month == 2 and ref.day == 29 and not is_leap(ref.year):
        found.add("t15")
    if real_date is not None and (
        real_date.weekday() == 6 or real_date in legal_holidays(real_date.year, facts)
    ):
        found.add("t12")

    # Numéro
    if not kinds:
        found.add("t10")
    elif ref.jurisdiction not in kinds:
        found.add("t11")

    if ref.jurisdiction == "cc":
        lexicon = ce_lexicon(ref.formation, facts)
        if ref.formation not in facts.chambers:
            found.add("t05" if lexicon in {"assembly", "section", "ch", "sous-sect"} else "t03")
        if "cc" in kinds:
            decision = ref.year
            appeal = number_year(ref.number, decision)
            if appeal > decision:
                found.add("t01")
            if decision - appeal >= facts.cc_old_gap[0]:
                found.add("t08")
            order = int(ref.number[3:5] + ref.number[6:])
            if ref.formation in facts.civil and order >= facts.criminal_series_min:
                found.add("t14")
            if ref.formation in facts.criminal and order < facts.criminal_series_min:
                found.add("t14")
    elif ref.jurisdiction == "ce":
        lexicon = ce_lexicon(ref.formation, facts)
        if ref.formation in facts.chambers:
            found.add("t05")
        elif lexicon is None or lexicon == "x":
            found.add("x_formation")
        first_chamber = facts.subsection_until + timedelta(days=1)
        last_subsection = facts.chamber_from - timedelta(days=1)
        if lexicon == "ch" and triplet < (
            first_chamber.year,
            first_chamber.month,
            first_chamber.day,
        ):
            found.add("t07")
        if lexicon == "sous-sect" and triplet > (
            last_subsection.year,
            last_subsection.month,
            last_subsection.day,
        ):
            found.add("t07")
    elif ref.jurisdiction == "ca":
        if ref.formation not in facts.all_seats:
            found.add("t04")
        if "ca" in kinds:
            decision = ref.year
            appeal = number_year(ref.number, decision)
            if appeal > decision:
                found.add("t09")
            if decision - appeal >= facts.ca_old_gap[0]:
                found.add("t13")
    return frozenset(found)
