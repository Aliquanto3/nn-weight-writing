"""Vérificateur de règles de S (story 1-9, D4 et O5, O6)."""

from __future__ import annotations

from datetime import date

import pytest

from nn_weight_writing.datasets.legal_rules import (
    easter,
    is_working_day,
    legal_holidays,
    number_year,
    violations,
)
from nn_weight_writing.tasks.legal.facts import FACTS_PATH, load_facts
from nn_weight_writing.tasks.legal.reference import MONTHS, parse_reference

NONE: set[str] = set()
CASES = [
    ("Cass. ass. plén., 17 novembre 2000, n° 99-13.701", NONE),
    ("Cass. ch. mixte, 21 février 2003, n° 99-18.759", NONE),
    ("CE, 5e ch., 12 mars 2019, n° 412345", NONE),
    ("CE, 3e sous-sect., 14 octobre 2010, n° 321456", NONE),
    ("CE, Sect., 15 juin 2016, n° 389012", NONE),
    ("CA Saint-Denis de la Réunion, 3 juin 2021, n° 19/01234", NONE),
    ("Cass. civ. 1re, 12 mars 2015, n° 06-27.123", NONE),
    ("Cass. civ. 1re, 14 mars 2015, n° 13-27.123", NONE),
    ("Cass. civ. 1re, 3 avril 2015, n° 13-27.123", NONE),
    ("Cass. civ. 1re, 12 mars 2015, n° 16-27.123", {"t01"}),
    ("Cass. soc., 30 février 2012, n° 10-14.567", {"t02"}),
    ("Cass. civ. 4e, 12 mars 2015, n° 13-27.123", {"t03"}),
    ("CA Lille, 12 mars 2015, n° 13/04567", {"t04"}),
    ("Cass. Sect., 12 mars 2015, n° 13-27.123", {"t05"}),
    ("CE, soc., 12 mars 2015, n° 381234", {"t05"}),
    ("CA Lyon, 4 mars 2027, n° 26/01234", {"t06"}),
    ("CE, 4e ch., 12 mars 2015, n° 381234", {"t07"}),
    ("CE, 4e sous-sect., 12 mars 2019, n° 412345", {"t07"}),
    ("Cass. crim., 12 mars 2015, n° 03-81.234", {"t08"}),
    ("CA Lyon, 12 mars 2015, n° 16/04567", {"t09"}),
    ("CA Lyon, 12 mars 2015, n° 1304567", {"t10"}),
    ("Cass. com., 12 mars 2015, n° 13-27123", {"t10"}),
    ("Cass. com., 12 mars 2015, n° 381234", {"t11"}),
    ("CA Lyon, 12 mars 2015, n° 13-27.123", {"t11"}),
    ("Cass. civ. 2e, 14 juillet 2015, n° 14-12.345", {"t12"}),
    ("CE, 2e ch., 15 mars 2020, n° 431234", {"t12"}),
    ("Cass. civ. 2e, 25 mai 2015, n° 14-12.345", {"t12"}),
    ("CA Lyon, 12 mars 2015, n° 04/04567", {"t13"}),
    ("Cass. crim., 12 mars 2015, n° 14-27.123", {"t14"}),
    ("Cass. soc., 12 mars 2015, n° 14-81.234", {"t14"}),
    ("CE, 1re ch., 29 février 2019, n° 412345", {"t15"}),
    ("Cass. civ. 1re, 12 mars 2015, n° 16-87.123", {"t01", "t14"}),
]


@pytest.mark.parametrize(("raw", "expected"), CASES)
def test_hand_written_references(raw, expected):
    assert violations(parse_reference(raw)) == frozenset(expected)


def test_holidays_match_service_public():
    h26 = legal_holidays(2026)
    assert h26[date(2026, 4, 6)] == "easter_monday"
    assert h26[date(2026, 5, 14)] == "ascension"
    assert h26[date(2026, 5, 25)] == "whit_monday"
    assert [d for d, name in legal_holidays(2027).items() if name == "easter_monday"] == [
        date(2027, 3, 29)
    ]
    fixed = {d for d, name in h26.items() if name[0].isdigit()}
    assert fixed == {
        date(2026, m, d)
        for m, d in [(1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25)]
    }
    assert len(h26) == 11


def test_easter_matches_a_hand_written_table():
    table = {
        2008: date(2008, 3, 23),
        2011: date(2011, 4, 24),
        2015: date(2015, 4, 5),
        2019: date(2019, 4, 21),
        2020: date(2020, 4, 12),
        2024: date(2024, 3, 31),
        2025: date(2025, 4, 20),
        2026: date(2026, 4, 5),
    }
    assert {year: easter(year) for year in table} == table


def meeus_jones_butcher(year: int) -> date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    month = (h + el - 7 * m + 114) // 31
    day = (h + el - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def test_easter_matches_a_second_algorithm():
    for year in range(2001, 2030):
        assert easter(year) == meeus_jones_butcher(year), year


def test_working_day_excludes_holidays_good_friday_and_boxing_day():
    assert is_working_day(date(2015, 3, 12))
    assert not is_working_day(date(2015, 3, 14))  # samedi
    assert not is_working_day(date(2015, 4, 3))  # Vendredi saint
    assert not is_working_day(date(2015, 4, 6))  # lundi de Pâques
    assert not is_working_day(date(2014, 12, 26))  # 26 décembre (vendredi)
    assert not is_working_day(date(2015, 5, 25))  # lundi de Pentecôte
    assert not is_working_day(date(2015, 7, 14))


def test_century_resolution():
    assert number_year("99-13.701", 2000) == 1999
    assert number_year("27-13.701", 2026) == 2027
    assert number_year("86-13.701", 2001) == 1986


def test_feb29_non_leap_violates_only_t15_on_any_weekday():
    # O6 : aucune règle de jour pour une date qui n'existe pas
    for year in (2003, 2015, 2019, 2022):
        found = violations(parse_reference(f"CA Lyon, 29 février {year}, n° 01/04567"))
        assert found == {"t15"} | ({"t13"} if year - 2001 >= 10 else set()), year
    assert (
        violations(parse_reference("CE, 1re sous-sect., 29 février 2016, n° 412345")) == frozenset()
    )


def test_t12_applies_to_legal_holidays_sundays_and_not_to_saturdays():
    f = load_facts()
    for day in (date(2018, 5, 10), date(2018, 4, 2), date(2018, 11, 11), date(2018, 12, 25)):
        assert day in legal_holidays(day.year, f)
    for day in (date(2018, 5, 10), date(2018, 4, 2), date(2018, 12, 25), date(2020, 3, 15)):
        raw = f"CA Lyon, {day.day} {MONTHS[day.month - 1]} {day.year}, n° 18/04567"
        assert violations(parse_reference(raw)) >= {"t12"}, day
    assert violations(parse_reference("CA Lyon, 17 mars 2018, n° 18/04567")) == frozenset()


def test_unverified_fact_is_refused(tmp_path):
    text = FACTS_PATH.read_text("utf-8")
    broken = text.replace('[dates]\nstatus = "convention"', '[dates]\nstatus = "unverified"', 1)
    assert broken != text
    path = tmp_path / "facts.toml"
    path.write_text(broken, "utf-8")
    with pytest.raises(ValueError, match="dates"):
        load_facts(path)
    assert load_facts(FACTS_PATH).corpus_date == date(2026, 11, 1)


def test_max_day_public_and_unchanged():
    """Story 1-12 : `MAX_DAY` exposé (ancien `_MAX_DAY`), valeurs inchangées."""
    from nn_weight_writing.datasets.legal_rules import MAX_DAY

    assert MAX_DAY == {2: 29, 4: 30, 6: 30, 9: 30, 11: 30}
