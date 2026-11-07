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


def test_bare_ce_number_needs_citation_separators():
    """E3 : le numéro nu du CE suit une virgule ; un montant ou un effectif n'en est pas un."""
    (amount,) = extract_references(
        "Le Conseil d'État (CE, 12 mars 2019) a jugé, dans une affaire portant sur "
        "250000 euros, que la décision était légale."
    )
    assert amount.number_text is None
    (lebon,) = extract_references("CE, Sect., 3 mars 2004, Ministre c/ X, 241151.")
    assert lebon.number_text == "241151"


# --- Tour de correction de la phase B (E15) : formes écrites à la main, aucune réponse copiée ---


def test_jurisdiction_inherited_from_header_line():
    """Juridiction dans l'introduction (ligne finie par « : ») puis bloc « Arrêt n° / Date »."""
    text = (
        "Voici un arrêt important de la Cour de cassation sur ce point :\n\n"
        "Arrêt n° 11-22.333\nDate : 14 mars 2013\nChambre sociale\nPourvoi n° 11-22.333\n"
    )
    (ref,) = extract_references(text)
    assert _fields(ref) == ("cc", "Chambre sociale", None, (14, 3, 2013), "11-22.333", None)
    assert text[ref.start : ref.end] == ref.raw and ref.raw.startswith("11-22.333")


def test_jurisdiction_inherited_from_title():
    text = "# Décision du Conseil d'État\n\nDate : 15 mars 2020\nNuméro de requête : 412345\n"
    (ref,) = extract_references(text)
    assert _fields(ref) == ("ce", None, None, (15, 3, 2020), "412345", None)
    assert ref.raw.startswith("15 mars 2020")


def test_jurisdiction_not_inherited_across_sentence_or_beyond_bound():
    plain = "La Cour de cassation juge ainsi.\n\nUn arrêt du 12 mars 2015 (pourvoi n° 13-27.123)."
    assert [r.jurisdiction for r in extract_references(plain)] == [None]
    far = "Arrêt de la Cour de cassation :\n\n" + "Texte sans référence. " * 12 + "n° 13-27.123"
    assert [r.jurisdiction for r in extract_references(far)] == [None]
    other = "Cour de cassation :\nLa cour d'appel de Lyon, 5 juin 2012, n° 10/01234, a jugé."
    assert [(r.jurisdiction, r.seat_text) for r in extract_references(other)] == [("ca", "Lyon")]


def test_long_sentence_keeps_its_court():
    """Phrase coupée par la borne de 200 caractères : date et numéro restent à la même cour."""
    text = (
        "La Cour de cassation a affirmé que le bailleur doit délivrer un logement décent et que "
        "cette obligation ne peut être écartée par une clause contraire, même acceptée par le "
        "preneur (arrêt du 12 mars 2018, n° 17-11.001)."
    )
    (ref,) = extract_references(text)
    assert _fields(ref) == ("cc", None, None, (12, 3, 2018), "17-11.001", None)


def test_repeated_number_is_one_reference():
    text = (
        "Cour de cassation :\nArrêt n° 09-11.222\nChambre civile\nDate : 22 février 2010\n"
        "Numéro de pourvoi : 09-11.222\n"
    )
    (ref,) = extract_references(text)
    assert _fields(ref) == ("cc", "Chambre civile", None, (22, 2, 2010), "09-11.222", None)
    # Deux numéros différents restent deux références (liste de D3).
    refs = extract_references("Cass. soc., 3 mai 2000, n° 98-12.345, puis n° 99-11.111.")
    assert [r.number_text for r in refs] == ["98-12.345", "99-11.111"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Arrêt du 12 mars 2015, Cour de cassation, 2e chambre civile, n° 14-11.222.",
            ("cc", "2e chambre civile", None, (12, 3, 2015), "14-11.222", None),
        ),
        (
            "L'arrêt du 24 juin 1983, rendu par la Cour de cassation, porte le numéro 10-67-50.",
            ("cc", None, None, (24, 6, 1983), "10-67-50", None),
        ),
        (
            "Date : 20 mai 2009 (Arrêt n° 2008-137 du Conseil d'État)\n"
            "Numéro de requête : RE 2008-137",
            ("ce", None, None, (20, 5, 2009), "2008-137", None),
        ),
        (
            "Dans l'arrêt n° 2019/1234 du 12 juin 2021, le Conseil d'État a jugé la mesure légale.",
            ("ce", None, None, (12, 6, 2021), "2019/1234", None),
        ),
    ],
)
def test_date_and_number_before_anchor(text, expected):
    (ref,) = extract_references(text)
    assert _fields(ref) == expected
    assert text[ref.start : ref.end] == ref.raw


def test_date_of_previous_sentence_not_attached():
    text = "Contrat signé le 3 mai 2010. La cour d'appel de Lyon, 5 juin 2012, n° 10/01234."
    (ref,) = extract_references(text)
    assert (ref.jurisdiction, (ref.day, ref.month, ref.year)) == ("ca", (5, 6, 2012))


@pytest.mark.parametrize(
    ("text", "number"),
    [
        ("Cour de cassation, 12 janvier 2015, n° 2013\u201114.123", "2013-14.123"),
        ("Cass. soc., 12 janvier 2015, n° 13\u201327.123", "13-27.123"),
        ("Conseil d'État, 13 mars 2008, n° 2007\u201114\u201112345", "2007-14-12345"),
    ],
)
def test_typographic_dashes_in_number_keep_offsets(text, number):
    (ref,) = extract_references(text)
    assert ref.number_text == number
    assert ref.raw == text[ref.start : ref.end] and ref.end == len(text)
    assert "\u2011" in ref.raw or "\u2013" in ref.raw  # texte d'origine, pas la copie de repérage


def test_date_never_read_inside_a_number():
    text = "Cour de cassation, Chambre civile, 15-14.12.2014-01000, n° 15-14.12.2014-01000"
    (ref,) = extract_references(text)
    assert (ref.day, ref.month, ref.year) == (None, None, None)
    assert ref.number_text == "15-14.12.2014-01000"
    # Une date numérique isolée reste lue.
    (dated,) = extract_references("Cass. soc., 14.12.2014, n° 13-27.123")
    assert (dated.day, dated.month, dated.year) == (14, 12, 2014)


@pytest.mark.parametrize(
    ("text", "formation"),
    [
        ("Cass. fisc., 16 décembre 2019, n° 18-22.111", "fisc."),
        ("Cour de cassation, 2\u1d49 chambre, 12 mars 2005, n° 03-11.111", "2e chambre"),
        ("La 3\u1d49 chambre de la Cour de cassation, le 4 mai 2006, n° 04-12.121", "3e chambre"),
        ("Cass. civ. 1\u02b3\u1d49, 3 mai 2000, n° 98-12.345", "civ. 1re"),
    ],
)
def test_fiscal_and_superscript_formations(text, formation):
    (ref,) = extract_references(text)
    assert ref.formation_text == formation
    assert ref.raw == text[ref.start : ref.end]


def test_single_word_refere_is_not_a_formation():
    (ref,) = extract_references("CE, 5 mars 2021, n° 445566 : la recevabilité du référé.")
    assert ref.formation_text is None
    (judge,) = extract_references("CE, juge des référés, 7 mars 2021, n° 445567")
    assert judge.formation_text == "juge des référés"
