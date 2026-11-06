"""Gabarit canonique des références (story 1-9, D1)."""

from __future__ import annotations

import pytest

from nn_weight_writing.tasks.legal.reference import (
    Reference,
    format_reference,
    parse_reference,
)

EXAMPLES = [
    (
        Reference("cc", "ass. plén.", 17, 11, 2000, "99-13.701"),
        "Cass. ass. plén., 17 novembre 2000, n° 99-13.701",
    ),
    (Reference("ce", "5e ch.", 12, 3, 2019, "412345"), "CE, 5e ch., 12 mars 2019, n° 412345"),
    (
        Reference("ca", "Saint-Denis de la Réunion", 3, 6, 2021, "19/01234"),
        "CA Saint-Denis de la Réunion, 3 juin 2021, n° 19/01234",
    ),
]


@pytest.mark.parametrize(("ref", "text"), EXAMPLES)
def test_format_and_parse_round_trip(ref, text):
    assert format_reference(ref) == text
    assert parse_reference(text) == ref
    assert format_reference(parse_reference(text)) == text


def test_first_day_and_month_names():
    ref = Reference("cc", "soc.", 1, 8, 2015, "13-27.123")
    assert format_reference(ref) == "Cass. soc., 1er août 2015, n° 13-27.123"
    assert parse_reference("Cass. soc., 1er août 2015, n° 13-27.123").day == 1


@pytest.mark.parametrize(
    "raw",
    [
        "Cass. civ. 1re 12 mars 2015 n° 13-27.123",  # sans virgules
        "Cass. civ. 1re, 12 mars, n° 13-27.123",  # date à 2 jetons
        "TA Lyon, 12 mars 2015, n° 13/04567",  # en-tête inconnu
        "Cass. civ. 1re, 12 mars 2015, 13-27.123",  # sans « n° »
        "Cass. , 12 mars 2015, n° 13-27.123",  # formation vide
        "Cass. soc., 12 marz 2015, n° 13-27.123",  # mois inconnu
        "Cass. soc., 012 mars 2015, n° 13-27.123",  # zéro initial
    ],
)
def test_parse_refuses_non_canonical(raw):
    with pytest.raises(ValueError):
        parse_reference(raw)
