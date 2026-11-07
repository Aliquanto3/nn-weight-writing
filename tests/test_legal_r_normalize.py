"""Normaliseur commun de la pré-étude R (story 1-12, D3, P2, AC4 à AC7)."""

from __future__ import annotations

import json

import pytest
from legal_r_support import body

from nn_weight_writing.datasets.legal_r.extract import extract_references
from nn_weight_writing.datasets.legal_r.normalize import (
    ALLOWED_FIELDS,
    FORBIDDEN_FIELDS,
    NormalizedRef,
    RefFields,
    canonical_cc_chamber,
    canonical_ce_formation,
    canonical_seat,
    fields_from_ce_opendata,
    fields_from_extracted,
    fields_from_judilibre,
    normalize,
    normalize_number,
)
from nn_weight_writing.tasks.legal.reference import format_reference

PERRUCHE_KEY = ("cc", "99-13.701", (2000, 11, 17))
PERRUCHE_D1 = "Cass. ass. plén., 17 novembre 2000, n° 99-13.701"


def _from_text(text: str) -> NormalizedRef:
    (ref,) = extract_references(text)
    return normalize(fields_from_extracted(ref))


def test_same_reference_three_sources():
    slm = _from_text("l'arrêt Perruche (Cass. ass. plén., 17 novembre 2000, n° 99-13.701)")
    meta = json.loads(body("search_99-13.701.json"))["results"][0]
    judilibre = normalize(fields_from_judilibre(meta))
    abridged = _from_text("Cass., AP, 17 nov. 2000, n° 99-13.701")
    for ref in (slm, judilibre, abridged):
        assert ref.key() == PERRUCHE_KEY
        assert format_reference(ref.to_reference()) == PERRUCHE_D1
    assert (slm.source, judilibre.source, judilibre.source_id) == (
        "slm",
        "judilibre",
        "60793b359ba5988459c3c363",
    )


def test_forbidden_fields_never_copied():
    meta = json.loads(body("scan_cc_2000-11-17.json"))["results"][0]
    fields = fields_from_judilibre(meta)
    dumped = json.dumps(vars(fields), ensure_ascii=False)
    for secret in ("TEXTE-INTEGRAL-SECRET", "SURLIGNAGE-SECRET", "Dès lors", "responsabilité"):
        assert secret not in dumped
    assert set(vars(fields)) == ALLOWED_FIELDS
    # Liste blanche : clé interdite acceptée mais jamais copiée ; clé inconnue refusée.
    kept = RefFields.from_mapping({"jurisdiction": "cc", "text": "SECRET", "zones": {}})
    assert kept == RefFields(jurisdiction="cc")
    assert {"text", "zones", "text_highlight", "Texte_Integral"} <= FORBIDDEN_FIELDS
    with pytest.raises(ValueError, match="liste blanche"):
        RefFields.from_mapping({"jurisdiction": "cc", "parties": "Dupont"})
    with pytest.raises(TypeError):
        normalize({"jurisdiction": "cc"})


@pytest.mark.parametrize(
    ("text", "jurisdiction", "expected"),
    [
        # P2 : variantes sans ambiguïté canonisées (remplace AC6).
        ("99-13701", "cc", "99-13.701"),
        ("9913701", "cc", "99-13.701"),
        ("99 13.701", "cc", "99-13.701"),
        ("99 - 13.701", "cc", "99-13.701"),
        ("99.13.701", "cc", "99-13.701"),
        ("99–13.701", "cc", "99-13.701"),
        ("99-13.701", "cc", "99-13.701"),
        # Non canonisables : texte gardé, sans espaces, jugé par la grille.
        ("991-3701", "cc", "991-3701"),
        ("99-137.01", "cc", "99-137.01"),
        ("99-13.7012", "cc", "99-13.7012"),
        ("13/04567", "cc", "13/04567"),
        ("428 409", "ce", "428409"),
        ("108.243", "ce", "108.243"),
        ("4284090", "ce", "4284090"),
        ("13 / 04567", "ca", "13/04567"),
        ("13/4567", "ca", "13/4567"),
        ("1304567", "ca", "1304567"),
        (None, "cc", None),
        ("   ", "cc", None),
    ],
)
def test_number_not_repaired(text, jurisdiction, expected):
    assert normalize_number(text, jurisdiction) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("première chambre civile", "civ. 1re"),
        ("1re civ.", "civ. 1re"),
        ("civ. 1", "civ. 1re"),
        ("Civ. 1ère", "civ. 1re"),
        ("chambre civile 2", "civ. 2e"),
        ("troisième chambre civile", "civ. 3e"),
        ("chambre commerciale, financière et économique", "com."),
        ("Com.", "com."),
        ("chambre sociale", "soc."),
        ("Crim.", "crim."),
        ("chambre criminelle", "crim."),
        ("Ass. plén.", "ass. plén."),
        ("assemblée plénière", "ass. plén."),
        ("AP", "ass. plén."),
        ("chambre mixte", "ch. mixte"),
        ("civ1", "civ. 1re"),
        ("comm", "com."),
        ("cr", "crim."),
        ("pl", "ass. plén."),
        ("mi", "ch. mixte"),
        # Formes inexistantes : forme canonique inexistante (R-O1).
        ("4e chambre civile", "civ. 4e"),
        ("chambre sociale 2", "soc. 2e"),
        ("chambre fiscale", "ch. fiscale"),
        # Formation du CE citée pour la Cour de cassation (R-O2).
        ("Section", "Sect."),
        ("3e chambre", "3e ch."),
        ("3e et 8e chambres réunies", "3e et 8e ch. réunies"),
        # Illisibles : None (unparsed).
        ("Civ.", None),
        ("chambre des requêtes", None),
        ("chambres réunies", None),
        ("ordo", None),
        ("allciv", None),
        ("other", None),
        ("creun", None),
        (None, None),
    ],
)
def test_cc_chamber_forms(text, expected):
    assert canonical_cc_chamber(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Assemblée du contentieux", "Ass."),
        ("Ass.", "Ass."),
        ("Assemblée", "Ass."),
        ("Section du Contentieux", "Sect."),
        ("Sect.", "Sect."),
        ("3e chambre", "3e ch."),
        ("3ème chambre jugeant seule", "3e ch."),
        ("1ère chambre", "1re ch."),
        ("10ème chambre", "10e ch."),
        ("1re sous-section", "1re sous-sect."),
        ("3e sous-section", "3e sous-sect."),
        ("3e et 8e chambres réunies", "3e et 8e ch. réunies"),
        ("8ème et 3ème chambres réunies", "3e et 8e ch. réunies"),
        ("1ère - 4ème chambres réunies", "1re et 4e ch. réunies"),
        ("3ème, 8ème, 9ème et 10ème chambres réunies", "3e, 8e, 9e et 10e ch. réunies"),
        ("3e et 8e sous-sections réunies", "3e et 8e sous-sect. réunies"),
        ("12e chambre", "12e ch."),
        ("Juge des référés", "juge des référés"),
        ("Juge des référés, formation collégiale", "juge des référés"),
        # Chambre de la Cour de cassation citée pour le CE : forme de D1 (R-O2).
        ("première chambre civile", "civ. 1re"),
        ("assemblée plénière", "ass. plén."),
        ("Formation spécialisée", None),
        ("", None),
    ],
)
def test_ce_formation_forms_and_joined(text, expected):
    assert canonical_ce_formation(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Paris", "Paris"),
        ("aix", "Aix-en-Provence"),
        ("Aix-en-Provence", "Aix-en-Provence"),
        ("Saint-Denis", "Saint-Denis de la Réunion"),
        ("La Réunion", "Saint-Denis de la Réunion"),
        ("nimes", "Nîmes"),
        ("ca_st_denis_reunion", "Saint-Denis de la Réunion"),
        ("ca_lyon", "Lyon"),
        ("lille", "Lille"),
        ("clermont-ferrand", "Clermont-Ferrand"),
    ],
)
def test_seat_aliases(text, expected):
    assert canonical_seat(text) == expected


def test_partial_reference():
    ref = _from_text("Cass. civ. 1re, 12 mars 2015")
    assert (ref.number, ref.is_complete(), ref.to_reference()) == (None, False, None)
    assert ref.key() == ("cc", None, (2015, 3, 12))
    no_date = normalize(RefFields(jurisdiction="cc", number_text="13-27.123"))
    assert not no_date.is_complete()
    unknown = normalize(
        RefFields(jurisdiction=None, number_text="13-27.123", day=1, month=2, year=2015)
    )
    assert not unknown.is_complete()


def test_to_reference_is_d1():
    ce = normalize(
        fields_from_ce_opendata(
            {
                "Numero_Dossier": "428409",
                "Date_Lecture": "2020-07-10",
                "Formation_Jugement": "3ème et 8ème chambres réunies",
                "Numero_ECLI": "ECLI:FR:CECHR:2020:428409.20200710",
            }
        )
    )
    assert format_reference(ce.to_reference()) == (
        "CE, 3e et 8e ch. réunies, 10 juillet 2020, n° 428409"
    )
    assert ce.ecli == "ECLI:FR:CECHR:2020:428409.20200710"
    ca = normalize(
        RefFields(
            jurisdiction="ca",
            seat_text="aix",
            day=1,
            month=3,
            year=2015,
            number_text="13/04567",
            formation_text="chambre correctionnelle",
        )
    )
    assert format_reference(ca.to_reference()) == "CA Aix-en-Provence, 1er mars 2015, n° 13/04567"
    assert ca.penal is True
    no_formation = _from_text("Cass. Civ., 12 mars 2015, n° 13-27.123")
    assert no_formation.is_complete() and no_formation.to_reference() is None
    bad_month = normalize(
        RefFields(
            jurisdiction="cc",
            formation_text="soc.",
            day=1,
            month=13,
            year=2015,
            number_text="13-27.123",
        )
    )
    assert bad_month.is_complete() and bad_month.to_reference() is None


# --- Tour de correction de la phase B (E15) ---


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("fisc.", "ch. fiscale"),
        ("Cass. fisc.", "ch. fiscale"),
        ("ch. fisc.", "ch. fiscale"),
        ("2\u1d49 chambre", "2e ch."),
        ("1\u02b3\u1d49 chambre civile", "civ. 1re"),
        ("1\u1d49\u02b3 chambre civile", "civ. 1re"),
        ("3\u1d49 civ.", "civ. 3e"),
    ],
)
def test_cc_fiscal_abbreviation_and_superscripts(text, expected):
    assert canonical_cc_chamber(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("référé", None),
        ("la recevabilité du référé", None),
        ("Bureau des référés", "juge des référés"),
        ("ordonnance de référé", "juge des référés"),
        ("ord. réf.", "juge des référés"),
        ("juge des référés", "juge des référés"),
        ("3\u1d49 chambre", "3e ch."),
    ],
)
def test_ce_refere_needs_judge_or_order(text, expected):
    assert canonical_ce_formation(text) == expected
