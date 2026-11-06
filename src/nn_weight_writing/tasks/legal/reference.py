"""Référence de décision : gabarit canonique de D1, écriture et lecture."""

from __future__ import annotations

import re
from dataclasses import dataclass

MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)
NUMBER_SIGN = "n° "
_DAY = re.compile(r"[1-9]\d?")
_YEAR = re.compile(r"\d{4}")


@dataclass(frozen=True)
class Reference:
    """`jurisdiction` : `cc`, `ce` ou `ca` ; `formation` : chambre, formation ou siège."""

    jurisdiction: str
    formation: str
    day: int
    month: int  # 1 à 12
    year: int
    number: str


def format_date(day: int, month: int, year: int) -> str:
    return f"{'1er' if day == 1 else day} {MONTHS[month - 1]} {year:04d}"


def format_reference(ref: Reference) -> str:
    date_text = format_date(ref.day, ref.month, ref.year)
    if ref.jurisdiction == "cc":
        head = f"Cass. {ref.formation}"
    elif ref.jurisdiction == "ce":
        head = f"CE, {ref.formation}"
    elif ref.jurisdiction == "ca":
        head = f"CA {ref.formation}"
    else:
        raise ValueError(f"juridiction inconnue : {ref.jurisdiction!r}")
    return f"{head}, {date_text}, {NUMBER_SIGN}{ref.number}"


def parse_reference(raw: str) -> Reference:
    """Lit une chaîne du gabarit de D1 ; `ValueError` hors gabarit."""
    if not isinstance(raw, str):
        raise ValueError("référence : chaîne attendue")
    parts = raw.rsplit(", ", 2)
    if len(parts) != 3:
        raise ValueError(f"référence hors gabarit : {raw!r}")
    head, date_text, number_text = parts
    if not number_text.startswith(NUMBER_SIGN) or len(number_text) == len(NUMBER_SIGN):
        raise ValueError(f"numéro hors gabarit : {raw!r}")
    number = number_text[len(NUMBER_SIGN) :]
    if head.startswith("Cass. "):
        jurisdiction, formation = "cc", head[len("Cass. ") :]
    elif head.startswith("CE, "):
        jurisdiction, formation = "ce", head[len("CE, ") :]
    elif head.startswith("CA "):
        jurisdiction, formation = "ca", head[len("CA ") :]
    else:
        raise ValueError(f"en-tête hors gabarit : {head!r}")
    if not formation:
        raise ValueError(f"formation absente : {raw!r}")
    tokens = date_text.split(" ")
    if len(tokens) != 3:
        raise ValueError(f"date hors gabarit : {date_text!r}")
    day_token, month_token, year_token = tokens
    if day_token == "1er":
        day = 1
    elif _DAY.fullmatch(day_token):
        day = int(day_token)
    else:
        raise ValueError(f"jour hors gabarit : {day_token!r}")
    if month_token not in MONTHS or not _YEAR.fullmatch(year_token):
        raise ValueError(f"date hors gabarit : {date_text!r}")
    return Reference(
        jurisdiction, formation, day, MONTHS.index(month_token) + 1, int(year_token), number
    )
