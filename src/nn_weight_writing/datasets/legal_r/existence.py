"""Vérification d'existence et fenêtres de couverture (story 1-12, D5).

Égalité exacte sur les champs (numéro normalisé, date, formation canonique ou siège), jamais sur
le total d'une recherche (T5, `relaxed`). Cour de cassation et cours d'appel : `/scan` du jour ;
Conseil d'État : index local de l'open data.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from nn_weight_writing.datasets.legal_r.ce_index import CeIndex
from nn_weight_writing.datasets.legal_r.judilibre import JudilibreClient, JudilibreError, cache_key
from nn_weight_writing.datasets.legal_r.normalize import (
    NormalizedRef,
    fields_from_ce_opendata,
    fields_from_judilibre,
    normalize,
    normalize_number,
)
from nn_weight_writing.datasets.legal_r.r_facts import load_seat_tables

CA_START = date(2022, 4, 15)
CE_START = date(2021, 9, 30)
CC_MEDIAN_YEARS = (2022, 2025)
CC_LAST_FULL_YEAR = 2025
CC_SHARE = 0.5
END_MARGIN = {"cc": 90, "ca": 90, "ce": 30}


@dataclass(frozen=True)
class CoverageWindow:
    jurisdiction: str
    start: date
    end: date
    basis: str

    def position(self, day: date) -> str | None:
        if day < self.start:
            return "before_window"
        if day > self.end:
            return "after_window"
        return None


def _cc_start(stats: dict) -> int:
    counts = {
        int(item["key"]["year"]): int(item["decisions_count"]) for item in stats["aggregated_data"]
    }
    low, high = CC_MEDIAN_YEARS
    median = statistics.median(counts.get(y, 0) for y in range(low, high + 1))
    start = CC_LAST_FULL_YEAR
    while counts.get(start - 1, 0) >= CC_SHARE * median:
        start -= 1
    if counts.get(CC_LAST_FULL_YEAR, 0) < CC_SHARE * median:
        raise ValueError("couverture cc : l'année 2025 est sous le seuil")
    return start


def coverage_windows(
    *, cc_stats: dict, ca_stats: dict, ce_max_date: str
) -> dict[str, CoverageWindow]:
    """Fenêtres de D5 : `cc_stats` avec `keys=year`, `ca_stats` sans clé, date max de l'index CE."""
    cc_end = date.fromisoformat(cc_stats["max_decision_date"]) - timedelta(days=END_MARGIN["cc"])
    ca_end = date.fromisoformat(ca_stats["max_decision_date"]) - timedelta(days=END_MARGIN["ca"])
    ce_end = date.fromisoformat(ce_max_date) - timedelta(days=END_MARGIN["ce"])
    start_year = _cc_start(cc_stats)
    return {
        "cc": CoverageWindow(
            "cc", date(start_year, 1, 1), cc_end, "/stats?keys=year, 50 % de la médiane 2022-2025"
        ),
        "ca": CoverageWindow("ca", CA_START, ca_end, "diffusion systématique (1-3)"),
        "ce": CoverageWindow("ce", CE_START, ce_end, "open data du CE"),
    }


@dataclass(frozen=True)
class Verification:
    status: str  # "exists", "absent", "unverifiable"
    reason: str | None = None  # motif d'une non vérifiable (D5)
    partial_match: str | None = None  # "formation" ou "date"
    source: str | None = None  # "judilibre" ou "ce-opendata"
    cache_key: str | None = None
    found_id: str | None = None
    checked_at: str | None = None

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "checked_at": self.checked_at,
            "cache_key": self.cache_key,
            "found_id": self.found_id,
        }


def _valid_date(ref: NormalizedRef) -> date | None:
    try:
        return date(ref.year, ref.month, ref.day)
    except TypeError, ValueError:
        return None


def verifiable(
    ref: NormalizedRef, windows: dict[str, CoverageWindow], *, today: date | None = None
) -> str | None:
    """None si l'unité peut être vérifiée, sinon le motif (D5)."""
    if not ref.is_complete():
        return "incomplete"
    day = _valid_date(ref)
    if day is None:
        return "invalid_date"
    if day > (today or datetime.now(UTC).date()):
        return "future"
    if ref.jurisdiction == "ca" and ref.penal:
        return "penal_ca"
    window = windows.get(ref.jurisdiction)
    if window is None:
        return "no_window"
    return window.position(day)


def _record_numbers(meta: dict, jurisdiction: str) -> set[str]:
    raw = [meta.get("number"), *(meta.get("numbers") or [])]
    return {n for n in (normalize_number(x, jurisdiction) for x in raw if x) if n}


@dataclass(frozen=True)
class _Candidate:
    formation: str | None
    source_id: str | None
    source_id_numbers: frozenset[str]
    day: date | None


def _judilibre_candidates(results: list[dict], jurisdiction: str) -> list[_Candidate]:
    out = []
    for meta in results:
        norm = normalize(fields_from_judilibre(meta))
        out.append(
            _Candidate(
                norm.formation,
                meta.get("id"),
                frozenset(_record_numbers(meta, jurisdiction)),
                _valid_date(norm),
            )
        )
    return out


def _ce_candidates(records: list[dict]) -> list[_Candidate]:
    out = []
    for record in records:
        norm = normalize(fields_from_ce_opendata(record))
        out.append(
            _Candidate(
                norm.formation,
                record.get("Numero_Dossier"),
                frozenset({norm.number} if norm.number else set()),
                _valid_date(norm),
            )
        )
    return out


def location_code(seat: str | None) -> str | None:
    _, codes = load_seat_tables()
    for code, name in codes.items():
        if name == seat:
            return code
    return None


def check_existence(
    ref: NormalizedRef,
    *,
    client: JudilibreClient | None,
    ce_index: CeIndex | None,
    windows: dict[str, CoverageWindow],
    today: date | None = None,
) -> Verification:
    """Vérifie une unité complète dans sa fenêtre ; sinon `unverifiable` avec son motif."""
    reason = verifiable(ref, windows, today=today)
    if reason is not None:
        return Verification("unverifiable", reason=reason)
    day = _valid_date(ref)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if ref.jurisdiction == "ce":
        if ce_index is None:
            return Verification("unverifiable", reason="api_error")
        records = ce_index.lookup(ref.number)
        candidates = _ce_candidates(records)
        same_day = [c for c in candidates if c.day == day]
        source, key = "ce-opendata", None
    else:
        if client is None:
            return Verification("unverifiable", reason="api_error")
        location = None
        if ref.jurisdiction == "ca":
            location = location_code(ref.formation)
            if location is None:
                return Verification("unverifiable", reason="unknown_seat")
        params = {
            "jurisdiction": ref.jurisdiction,
            "date_start": day.isoformat(),
            "date_end": day.isoformat(),
            "date_type": "creation",
            "abridged": "true",
            "batch_size": 1000,
        }
        if location:
            params["location"] = location
        try:
            results = client.scan_day(ref.jurisdiction, day.isoformat(), location)
        except JudilibreError as error:
            if error.fatal:  # 423 ou quota journalier : arrêt net (D5, P8)
                raise
            return Verification("unverifiable", reason="api_error", source="judilibre")
        same_day = _judilibre_candidates(results, ref.jurisdiction)
        source, key = "judilibre", cache_key("/scan", params)
    with_number = [c for c in same_day if ref.number in c.source_id_numbers]
    for cand in with_number:
        if ref.formation is None or cand.formation == ref.formation:
            return Verification(
                "exists", source=source, cache_key=key, found_id=cand.source_id, checked_at=stamp
            )
    if with_number:
        return Verification(
            "absent",
            partial_match="formation",
            source=source,
            cache_key=key,
            found_id=None,
            checked_at=stamp,
        )
    # Diagnostic : le même numéro à une autre date (informatif).
    other_date = False
    if ref.jurisdiction == "ce":
        other_date = any(c.day != day for c in candidates)
    else:
        try:
            found = client.search_number(ref.number, ref.jurisdiction)
        except JudilibreError as error:
            if error.fatal:  # 423 ou quota journalier : arrêt net (D5, P8)
                raise
            return Verification("unverifiable", reason="api_error", source="judilibre")
        other_date = any(
            ref.number in _record_numbers(meta, ref.jurisdiction)
            and meta.get("decision_date") != day.isoformat()
            for meta in found
        )
    return Verification(
        "absent",
        partial_match="date" if other_date else None,
        source=source,
        cache_key=key,
        checked_at=stamp,
    )
