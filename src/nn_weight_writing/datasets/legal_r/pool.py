"""Vraies candidates de R (story 1-13, D3, S10, S12) : décisions d'un jour, même normaliseur.

Un seul point d'appel à `normalize` pour les deux classes (`reference_of`, CAP-11) : la chaîne
des fausses (`dataset.select_fakes`) et celle des vraies passent par lui. Le `raw` d'une vraie
est la référence normalisée, sans autre modification (condition 4 de 1-3) ; ses champs d'origine
sont gardés à part (`origin`, sans texte ni nom), pour la non-altération (S12).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date

from nn_weight_writing.datasets.legal_r.ce_index import CeIndex
from nn_weight_writing.datasets.legal_r.judilibre import JudilibreClient
from nn_weight_writing.datasets.legal_r.normalize import (
    NormalizedRef,
    RefFields,
    fields_from_ce_opendata,
    fields_from_judilibre,
    normalize,
    normalize_number,
)
from nn_weight_writing.tasks.legal.encoders import encode_chars
from nn_weight_writing.tasks.legal.reference import format_reference, parse_reference

R_RAW_MAX = 160
CC_ORIGIN_FIELDS = (
    "id",
    "jurisdiction",
    "chamber",
    "decision_date",
    "number",
    "numbers",
    "ecli",
    "type",
    "update_date",
)
CE_ORIGIN_FIELDS = (
    "Numero_Dossier",
    "Date_Lecture",
    "Formation_Jugement",
    "Numero_ECLI",
    "Type_Decision",
    "Date_Mise_Jour",
)


def reference_of(fields: RefFields) -> tuple[NormalizedRef, str | None]:
    """`normalize`, puis `to_reference()` et `format_reference()` : seul appel au normaliseur."""
    ref = normalize(fields)
    reference = ref.to_reference()
    return ref, (format_reference(reference) if reference is not None else None)


def d1_ok(raw: str | None) -> bool:
    """Référence écrite en D1 : relue à l'identique, 160 caractères au plus, encodable."""
    if not raw or len(raw) > R_RAW_MAX:
        return False
    try:
        if format_reference(parse_reference(raw)) != raw:
            return False
        encode_chars(raw)
    except ValueError, TypeError, IndexError:
        return False
    return True


@dataclass(frozen=True)
class RealCandidate:
    jurisdiction: str
    formation: str
    day: date
    number: str
    raw: str
    source: str  # "judilibre" ou "ce-opendata"
    source_id: str
    update_date: str | None
    numbers: frozenset[str] = frozenset()  # tous les numéros normalisés de la décision
    origin: dict = field(default_factory=dict, compare=False, hash=False)


def project_candidate(
    fields: RefFields, origin: Mapping, numbers: Iterable[str | None] = ()
) -> RealCandidate | None:
    """Décision -> candidate ; None si la référence n'est pas complète et écrite en D1."""
    ref, raw = reference_of(fields)
    if ref.jurisdiction not in ("cc", "ce") or not d1_ok(raw):
        return None
    try:
        day = date(ref.year, ref.month, ref.day)
    except TypeError, ValueError:
        return None
    all_numbers = {ref.number}
    all_numbers.update(n for n in (normalize_number(x, ref.jurisdiction) for x in numbers) if n)
    return RealCandidate(
        jurisdiction=ref.jurisdiction,
        formation=ref.formation,
        day=day,
        number=ref.number,
        raw=raw,
        source=fields.source or "",
        source_id=fields.source_id or "",
        update_date=fields.update_date,
        numbers=frozenset(all_numbers),
        origin=dict(origin),
    )


def cc_day_candidates(client: JudilibreClient, day: date) -> list[RealCandidate]:
    """Décisions de la Cour de cassation rendues ce jour (`/scan` du jour, S10), projetées.

    Tous les `type` sont gardés, comme à la vérification d'existence de 1-12 : la base classe
    `other` l'essentiel des décisions récentes (mesure de la phase A, 2026-11-07), et le type
    n'est pas visible dans le `raw`. Il reste dans `origin`."""
    out = []
    for meta in client.scan_day("cc", day.isoformat()):
        if meta.get("decision_date") != day.isoformat():
            continue
        origin = {k: meta[k] for k in CC_ORIGIN_FIELDS if k in meta}
        numbers = [meta.get("number"), *(meta.get("numbers") or [])]
        candidate = project_candidate(fields_from_judilibre(meta), origin, numbers)
        if candidate is not None:
            out.append(candidate)
    return out


class CeDays:
    """Index du Conseil d'État rangé par jour de lecture (aucun téléchargement)."""

    def __init__(self, index: CeIndex) -> None:
        self._by_day: dict[str, list[dict]] = {}
        for record in index.records:
            self._by_day.setdefault(str(record.get("Date_Lecture", ""))[:10], []).append(record)

    def candidates(self, day: date) -> list[RealCandidate]:
        out = []
        for record in self._by_day.get(day.isoformat(), []):
            origin = {k: record[k] for k in CE_ORIGIN_FIELDS if k in record}
            candidate = project_candidate(fields_from_ce_opendata(record), origin)
            if candidate is not None:
                out.append(candidate)
        return out
