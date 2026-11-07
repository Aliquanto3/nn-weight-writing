"""Unités dédupliquées, citation canonique, classes et classement publié (story 1-12, D6).

Aucune part n'est calculée ici (P1) : `porte` les calcule après le contrôle de qualité.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from nn_weight_writing.datasets.legal_r.existence import Verification
from nn_weight_writing.datasets.legal_r.extract import ExtractedRef
from nn_weight_writing.datasets.legal_r.grid import incoherences, nuss_types
from nn_weight_writing.datasets.legal_r.normalize import NormalizedRef
from nn_weight_writing.datasets.legal_r.r_facts import RFacts
from nn_weight_writing.tasks.legal.facts import Facts, load_facts
from nn_weight_writing.tasks.legal.reference import format_reference

CLASSEMENT_SCHEMA = 1
CLASSES = ("incoherent", "coherent_absent", "exists", "unverifiable", "partial", "out_of_scope")
SCOPE = ("cc", "ce")  # P5 : les cours d'appel citées sont hors du champ de l'étude
CLASSEMENT_FIELDS = (
    "schema",
    "unit_id",
    "jurisdiction",
    "formation",
    "year",
    "month",
    "day",
    "number",
    "ecli",
    "canonical",
    "class",
    "rules",
    "nuss_types",
    "unverifiable_reason",
    "partial_match",
    "grid_false_positive",
    "class_conflict",
    "verification",
    "citations",
    "source",
    "versions",
)


@dataclass(frozen=True)
class Citation:
    model: str
    digest: str
    request_id: str
    start: int
    end: int
    raw: str
    generation_date: date
    ref: NormalizedRef


@dataclass
class Unit:
    key: tuple
    citations: list[Citation]
    unit_id: str = ""
    klass: str | None = None
    rules: frozenset[str] = frozenset()
    unverifiable_reason: str | None = None
    partial_match: str | None = None
    grid_false_positive: bool = False
    class_conflict: bool = False
    verification: Verification | None = None
    extra: dict = field(default_factory=dict)

    @property
    def canonical(self) -> Citation:
        return self.citations[0]

    @property
    def ref(self) -> NormalizedRef:
        return self.canonical.ref


def citation_from(
    extracted: ExtractedRef, ref: NormalizedRef, *, model, digest, request_id, generation_date
) -> Citation:
    return Citation(
        model=model,
        digest=digest,
        request_id=request_id,
        start=extracted.start,
        end=extracted.end,
        raw=extracted.raw,
        generation_date=generation_date,
        ref=ref,
    )


def _sortable(key: tuple) -> tuple:
    jurisdiction, number, (year, month, day) = key
    return (
        jurisdiction or "",
        number or "",
        year if year is not None else -1,
        month if month is not None else -1,
        day if day is not None else -1,
    )


def build_units(citations: Iterable[Citation], model_order: Sequence[str]) -> list[Unit]:
    """Unité = `key()` ; une clé citée deux fois dans une réponse compte une citation.

    Citation canonique : modèle dans l'ordre de `model_order`, puis `request_id`, puis `start`.
    `unit_id` : rang dans l'ordre trié des clés.
    """
    rank = {m: i for i, m in enumerate(model_order)}
    groups: dict[tuple, dict[tuple, Citation]] = {}
    for cit in citations:
        key = cit.ref.key()
        per_response = groups.setdefault(key, {})
        response = (cit.model, cit.request_id)
        if response not in per_response or cit.start < per_response[response].start:
            per_response[response] = cit
    units = []
    for i, key in enumerate(sorted(groups, key=_sortable), start=1):
        cits = sorted(
            groups[key].values(),
            key=lambda c: (rank.get(c.model, len(rank)), c.model, c.request_id, c.start),
        )
        units.append(Unit(key=key, citations=cits, unit_id=f"r-u{i:05d}"))
    return units


def classify_unit(
    unit: Unit,
    *,
    facts: Facts,
    r_facts: RFacts,
    verify: Callable[[NormalizedRef], Verification] | None,
    scope: Sequence[str] = SCOPE,
) -> Unit:
    """Ordre de D6, d'après la citation canonique ; `verify` : vérification d'existence (D5)."""
    ref = unit.ref
    rules_per_citation = [
        incoherences(c.ref, generation_date=c.generation_date, facts=facts, r_facts=r_facts)
        for c in unit.citations
    ]
    unit.rules = rules_per_citation[0]
    unit.class_conflict = len({bool(r) for r in rules_per_citation}) > 1
    # Juridiction inconnue (None) : référence incomplète, donc `partial` (D6, ordre 1 puis 2).
    if ref.jurisdiction is not None and ref.jurisdiction not in scope:
        unit.klass = "out_of_scope"
        return unit
    if not ref.is_complete():
        unit.klass = "partial"
        return unit
    verification = verify(ref) if verify is not None else Verification("unverifiable", "api_error")
    # Rappel insuffisant (P6) : une absence n'est plus une preuve pour cette juridiction.
    if verification.status == "absent" and not r_facts.recall_reliable.get(ref.jurisdiction):
        verification = Verification("unverifiable", reason="verification_unreliable")
    unit.verification = verification
    unit.partial_match = verification.partial_match
    if verification.status == "exists":
        unit.klass = "exists"
        unit.grid_false_positive = bool(unit.rules)
        return unit
    if unit.rules:
        unit.klass = "incoherent"
        return unit
    if verification.status == "absent":
        unit.klass = "coherent_absent"
        return unit
    unit.klass = "unverifiable"
    unit.unverifiable_reason = verification.reason
    return unit


def _canonical(ref: NormalizedRef) -> str | None:
    reference = ref.to_reference()
    return format_reference(reference) if reference is not None else None


def _published_formation(ref: NormalizedRef) -> tuple[str | None, str | None]:
    """Formation et citation canonique publiées.

    Un siège de cour d'appel hors des 36 garde le nom cité pour la grille (D3, R-O3), mais ce nom
    peut être celui d'une partie (« CA Renault SA ») : il n'est pas publié (D3, D6 : aucun nom).
    """
    if ref.jurisdiction == "ca" and ref.formation not in load_facts().all_seats:
        return None, None
    return ref.formation, _canonical(ref)


def classement_row(unit: Unit, versions: dict) -> dict:
    ref = unit.ref
    verification = unit.verification or Verification("unverifiable")
    formation, canonical = _published_formation(ref)
    row = {
        "schema": CLASSEMENT_SCHEMA,
        "unit_id": unit.unit_id,
        "jurisdiction": ref.jurisdiction,
        "formation": formation,
        "year": ref.year,
        "month": ref.month,
        "day": ref.day,
        "number": ref.number,
        "ecli": ref.ecli,
        "canonical": canonical,
        "class": unit.klass,
        "rules": sorted(unit.rules),
        "nuss_types": list(nuss_types(unit.rules)),
        "unverifiable_reason": unit.unverifiable_reason,
        "partial_match": unit.partial_match,
        "grid_false_positive": unit.grid_false_positive,
        "class_conflict": unit.class_conflict,
        "verification": verification.as_dict(),
        "citations": [
            {"model": c.model, "digest": c.digest[:12], "request_id": c.request_id}
            for c in unit.citations
        ],
        "source": "slm",
        "versions": dict(versions),
    }
    assert tuple(row) == CLASSEMENT_FIELDS
    return row


def _same(text: str) -> str:
    return text


def write_classement(
    path: Path, units: Sequence[Unit], versions: dict, *, redact: Callable[[str], str] = _same
) -> None:
    """Une ligne par unité, triée par `unit_id` ; ni texte de réponse, ni passage, ni nom.

    `redact` : masque des secrets appliqué à chaque ligne écrite (P9 ; le script passe celui du
    journal)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for unit in sorted(units, key=lambda u: u.unit_id):
            line = json.dumps(classement_row(unit, versions), ensure_ascii=False)
            handle.write(redact(line) + "\n")


def write_extraction(
    path: Path, units: Sequence[Unit], *, redact: Callable[[str], str] = _same
) -> None:
    """Passages cités (`raw`, `start`, `end`) : `interne/`, jamais publié (D8)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for unit in sorted(units, key=lambda u: u.unit_id):
            for c in unit.citations:
                row = {
                    "unit_id": unit.unit_id,
                    "model": c.model,
                    "request_id": c.request_id,
                    "start": c.start,
                    "end": c.end,
                    "raw": c.raw,
                }
                handle.write(redact(json.dumps(row, ensure_ascii=False)) + "\n")


def read_classement(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
