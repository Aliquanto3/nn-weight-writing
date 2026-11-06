"""Encodeurs fixes de S : `legal.chars@1` (réseau C), `legal.fields@2` (réseau F), D5.

`legal.fields@1` (champs en scalaires normalisés) reste lisible pour les runs gelés de 1-11 qui
le portent ; F l'a remplacé par `@2` (champs en one-hot, revue de 1-11).
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np

from nn_weight_writing.tasks.legal.reference import MONTHS, NUMBER_SIGN

ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789 .,-/éèêàâîôûç"
N_SYMBOLS = len(ALPHABET) + 1  # 50 symboles de l'alphabet, plus « autre » (indice 50)
OTHER = len(ALPHABET)
# (nom, première position, longueur)
SLOTS = (("header", 0, 32), ("day", 32, 3), ("month", 35, 9), ("year", 44, 4), ("number", 48, 12))
N_POSITIONS = 60
N_CHARS = N_POSITIONS * N_SYMBOLS  # 3 060
N_FIELDS = 32 * N_SYMBOLS + 12 * N_SYMBOLS + 5  # 2 249
YEAR_LOW, YEAR_SPAN = 1980, 50
# `legal.fields@2` : années 1980 à 2039 en one-hot (décisions 2001-2029, AA des numéros 1986-2032).
YEARS = tuple(range(1980, 2040))
_V2_DAY = (32 + 12) * N_SYMBOLS  # 2 244 : jour 1 à 31
_V2_MONTH = _V2_DAY + 31  # 2 275 : mois 1 à 12
_V2_YEAR = _V2_MONTH + 12  # 2 287 : année de la décision
_V2_HAS_AA = _V2_YEAR + len(YEARS)  # 2 347 : le numéro commence par AA- ou AA/
_V2_AA_YEAR = _V2_HAS_AA + 1  # 2 348 : année AA du numéro
N_FIELDS_V2 = _V2_AA_YEAR + len(YEARS)  # 2 408
_NUMBER_YEAR = re.compile(r"^(\d{2})[-/]")


def _split(raw: object) -> tuple[str, list[str], str]:
    """En-tête, jetons de date et numéro d'une référence en minuscules NFC."""
    if not isinstance(raw, str):
        raise TypeError("l'exemple brut doit être une chaîne")
    text = unicodedata.normalize("NFC", raw).lower()
    parts = text.rsplit(", ", 2)
    if len(parts) != 3 or not parts[2].startswith(NUMBER_SIGN):
        raise ValueError(f"référence hors gabarit : {raw!r}")
    tokens = parts[1].split(" ")
    if len(tokens) != 3:
        raise ValueError(f"date hors gabarit : {raw!r}")
    return parts[0], tokens, parts[2][len(NUMBER_SIGN) :]


def _put(x: np.ndarray, text: str, first: int, length: int) -> None:
    for offset, char in enumerate(text[:length]):
        symbol = ALPHABET.find(char)
        x[N_SYMBOLS * (first + offset) + (symbol if symbol >= 0 else OTHER)] = 1.0


def encode_chars(raw: object) -> np.ndarray:
    header, (day, month, year), number = _split(raw)
    x = np.zeros(N_CHARS, dtype=np.float32)
    for text, (_, first, length) in zip((header, day, month, year, number), SLOTS, strict=True):
        _put(x, text, first, length)
    return x


def _year_value(year: int) -> float:
    return float(min(max((year - YEAR_LOW) / YEAR_SPAN, 0.0), 1.0))


def encode_fields(raw: object) -> np.ndarray:
    header, (day_token, month_token, year_token), number = _split(raw)
    x = np.zeros(N_FIELDS, dtype=np.float32)
    _put(x, header, 0, 32)
    # Le numéro occupe les positions 32 à 43 de ce vecteur : 12 positions de caractères.
    _put(x, number, 32, 12)
    base = (32 + 12) * N_SYMBOLS
    day = 1 if day_token == "1er" else int(day_token) if day_token.isdecimal() else 0
    x[base] = day / 31
    x[base + 1] = (MONTHS.index(month_token) + 1) / 12 if month_token in MONTHS else 0.0
    x[base + 2] = _year_value(int(year_token)) if year_token.isdecimal() else 0.0
    match = _NUMBER_YEAR.match(number)
    x[base + 3] = 1.0 if match else 0.0
    if match:
        aa = int(match.group(1))
        x[base + 4] = _year_value(1900 + aa if aa >= 50 else 2000 + aa)
    return x


def _one_hot(x: np.ndarray, base: int, index: int, size: int) -> None:
    if 0 <= index < size:
        x[base + index] = 1.0


def _aa_year(number: str) -> int | None:
    match = _NUMBER_YEAR.match(number)
    if not match:
        return None
    aa = int(match.group(1))
    return 1900 + aa if aa >= 50 else 2000 + aa


def encode_fields_v2(raw: object) -> np.ndarray:
    """`legal.fields@2` : mêmes champs extraits que `@1`, jour, mois et années en one-hot.

    Aucun drapeau calculé (date valide, bissextile, écart) : seulement la représentation des
    champs que C lit en caractères. Valeur illisible ou hors plage : groupe tout à 0.
    """
    header, (day_token, month_token, year_token), number = _split(raw)
    x = np.zeros(N_FIELDS_V2, dtype=np.float32)
    _put(x, header, 0, 32)
    _put(x, number, 32, 12)
    day = 1 if day_token == "1er" else int(day_token) if day_token.isdecimal() else 0
    _one_hot(x, _V2_DAY, day - 1, 31)
    if month_token in MONTHS:
        _one_hot(x, _V2_MONTH, MONTHS.index(month_token), 12)
    if year_token.isdecimal():
        _one_hot(x, _V2_YEAR, int(year_token) - YEARS[0], len(YEARS))
    aa_year = _aa_year(number)
    if aa_year is not None:
        x[_V2_HAS_AA] = 1.0
        _one_hot(x, _V2_AA_YEAR, aa_year - YEARS[0], len(YEARS))
    return x
