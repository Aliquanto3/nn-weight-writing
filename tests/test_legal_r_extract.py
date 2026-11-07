"""Extracteur de références de la pré-étude R (story 1-12, D3, AC3)."""

from __future__ import annotations

import dataclasses

import pytest

from nn_weight_writing.datasets.legal_r.extract import ExtractedRef, extract_references

AC3 = (
    "Le préjudice de l'enfant né handicapé a été admis par l'arrêt Perruche (Cass. ass. plén., "
    "17 novembre 2000, n° 99-13.701). Voir aussi CE, 3e et 8e chambres réunies, 10 juillet 2020, "
    "req. n° 428409."
)


def _fields(ref: ExtractedRef) -> tuple:
    return (
        ref.jurisdiction,
        ref.formation_text,
        ref.seat_text,
        (ref.day, ref.month, ref.year),
        ref.number_text,
        ref.ecli,
    )


def test_two_references_one_response():
    refs = extract_references(AC3)
    assert [_fields(r) for r in refs] == [
        ("cc", "ass. plén.", None, (17, 11, 2000), "99-13.701", None),
        ("ce", "3e et 8e chambres réunies", None, (10, 7, 2020), "428409", None),
    ]
    first, second = refs
    assert AC3[first.start : first.end] == first.raw
    assert "99-13.701" in first.raw and "428409" in second.raw


def test_party_names_not_in_fields():
    text = AC3 + " Dans l'affaire Dupont c/ Martin, Cass. civ. 1re, 12 mars 2015, n° 13-27.123."
    for ref in extract_references(text):
        for field in dataclasses.fields(ref):
            value = getattr(ref, field.name)
            if field.name == "raw" or not isinstance(value, str):
                continue
            for name in ("Perruche", "Dupont", "Martin", "affaire"):
                assert name not in value, (field.name, value)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Cass. soc., 12 mars 2015, n° 13-27.123", (12, 3, 2015)),
        ("Cass. soc., 1er mars 2015, n° 13-27.123", (1, 3, 2015)),
        ("Cass. soc., 3 févr. 2015, n° 13-27.123", (3, 2, 2015)),
        ("Cass. soc., 3 sept. 2015, n° 13-27.123", (3, 9, 2015)),
        ("Cass. soc., 3 janv. 2015, n° 13-27.123", (3, 1, 2015)),
        ("Cass. soc., 12/03/2015, n° 13-27.123", (12, 3, 2015)),
        ("Cass. soc., 12.03.2015, n° 13-27.123", (12, 3, 2015)),
        ("Cass. soc., 2015-03-12, n° 13-27.123", (12, 3, 2015)),
        ("Cass. soc., 30 février 2015, n° 13-27.123", (30, 2, 2015)),
        ("Cass. soc., 14 Août 2015, n° 13-27.123", (14, 8, 2015)),
    ],
)
def test_date_forms(text, expected):
    (ref,) = extract_references(text)
    assert (ref.day, ref.month, ref.year) == expected


@pytest.mark.parametrize(
    ("text", "number"),
    [
        ("Cass. civ. 2e, 12 mars 2015, n° 13-27.123", "13-27.123"),
        ("Cass. civ. 2e, 12 mars 2015, nº 13-27.123", "13-27.123"),
        ("Cass. civ. 2e, 12 mars 2015, no 13-27.123", "13-27.123"),
        ("Cass. civ. 2e, 12 mars 2015, pourvoi n° 13 27.123", "13 27.123"),
        ("Cass. civ. 2e, 12 mars 2015, numéro de pourvoi : 13-27123", "13-27123"),
        ("Cass. civ. 2e, 12 mars 2015, 13-27.123", "13-27.123"),
        ("CA Lyon, 12 mars 2015, 13/04567", "13/04567"),
        ("CE, 10 juillet 2020, requête n° 428 409", "428 409"),
        ("CE, Ass., 20 oct. 1989, 108243", "108243"),
        ("CE, 10 juillet 2020, n° 428409 - 10 juillet 2020", "428409"),
    ],
)
def test_number_after_markers(text, number):
    refs = extract_references(text)
    assert refs[0].number_text == number
    # Une seconde date ouvre une seconde référence, sans numéro (D3).
    assert [r.number_text for r in refs[1:]] == [None] * (len(refs) - 1)


def test_short_or_normative_numbers_ignored():
    text = (
        "Cass. civ. 2e, 12 mars 2015, Bull. civ. II, n° 45, sur la loi n° 85-677 du "
        "5 juillet 1985 et le règlement (CE) n° 1393/2007 du 13 novembre 2007"
    )
    refs = extract_references(text)
    assert [_fields(r) for r in refs] == [("cc", "civ. 2e", None, (12, 3, 2015), None, None)]


def test_list_of_references_same_court():
    text = "Cass. civ. 1re, 3 mai 2000, n° 98-12.345 ; 5 juin 2001, n° 99-11.111."
    refs = extract_references(text)
    assert [_fields(r) for r in refs] == [
        ("cc", "civ. 1re", None, (3, 5, 2000), "98-12.345", None),
        ("cc", None, None, (5, 6, 2001), "99-11.111", None),
    ]


def test_structured_answer_over_lines_and_formation_before_court():
    text = (
        "**Juridiction** : Cour de cassation, chambre commerciale\n"
        "**Date** : 12 mars 2015\n**Numéro de pourvoi** : 13-27.123\n\n"
        "La première chambre civile de la Cour de cassation, le 1er mars 2016 (n° 14-11.111), "
        "a jugé."
    )
    refs = extract_references(text)
    assert [_fields(r) for r in refs] == [
        ("cc", "chambre commerciale", None, (12, 3, 2015), "13-27.123", None),
        ("cc", "première chambre civile", None, (1, 3, 2016), "14-11.111", None),
    ]


def test_ecli_alone_gives_jurisdiction():
    refs = extract_references(
        "Voir ECLI:FR:CECHR:2020:428409.20200710. Puis ecli:fr:ccass:2019:c200327."
    )
    assert [(r.jurisdiction, r.ecli, r.number_text) for r in refs] == [
        ("ce", "ECLI:FR:CECHR:2020:428409.20200710", None),
        ("cc", "ECLI:FR:CCASS:2019:C200327", None),
    ]


def test_ecli_after_reference_is_attached():
    (ref,) = extract_references(
        "Cass. civ. 2e, 14 mars 2019, n° 18-12.821, ECLI:FR:CCASS:2019:C200327"
    )
    assert _fields(ref) == (
        "cc",
        "civ. 2e",
        None,
        (14, 3, 2019),
        "18-12.821",
        "ECLI:FR:CCASS:2019:C200327",
    )


@pytest.mark.parametrize(
    "text",
    [
        "TA de Paris, 3 mai 2019, n° 1912345",
        "CAA de Lyon, 3 mai 2019, n° 19LY01234",
        "Conseil constitutionnel, 3 mai 2019, n° 2019-778",
        "Tribunal des conflits, 3 mai 2019, n° C4150",
        "CEDH, 3 mai 2019, n° 12345/15",
        "CJUE, 3 mai 2019, n° C-123/18",
        "tribunal judiciaire de Lille, 3 mai 2019, n° 19/01234",
    ],
)
def test_other_jurisdictions_flagged(text):
    refs = extract_references(text)
    assert refs and {r.jurisdiction for r in refs} == {"other"}


def test_number_without_court_opens_unknown_reference():
    (ref,) = extract_references("Un arrêt du 12 mars 2015 (pourvoi n° 13-27.123) a jugé.")
    assert (ref.jurisdiction, ref.number_text) == (None, "13-27.123")


def test_court_of_appeal_seat_and_other_forms():
    refs = extract_references(
        "CA Aix, 1re ch., 12 mars 2015, n° 13/04567 et cour d'appel de Lyon, 3 mai 2016, "
        "RG 15/01234"
    )
    assert [(r.jurisdiction, r.seat_text, r.number_text) for r in refs] == [
        ("ca", "Aix", "13/04567"),
        ("ca", "Lyon", "15/01234"),
    ]


def test_empty_and_no_reference():
    assert extract_references("") == []
    assert extract_references("La Cour de cassation a une jurisprudence constante.") == []


@pytest.mark.parametrize(
    ("text", "formation"),
    [
        ("Cass. soc. 12 mars 2015, n° 13-27.123", "soc."),
        ("Cass. Civ., 12 mars 2015, n° 13-27.123", "Civ."),
        ("Cass. chambre sociale 1er mars 2015, n° 13-27.123", "chambre sociale"),
        ("Cass. soc. 2, 12 mars 2015, n° 13-27.123", "soc. 2"),
    ],
)
def test_rank_never_taken_from_date(text, formation):
    (ref,) = extract_references(text)
    assert ref.formation_text == formation
    assert (ref.day, ref.month, ref.year) in {(12, 3, 2015), (1, 3, 2015)}
