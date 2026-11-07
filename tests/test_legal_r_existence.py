"""Vérification d'existence et fenêtres (story 1-12, D5, AC10, AC11, AC13)."""

from __future__ import annotations

import json
from datetime import date

from legal_r_support import (
    EMPTY_SCAN,
    EMPTY_SEARCH,
    FakeClock,
    FakeTransport,
    body,
    ce_archive,
    make_client,
    ok,
)

from nn_weight_writing.datasets.legal_r.ce_index import KEPT_TAGS, CeIndex, parse_archive
from nn_weight_writing.datasets.legal_r.classify import Unit, citation_from, classify_unit
from nn_weight_writing.datasets.legal_r.existence import (
    CoverageWindow,
    check_existence,
    coverage_windows,
)
from nn_weight_writing.datasets.legal_r.extract import extract_references
from nn_weight_writing.datasets.legal_r.normalize import RefFields, fields_from_extracted, normalize
from nn_weight_writing.datasets.legal_r.r_facts import RFacts
from nn_weight_writing.tasks.legal.facts import load_facts

TODAY = date(2026, 11, 7)
WINDOWS = {
    "cc": CoverageWindow("cc", date(1989, 1, 1), date(2026, 8, 7), "test"),
    "ca": CoverageWindow("ca", date(2022, 4, 15), date(2026, 7, 31), "test"),
    "ce": CoverageWindow("ce", date(2021, 9, 30), date(2026, 10, 7), "test"),
}


def _ref(text):
    (extracted,) = extract_references(text)
    return normalize(fields_from_extracted(extracted))


def _client(tmp_path):
    clock = FakeClock()
    transport = FakeTransport(
        [
            ("/scan", {"date_start": "2000-11-17"}, [ok("scan_cc_2000-11-17.json")]),
            ("/scan", {}, [ok(EMPTY_SCAN)]),
            ("/search", {"query": "99-13.701"}, [ok("search_99-13.701.json")]),
            ("/search", {"query": "99-99.999"}, [ok("search_99-99.999_relaxed.json")]),
            ("/search", {}, [ok(EMPTY_SEARCH)]),
        ],
        clock,
    )
    return make_client(transport, clock, tmp_path / "cache"), transport


def _check(ref, client, ce_index=None):
    return check_existence(ref, client=client, ce_index=ce_index, windows=WINDOWS, today=TODAY)


def test_exists_by_field_equality(tmp_path):
    client, _ = _client(tmp_path)
    found = _check(_ref("Cass. ass. plén., 17 novembre 2000, n° 99-13.701"), client)
    assert (found.status, found.found_id, found.source) == (
        "exists",
        "60793b359ba5988459c3c363",
        "judilibre",
    )
    assert found.cache_key and found.partial_match is None
    # Un élément de `numbers` suffit (décision à deux pourvois joints).
    joined = _check(_ref("Cass. civ. 1re, 17 novembre 2000, n° 98-10.002"), client)
    assert (joined.status, joined.found_id) == ("exists", "fixture-cc-0002")
    # Sans formation : numéro et date.
    bare = _check(_ref("Cass., 17 novembre 2000, n° 99-13.701"), client)
    assert bare.status == "exists"


def test_partial_matches(tmp_path):
    client, _ = _client(tmp_path)
    other_day = _check(_ref("Cass. ass. plén., 18 novembre 2000, n° 99-13.701"), client)
    assert (other_day.status, other_day.partial_match) == ("absent", "date")
    other_chamber = _check(_ref("Cass. civ. 1re, 17 novembre 2000, n° 99-13.701"), client)
    assert (other_chamber.status, other_chamber.partial_match) == ("absent", "formation")
    assert other_chamber.found_id is None


def test_relaxed_search_ignored(tmp_path):
    client, _ = _client(tmp_path)
    invented = _check(_ref("Cass. ass. plén., 17 novembre 2000, n° 99-99.999"), client)
    assert (invented.status, invented.partial_match, invented.found_id) == ("absent", None, None)


def test_coverage_windows():
    windows = coverage_windows(
        cc_stats=json.loads(body("stats_cc_year.json"))["results"],
        ca_stats=json.loads(body("stats_ca.json"))["results"],
        ce_max_date="2026-11-06",
    )
    # Fixture réduite : 2009 à 2021 absentes, comptées 0 -> début en 2022.
    assert {j: (w.start, w.end) for j, w in windows.items()} == {
        "cc": (date(2022, 1, 1), date(2026, 8, 7)),
        "ca": (date(2022, 4, 15), date(2026, 7, 31)),
        "ce": (date(2021, 9, 30), date(2026, 10, 7)),
    }
    # Série complète : médiane 2022-2025 = 16 314, seuil 8 157 ; 1988 (7 525) sous le seuil.
    dense = {y: 9000 for y in range(1985, 2026)} | {1988: 7525, 2022: 16231, 2023: 17236}
    dense |= {2024: 16351, 2025: 16277}
    stats = {
        "max_decision_date": "2026-11-05",
        "aggregated_data": [
            {"key": {"year": str(y)}, "decisions_count": n} for y, n in dense.items()
        ],
    }
    cc = coverage_windows(
        cc_stats=stats, ca_stats={"max_decision_date": "2026-10-29"}, ce_max_date="2026-11-06"
    )["cc"]
    assert cc.start == date(1989, 1, 1)
    # AC13 : cohérente CE de 2019 non vérifiable, incohérente CE de 2019 incohérente.
    facts = load_facts()
    r_facts = RFacts(recall_reliable={"cc": True, "ce": True})

    def unit(text):
        ref = _ref(text)
        cit = citation_from(
            extract_references(text)[0],
            ref,
            model="qwen3.5:2b",
            digest="sha256:abc",
            request_id="ce-001",
            generation_date=TODAY,
        )
        return Unit(key=ref.key(), citations=[cit])

    def verify(ref):
        return check_existence(ref, client=None, ce_index=CeIndex(), windows=WINDOWS, today=TODAY)

    coherent = classify_unit(
        unit("CE, 5e sous-sect., 12 mars 2015, n° 361234"),
        facts=facts,
        r_facts=r_facts,
        verify=verify,
    )
    assert (coherent.klass, coherent.unverifiable_reason) == ("unverifiable", "before_window")
    incoherent = classify_unit(
        unit("CE, 12e ch., 12 mars 2019, n° 412345"), facts=facts, r_facts=r_facts, verify=verify
    )
    assert (incoherent.klass, incoherent.rules) == ("incoherent", {"R-O5"})
    late = check_existence(
        _ref("CE, 5e ch., 20 octobre 2026, n° 491234"),
        client=None,
        ce_index=CeIndex(),
        windows=WINDOWS,
        today=TODAY,
    )
    assert late.reason == "after_window"
    penal = normalize(
        RefFields(
            jurisdiction="ca",
            seat_text="Paris",
            formation_text="chambre correctionnelle",
            day=12,
            month=3,
            year=2024,
            number_text="23/01234",
        )
    )
    assert check_existence(penal, client=None, ce_index=None, windows=WINDOWS).reason == "penal_ca"


def test_ce_index_lookup(tmp_path):
    index = CeIndex(parse_archive(ce_archive(tmp_path / "CE_fixture.zip")))
    assert len(index) == 3 and index.max_date() == "2024-10-10"
    (record,) = index.lookup("428 409")
    assert record["Formation_Jugement"] == "3ème et 8ème chambres réunies"
    index.save(tmp_path / "index.jsonl")
    reloaded = CeIndex.load(tmp_path / "index.jsonl")
    assert reloaded.records == sorted(
        index.records, key=lambda r: (r["Date_Lecture"], r["Numero_Dossier"])
    )
    windows = {**WINDOWS, "ce": CoverageWindow("ce", date(2020, 1, 1), date(2026, 10, 7), "t")}

    def check(text):
        return check_existence(
            _ref(text), client=None, ce_index=reloaded, windows=windows, today=TODAY
        )

    exists = check("CE, 3e et 8e chambres réunies, 10 juillet 2020, req. n° 428409")
    assert (exists.status, exists.source, exists.found_id) == ("exists", "ce-opendata", "428409")
    assert check("CE, 3e ch., 10 juillet 2020, n° 428409").partial_match == "formation"
    assert check("CE, 3e et 8e ch. réunies, 11 juillet 2020, n° 428409").partial_match == "date"
    assert check("CE, juge des référés, 15 janvier 2024, n° 490001").status == "exists"
    absent = check("CE, 3e ch., 10 juillet 2020, n° 428410")
    assert (absent.status, absent.partial_match) == ("absent", None)


def test_ce_archive_text_dropped(tmp_path):
    records = list(parse_archive(ce_archive(tmp_path / "CE_fixture.zip")))
    assert [r["Numero_Dossier"] for r in records] == ["428409", "447363", "490001"]
    for record in records:
        assert set(record) <= set(KEPT_TAGS)
        assert "Texte_Integral" not in record
    assert records[1]["Formation_Jugement"] == "3ème chambre jugeant seule"
    assert records[2]["Formation_Jugement"] == "Juge des référés"  # XML mal formé : repli
    index = CeIndex(records)
    index.save(tmp_path / "index.jsonl")
    written = (tmp_path / "index.jsonl").read_text(encoding="utf-8")
    assert "TEXTE-INTEGRAL-CE-SECRET" not in written and "Dupont" not in written
