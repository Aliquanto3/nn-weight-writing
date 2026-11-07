"""Grille d'incohérence de R (story 1-12, D4, AC8 et AC9)."""

from __future__ import annotations

from datetime import date

import pytest

from nn_weight_writing.datasets.legal import generate_rows
from nn_weight_writing.datasets.legal_r.extract import extract_references
from nn_weight_writing.datasets.legal_r.grid import (
    BY_RULE,
    ECLI_RULES,
    NUSS_TO_RULE,
    RULES,
    incoherences,
)
from nn_weight_writing.datasets.legal_r.normalize import (
    RefFields,
    fields_from_extracted,
    normalize,
    normalize_number,
)
from nn_weight_writing.datasets.legal_r.r_facts import RFacts, load_r_facts
from nn_weight_writing.datasets.legal_rules import violations
from nn_weight_writing.tasks.legal.facts import load_facts
from nn_weight_writing.tasks.legal.reference import parse_reference

FACTS = load_facts()
NO_RULE_OFF = {"cc": frozenset(), "ce": frozenset(), "ca": frozenset()}
# AC8 : R-E4 et R-E5 désactivées, CCASS seul code mesuré pour `cc`.
TEST_R_FACTS = RFacts(
    ecli_codes={"cc": frozenset({"CCASS"})},
    disabled_rules={j: frozenset({"R-E4", "R-E5"}) for j in ("cc", "ce", "ca")},
)
GEN = date(2026, 11, 7)


def _ref(text: str, ecli: str | None = None):
    (extracted,) = [r for r in extract_references(text) if r.number_text]
    fields = fields_from_extracted(extracted)
    if ecli:
        fields = RefFields(**{**vars(fields), "ecli": ecli})
    return normalize(fields)


HAND_WRITTEN = [
    ("Cass. civ. 4e, 12 mars 2015, n° 13-27.123", None, GEN, {"R-O1"}),
    ("Cass. civ. 4e, 12 mars 1995, n° 93-12.345", None, GEN, set()),
    ("Cass. soc., 30 février 1990, n° 88-14.567", None, GEN, {"R-C1"}),
    ("Cass. civ. 1re, 15 mars 2015, n° 13-27.123", None, GEN, {"R-C4"}),
    ("Cass. civ. 1re, 6 avril 2015, n° 13-27.123", None, GEN, set()),
    ("CA Lyon, 15 mars 2015, n° 13/04567", None, GEN, set()),
    ("CE, juge des référés, 15 mars 2020, n° 439674", None, GEN, set()),
    ("CE, 3e et 8e ch. réunies, 12 mars 2014, n° 361234", None, GEN, {"R-O4"}),
    ("CE, 12e ch., 12 mars 2019, n° 412345", None, GEN, {"R-O5"}),
    ("CA Lille, 12 mars 2015, n° 13/04567", None, GEN, {"R-O3"}),
    ("Cass. com., 4 juin 2026, n° 24-12.345", None, date(2026, 5, 1), {"R-C3"}),
    ("Cass. crim., 12 mars 2015, n° 14-27.123", None, GEN, {"R-A1"}),
    (
        "Cass. ass. plén., 17 novembre 2000, n° 99-13.701",
        "ECLI:FR:CCASS:2001:AP00001",
        GEN,
        {"R-E3"},
    ),
    ("CE, 5e ch., 12 mars 2019, n° 412345", "ECLI:FR:CCASS:2019:C100001", GEN, {"R-E2"}),
    # Lignes de plus : bornes et domaines.
    ("Cass. soc., 29 février 2015, n° 13-27.123", None, GEN, {"R-C2"}),
    ("Cass. soc., 29 février 1999, n° 97-27.123", None, GEN, {"R-C2"}),
    ("Cass. soc., 12 mars 2015, n° 16-27.123", None, GEN, {"R-H1"}),
    ("Cass. soc., 12 mars 2015, n° 05-27.123", None, GEN, {"R-H2"}),
    ("Cass. soc., 12 mars 2015, n° 06-27.123", None, GEN, set()),
    ("CA Paris, 12 mars 2015, n° 05/01234", None, GEN, {"R-H4"}),
    ("CA Paris, 12 mars 2015, n° 16/01234", None, GEN, {"R-H3"}),
    ("Cass. soc., 12 mars 2015, n° 13-271.23", None, GEN, {"R-F1"}),
    ("Cass. soc., 12 mars 2015, n° 13/04567", None, GEN, {"R-F2"}),
    ("CE, 5e ch., 12 mars 2019, n° 412.345", None, GEN, {"R-F1"}),
    ("Cass. soc., 12 mars 2015, n° 1327123", None, GEN, set()),
    ("CE, Sect., 12 mars 2015, n° 13-27.123", None, GEN, {"R-F2"}),
    ("Cass. Sect., 12 mars 2015, n° 13-27.123", None, GEN, {"R-O2"}),
    ("CE, civ. 1re, 12 mars 2015, n° 361234", None, GEN, {"R-O2"}),
    ("CE, 3e sous-sect., 12 mars 2019, n° 412345", None, GEN, {"R-O4"}),
    ("CE, 3e ch., 12 mars 2014, n° 361234", None, GEN, {"R-O4"}),
    ("CE, 3e ch., 12 juillet 2016, n° 361234", None, GEN, set()),
    ("CE, Sect., 11 novembre 2020, n° 431234", None, GEN, {"R-C4"}),
    ("CE, 5e ch., 12 mars 2019, n° 412345", "ECLI:FR:CE:2019", GEN, {"R-E1"}),
    ("CE, 5e ch., 12 mars 2019, n° 412345", "ECLI:FR:CECHS:2019:412345.20190312", GEN, set()),
    ("Cass. com., 12 mars 2015, n° 13-27.123", "ECLI:FR:XYZ:2015:CO00001", GEN, set()),
    ("Cass. com., 12 mars 1995, n° 93-12.345", "ECLI:FR:CCASS:1996:CO00001", GEN, {"R-E3"}),
]


@pytest.mark.parametrize(("text", "ecli", "generation", "expected"), HAND_WRITTEN)
def test_grid_hand_written(text, ecli, generation, expected):
    ref = _ref(text, ecli)
    got = incoherences(ref, generation_date=generation, facts=FACTS, r_facts=TEST_R_FACTS)
    assert got == frozenset(expected)


def test_measured_ecli_rules_when_enabled():
    r_facts = RFacts(
        ecli_codes={"cc": frozenset({"CCASS"}), "ce": frozenset({"CECHR", "CECHS"})},
        cc_prefixes={"com.": frozenset({"CO"}), "soc.": frozenset({"SO"})},
        disabled_rules=NO_RULE_OFF,
    )
    ce = _ref("CE, 5e ch., 12 mars 2019, n° 412345", "ECLI:FR:CECHS:2019:412346.20190312")
    assert incoherences(ce, generation_date=GEN, r_facts=r_facts) == {"R-E4"}
    cc = _ref("Cass. com., 12 mars 2015, n° 13-27.123", "ECLI:FR:CCASS:2015:SO00012")
    assert incoherences(cc, generation_date=GEN, r_facts=r_facts) == {"R-E5"}
    unknown_prefix = _ref("Cass. com., 12 mars 2015, n° 13-27.123", "ECLI:FR:CCASS:2015:ZZ00012")
    assert incoherences(unknown_prefix, generation_date=GEN, r_facts=r_facts) == frozenset()
    cc_code_for_ce = _ref("Cass. com., 12 mars 2015, n° 13-27.123", "ECLI:FR:CECHR:2015:CO1")
    assert incoherences(cc_code_for_ce, generation_date=GEN, r_facts=r_facts) == {"R-E2"}


def _s_refs():
    for rows in generate_rows(0).values():
        for row in rows:
            ref = parse_reference(row.raw)
            fields = RefFields(
                jurisdiction=ref.jurisdiction,
                formation_text=ref.formation if ref.jurisdiction != "ca" else None,
                seat_text=ref.formation if ref.jurisdiction == "ca" else None,
                day=ref.day,
                month=ref.month,
                year=ref.year,
                number_text=ref.number,
            )
            yield ref, row.type_id, normalize(fields)


def test_grid_matches_violations():
    """AC9 : mêmes règles que `violations()` sur les cinq jeux de S (graine 0)."""
    r_facts = RFacts(disabled_rules=NO_RULE_OFF)
    checked = repaired = 0
    window = (FACTS.window_start, FACTS.window_end)
    for ref, type_id, norm in _s_refs():
        assert norm.to_reference() is not None
        found = violations(ref, FACTS)
        got = incoherences(norm, generation_date=FACTS.corpus_date, facts=FACTS, r_facts=r_facts)
        # R-C3 <-> t06 (date de génération = date d'arrêt du corpus).
        assert ("R-C3" in got) == ("t06" in found)
        # R-C4 : t12 restreint (fêtes fixes et dimanches, pas les cours d'appel).
        assert "R-C4" not in got or "t12" in found
        day = (
            date(ref.year, ref.month, ref.day)
            if "t02" not in found and "t15" not in found
            else None
        )
        if day is None or not window[0] <= day <= window[1]:
            continue
        expected = {NUSS_TO_RULE[t] for t in found - {"t06", "t12", "x_formation"}}
        if "t10" in found and normalize_number(ref.number, ref.jurisdiction) != ref.number:
            # P2 : point ou tiret manquant d'un numéro de la Cour de cassation, canonisé.
            expected.discard("R-F1")
            repaired += 1
        assert got - {"R-C3", "R-C4", "R-O5"} == expected, (ref, type_id)
        checked += 1
    assert checked > 15000
    assert repaired > 0


def test_domains():
    """Avant 2001 ou après la génération : seules les règles U jouent."""
    r_facts = RFacts(disabled_rules=NO_RULE_OFF)
    old = _ref("Cass. civ. 4e, 15 mars 1998, n° 03-27.123")
    assert incoherences(old, generation_date=GEN, r_facts=r_facts) == frozenset()
    future = _ref("Cass. civ. 4e, 31 février 2027, n° 03-27.123")
    assert incoherences(future, generation_date=GEN, r_facts=r_facts) == {"R-C1", "R-C3"}
    boundary = _ref("Cass. crim., 2 janvier 2001, n° 99-27.123")
    assert incoherences(boundary, generation_date=GEN, r_facts=r_facts) == {"R-A1"}
    before = _ref("Cass. crim., 1er janvier 2001, n° 99-27.123")
    assert incoherences(before, generation_date=GEN, r_facts=r_facts) == frozenset()
    assert {r.domain for r in RULES} == {"U", "F", "M"}


def test_disabled_rule_not_applied():
    ref = _ref("Cass. civ. 4e, 12 mars 2015, n° 13-27.123")
    on = RFacts(disabled_rules=NO_RULE_OFF)
    off = RFacts(disabled_rules={"cc": frozenset({"R-O1"})})
    other = RFacts(disabled_rules={"ce": frozenset({"R-O1"})})
    assert incoherences(ref, generation_date=GEN, r_facts=on) == {"R-O1"}
    assert incoherences(ref, generation_date=GEN, r_facts=off) == frozenset()
    assert incoherences(ref, generation_date=GEN, r_facts=other) == {"R-O1"}


def test_partial_reference_rules():
    no_number = normalize(RefFields(jurisdiction="cc", day=30, month=2, year=2015))
    assert incoherences(no_number, generation_date=GEN, r_facts=TEST_R_FACTS) == {"R-C1"}
    no_court = normalize(RefFields(day=12, month=3, year=2015, number_text="13-271.23"))
    assert incoherences(no_court, generation_date=GEN, r_facts=TEST_R_FACTS) == {"R-F1"}
    no_date = normalize(RefFields(jurisdiction="cc", number_text="13-271.23"))
    assert incoherences(no_date, generation_date=GEN, r_facts=TEST_R_FACTS) == frozenset()


def test_rules_table_complete():
    ids = [r.id for r in RULES]
    assert len(ids) == len(set(ids)) == 21
    for rule in RULES:
        assert rule.category in {
            "calendrier",
            "chronologie",
            "format",
            "formation",
            "ECLI",
            "autre",
        }
        assert rule.domain in {"U", "F", "M"} and rule.basis
    assert [r.id for r in RULES if r.category == "autre"] == ["R-A1"]
    assert ECLI_RULES == {"R-E1", "R-E2", "R-E3", "R-E4", "R-E5"}
    assert {r.id for r in RULES if r.domain == "M"} == {"R-E2", "R-E4", "R-E5"}
    assert BY_RULE["R-C4"].nuss == "t12" and BY_RULE["R-O5"].nuss is None
    # Le fichier livré passe le chargeur (aucune section `unverified`).
    shipped = load_r_facts()
    assert shipped.recall_reliable == {"cc": True, "ce": True}
    assert set(shipped.coverage) == {"cc", "ce", "ca"}
