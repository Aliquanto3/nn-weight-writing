"""Jeu R (`legal_r`, story 1-13) : fausses du classement de 1-12, vraies appariées, découpage.

Ordre de la construction (D2 à D5, décisions S1 à S12) :

1. `select_fakes` : unités du dénominateur de la porte (P0), dans la fenêtre de couverture,
   `canonical` recalculée par le même normaliseur que les vraies (CAP-11), aucun `raw` de S ;
2. `recheck_fakes` : revérification d'existence (D4) ;
3. `match_reals` : une vraie par fausse, même juridiction, jour (ou jour voisin de même type),
   formation et classe d'écart d'année du numéro (S1, S6, S10) ;
4. `split_pairs` : séance, entraînement et réservé, par paire et par strate (D5) ;
5. `write_r_dataset` : `examples.jsonl`, `labels.jsonl`, `sources.jsonl`, `dataset.json`.

Aucune fonction ne lit `data/r/` : le script `scripts/jeu_r.py` leur passe ce qu'il a lu.
"""

from __future__ import annotations

import calendar
import json
import re
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from nn_weight_writing.datasets.io import Row, write_dataset
from nn_weight_writing.datasets.legal_r.ce_index import CeIndex
from nn_weight_writing.datasets.legal_r.existence import CoverageWindow, check_existence
from nn_weight_writing.datasets.legal_r.extract import extract_references
from nn_weight_writing.datasets.legal_r.gate import family_of
from nn_weight_writing.datasets.legal_r.grid import BY_RULE, ECLI_RULES
from nn_weight_writing.datasets.legal_r.judilibre import JudilibreClient, JudilibreError
from nn_weight_writing.datasets.legal_r.normalize import NormalizedRef, fields_from_extracted
from nn_weight_writing.datasets.legal_r.pool import RealCandidate, d1_ok, reference_of
from nn_weight_writing.datasets.legal_rules import legal_holidays

R_TASK = "legal_r"
R_DATASET_VERSION = 1
R_ID_PREFIX = "jr-"
MIN_FAKES = 80
TRAIN_MIN_FAKES = 120
SESSION_PAIRS = 20
MAX_DAY_TRIES = 15  # jours interrogés au plus par fausse (le jour visé compris), S10
GATE_CLASSES = ("incoherent", "coherent_absent")
FORMATION_RULES = frozenset({"R-O1", "R-O2", "R-O4", "R-O5"})
FUTURE_RULE = "R-C3"
# Amendement A1 (Anaël, 2026-11-07) : l'appariement ne porte jamais sur le champ incohérent.
NUMBER_RULES = frozenset({"R-H1", "R-H2", "R-H3", "R-H4", "R-F1", "R-F2", "R-A1"})
DATE_RULES = frozenset({"R-C1", "R-C2", "R-C3", "R-C4"})
COHERENT_TYPE = "c00"
OTHER_TYPE = "x01"
REAL_TYPE = "real"
GAP_CLASSES = ("0", "1", "2", "3+", "none")
DAY_KINDS = ("ouvre", "samedi", "dimanche_ou_ferie")
SPLITS = {"session": ("s", 0), "train": ("t", 1), "eval": ("e", 2)}
EXCLUSIONS = (
    "not_in_gate",
    "ecli_only",
    "not_d1",
    "span_context",
    "before_window",
    "after_window_not_future",
    "future_not_visible",
    "raw_in_s",
    "number_repeated",
    "found_at_build",
    "recheck_unverifiable",
    "no_real_in_stratum",
)
_CC_NUMBER = re.compile(r"(\d{2})-\d{2}\.\d{3}")


class RBuildError(Exception):
    """Refus de construction : `code` lisible, `exit_code` 2 (garde) ou 3 (base injoignable)."""

    def __init__(self, code: str, detail: str, exit_code: int = 2) -> None:
        super().__init__(f"{code} : {detail}")
        self.code = code
        self.detail = detail
        self.exit_code = exit_code


# --- Fausses (D2) --------------------------------------------------------------------------


@dataclass(frozen=True)
class FakeRow:
    unit_id: str
    jurisdiction: str
    formation: str
    year: int
    month: int
    day: int
    number: str
    raw: str  # `canonical` du classement, jamais retouchée
    type_id: str
    rules: tuple[str, ...]
    nuss_types: tuple[str, ...]
    model: str  # modèle de la citation canonique
    klass: str  # "incoherent" ou "coherent_absent"
    class_conflict: bool = False
    partial_match: str | None = None

    @property
    def valid_date(self) -> date | None:
        try:
            return date(self.year, self.month, self.day)
        except ValueError:
            return None

    @property
    def future(self) -> bool:
        return FUTURE_RULE in self.rules

    @property
    def formation_exists(self) -> bool:
        return not set(self.rules) & FORMATION_RULES

    @property
    def match_gap(self) -> bool:
        """A1 : classe d'écart appariée sauf numéro incohérent ou non canonisable (`none`)."""
        return not set(self.rules) & NUMBER_RULES and (
            year_gap_class(self.jurisdiction, self.year, self.number) != "none"
        )

    @property
    def match_day_kind(self) -> bool:
        """A1 : type de jour apparié sauf date incohérente (impossible, future, t12)."""
        return not set(self.rules) & DATE_RULES and self.valid_date is not None


RealRow = RealCandidate  # une vraie retenue est une candidate tirée (D3)


@dataclass(frozen=True)
class Pair:
    fake: FakeRow
    real: RealCandidate
    notes: dict = field(default_factory=dict, compare=False, hash=False)


@dataclass
class Selection:
    fakes: list[FakeRow]
    excluded: dict[str, int]
    before_window: dict[str, int] = field(default_factory=dict)  # par juridiction


def type_of(rules: Iterable[str], nuss_types: Iterable[str]) -> str:
    """Plus petit type de Nuss des règles hors ECLI ; `x01` sans type ; `c00` sans règle."""
    rules = set(rules)
    if not rules:
        return COHERENT_TYPE
    kept = rules - ECLI_RULES
    if not kept:
        raise ValueError("règles ECLI seules : unité hors de p_d1, exclue en amont")
    types = sorted(t for t in nuss_types if any(BY_RULE[r].nuss == t for r in kept))
    return types[0] if types else OTHER_TYPE


def period_of(year: int, future: bool = False) -> str:
    if future:
        return "future"
    if year <= 2000:
        return "1989-2000"
    if year <= 2015:
        return "2001-2015"
    if year <= 2021:
        return "2016-2021"
    return "2022+"


def day_kind(day: date) -> str:
    """Type de jour (S6) : jour ouvré, samedi, ou dimanche et fête légale."""
    if day.weekday() == 6 or day in legal_holidays(day.year):
        return "dimanche_ou_ferie"
    if day.weekday() == 5:
        return "samedi"
    return "ouvre"


def year_gap_class(jurisdiction: str, year: int, number: str | None) -> str:
    """Écart année de la décision - année du pourvoi lue dans le numéro (S1).

    Classes `0`, `1`, `2`, `3+` ; `none` sans année dans le numéro (Conseil d'État, numéro hors
    motif). Un écart négatif (pourvoi après la décision, t01) va dans `0`, la classe la plus
    proche : l'incohérence elle-même n'est pas appariée.
    """
    match = _CC_NUMBER.fullmatch(number or "") if jurisdiction == "cc" else None
    if match is None:
        return "none"
    full = (year // 100) * 100 + int(match[1])
    if full > year + 10:
        full -= 100
    gap = year - full
    return "0" if gap <= 0 else "1" if gap == 1 else "2" if gap == 2 else "3+"


def raw_gap_class(raw: str) -> str:
    from nn_weight_writing.tasks.legal.reference import parse_reference

    ref = parse_reference(raw)
    return year_gap_class(ref.jurisdiction, ref.year, ref.number)


def _before(row: Mapping, window: CoverageWindow) -> bool:
    try:
        return date(row["year"], row["month"], row["day"]) < window.start
    except ValueError:
        return (row["year"], row["month"]) < (window.start.year, window.start.month)


def _after(fake: FakeRow, day: date) -> bool:
    """Date de la fausse postérieure à `day` (année et mois pour une date impossible)."""
    valid = fake.valid_date
    if valid is not None:
        return valid > day
    return (fake.year, fake.month) > (day.year, day.month)


def _canonical_citations(extraction: Iterable[Mapping]) -> dict[str, Mapping]:
    """Première ligne de chaque unité : citation canonique (ordre de D3 de 1-12)."""
    out: dict[str, Mapping] = {}
    for row in extraction:
        out.setdefault(row["unit_id"], row)
    return out


def recompute_canonical(row: Mapping, citation: Mapping | None) -> str | None:
    """Chaîne des fausses (CAP-11) : passage cité -> `fields_from_extracted` -> normaliseur."""
    if citation is None:
        return None
    key = (row["jurisdiction"], row["number"], (row["year"], row["month"], row["day"]))
    found = extract_references(citation["raw"])
    for extracted in found:
        ref, raw = reference_of(fields_from_extracted(extracted))
        if ref.key() == key:
            return raw
    # Juridiction héritée (extracteur du tour 1 de 1-12, `_inherit`) : l'ancre est hors du
    # passage enregistré ; seule une référence sans juridiction reçoit celle du classement.
    for extracted in found:
        if extracted.jurisdiction is None:
            inherited = replace(extracted, jurisdiction=row["jurisdiction"])
            ref, raw = reference_of(fields_from_extracted(inherited))
            if ref.key() == key:
                return raw
    return None


def _no_reference_in_span(row: Mapping, citation: Mapping) -> bool:
    """Aucune référence complète ne se relit dans le passage seul, même avec la juridiction
    héritée : ses champs ont été lus hors du passage enregistré (date avant l'ancre, bloc
    structuré du tour 1 de 1-12). Une référence complète de clé différente reste un écart du
    normaliseur (`normalizer_mismatch`)."""
    for extracted in extract_references(citation["raw"]):
        if extracted.jurisdiction is None:
            extracted = replace(extracted, jurisdiction=row["jurisdiction"])
        if reference_of(fields_from_extracted(extracted))[0].is_complete():
            return False
    return True


def select_fakes(
    classement: Sequence[Mapping],
    *,
    extraction: Iterable[Mapping],
    windows: Mapping[str, CoverageWindow],
    s_raws: frozenset[str] | set[str] = frozenset(),
    corpus_date: date | None = None,
) -> Selection:
    """Fausses admises (D2, S7) ; `RBuildError("normalizer_mismatch")` si le recalcul diffère.

    Avec `corpus_date` (S5), une fausse R-C3 (future à sa date de génération) dont la date n'est
    pas postérieure à `corpus_date` est exclue (`future_not_visible`) : la description de R date
    t06 par `corpus_date`, elle ne serait ni future ni vérifiée. Une fausse dont le numéro est
    celui d'une fausse déjà retenue (ordre des `unit_id`) est exclue (`number_repeated`) : aucun
    numéro n'est commun à deux jeux de R (D5).
    """
    citations = _canonical_citations(extraction)
    numbers: set[tuple[str, str]] = set()
    excluded = dict.fromkeys(EXCLUSIONS, 0)
    before: Counter = Counter()
    fakes: list[FakeRow] = []
    for row in sorted(classement, key=lambda r: r["unit_id"]):
        klass, rules = row["class"], frozenset(row["rules"])
        if klass not in GATE_CLASSES:
            excluded["not_in_gate"] += 1
            continue
        if klass == "incoherent" and rules <= ECLI_RULES:
            excluded["ecli_only"] += 1
            continue
        canonical = row["canonical"]
        if canonical is None or row["formation"] is None:
            excluded["not_d1"] += 1
            continue
        citation = citations.get(row["unit_id"])
        recomputed = recompute_canonical(row, citation)
        if recomputed is None and citation is not None and _no_reference_in_span(row, citation):
            excluded["span_context"] += 1  # rien n'est recalculable sans le texte de réponse
            continue
        if recomputed != canonical:
            raise RBuildError("normalizer_mismatch", f"{row['unit_id']} : canonical recalculée")
        if not d1_ok(canonical):
            excluded["not_d1"] += 1
            continue
        window = windows[row["jurisdiction"]]
        if _before(row, window):
            excluded["before_window"] += 1
            before[row["jurisdiction"]] += 1
            continue
        fake = FakeRow(
            unit_id=row["unit_id"],
            jurisdiction=row["jurisdiction"],
            formation=row["formation"],
            year=row["year"],
            month=row["month"],
            day=row["day"],
            number=row["number"],
            raw=canonical,
            type_id=type_of(rules, row["nuss_types"]),
            rules=tuple(sorted(rules)),
            nuss_types=tuple(row["nuss_types"]),
            model=row["citations"][0]["model"],
            klass=klass,
            class_conflict=bool(row.get("class_conflict")),
            partial_match=row.get("partial_match"),
        )
        valid = fake.valid_date
        if fake.future and corpus_date is not None and not _after(fake, corpus_date):
            excluded["future_not_visible"] += 1
            continue
        if valid is not None and valid > window.end and not fake.future:
            excluded["after_window_not_future"] += 1
            continue
        if canonical in s_raws:
            excluded["raw_in_s"] += 1
            continue
        if (fake.jurisdiction, fake.number) in numbers:
            excluded["number_repeated"] += 1
            continue
        numbers.add((fake.jurisdiction, fake.number))
        fakes.append(fake)
    return Selection(fakes, excluded, dict(sorted(before.items())))


# --- Revérification (D4) -------------------------------------------------------------------


def _as_ref(fake: FakeRow) -> NormalizedRef:
    return NormalizedRef(
        fake.jurisdiction, fake.formation, fake.day, fake.month, fake.year, fake.number, None
    )


def recheck_fakes(
    selection: Selection,
    *,
    client: JudilibreClient | None,
    ce_index: CeIndex | None,
    windows: Mapping[str, CoverageWindow],
    today: date,
) -> list[str]:
    """Retire de `selection` les fausses trouvées existantes ; rend leurs `unit_id`.

    Une date impossible ou future n'est pas interrogée. `api_error` ou erreur fatale de
    Judilibre : `RBuildError` (code 3), rien n'est écrit.
    """
    kept, found = [], []
    for fake in selection.fakes:
        valid = fake.valid_date
        window = windows[fake.jurisdiction]
        if valid is None or fake.future or window.position(valid) is not None:
            kept.append(fake)
            continue
        try:
            verdict = check_existence(
                _as_ref(fake), client=client, ce_index=ce_index, windows=dict(windows), today=today
            )
        except JudilibreError as error:
            raise RBuildError("api_error", str(error), exit_code=3) from error
        if verdict.status == "exists":
            found.append(fake.unit_id)
            selection.excluded["found_at_build"] += 1
        elif verdict.status == "unverifiable":
            if verdict.reason == "api_error":
                raise RBuildError("api_error", f"{fake.unit_id} : revérification", exit_code=3)
            selection.excluded["recheck_unverifiable"] += 1
        else:
            kept.append(fake)
    selection.fakes = kept
    return found


# --- Vraies appariées (D3, S1, S6, S10) ----------------------------------------------------

Pool = Callable[[str, date], list[RealCandidate]]


def _target_day(fake: FakeRow, year: int) -> date:
    last = calendar.monthrange(year, fake.month)[1]
    return date(year, fake.month, min(fake.day, last))


def _days_around(target: date, kind: str | None, low: date, high: date) -> list[date]:
    """Jour visé puis voisins de même type de jour (de tout type si `kind` est nul, A1), dans
    l'année et dans [low, high] (S10)."""
    out: list[date] = []
    first, last = max(low, date(target.year, 1, 1)), min(high, date(target.year, 12, 31))
    if first > last:
        return out
    start = min(max(target, first), last)
    for offset in range(0, 366):
        for day in (start + timedelta(offset), start - timedelta(offset)) if offset else (start,):
            if first <= day <= last and kind in (None, day_kind(day)) and day not in out:
                out.append(day)
                if len(out) == MAX_DAY_TRIES:
                    return out
    return out


def match_reals(
    fakes: Sequence[FakeRow],
    pool: Pool,
    *,
    seed: int,
    windows: Mapping[str, CoverageWindow],
    corpus_date: date,
    forbidden_raws: frozenset[str] | set[str] = frozenset(),
) -> tuple[list[Pair], list[str]]:
    """Une vraie par fausse (ordre des `unit_id`) ; rend les paires et les fausses sans vraie.

    Strate d'une fausse : juridiction, jour (le jour cité, sinon un voisin de même type de jour
    dans la même année), formation, classe d'écart d'année du numéro. Amendement A1 : un critère
    qui porte le champ incohérent de la fausse n'est pas apparié (type de jour pour une règle de
    date, formation pour une règle de formation, écart pour une règle de numéro ou un numéro
    `none`) ; l'année d'une fausse future est la plus proche dans la fenêtre. Tirage uniforme
    sans remise par `default_rng([seed, 0, i])`.
    """
    ordered = sorted(fakes, key=lambda f: f.unit_id)
    fake_numbers = {(f.jurisdiction, f.number) for f in ordered}
    used = set(forbidden_raws) | {f.raw for f in ordered}
    used_numbers: set[tuple[str, str]] = set()  # numéros des vraies déjà tirées (D5)
    pairs: list[Pair] = []
    unmatched: list[str] = []
    for i, fake in enumerate(ordered):
        rng = np.random.default_rng([seed, 0, i])
        window = windows[fake.jurisdiction]
        high = min(window.end, corpus_date)
        notes: dict = {}
        year = fake.year
        if year > high.year or year < window.start.year:
            year = min(max(year, window.start.year), high.year)  # année la plus proche (A1)
            notes["year_nearest"] = year
        kind = day_kind(fake.valid_date) if fake.match_day_kind else None
        target = _target_day(fake, year)
        formation = fake.formation if fake.formation_exists else None
        gap = year_gap_class(fake.jurisdiction, fake.year, fake.number) if fake.match_gap else None
        free = {"day_kind": kind is None, "formation": formation is None, "year_gap": gap is None}
        notes["unmatched_criteria"] = [name for name, is_free in free.items() if is_free]
        chosen = None
        for day in _days_around(target, kind, window.start, high):
            candidates = sorted(
                (
                    c
                    for c in pool(fake.jurisdiction, day)
                    if (formation is None or c.formation == formation)
                    and (gap is None or year_gap_class(c.jurisdiction, c.day.year, c.number) == gap)
                    and c.raw not in used
                    and not any((c.jurisdiction, n) in fake_numbers for n in c.numbers)
                    and not any((c.jurisdiction, n) in used_numbers for n in c.numbers)
                ),
                key=lambda c: (c.raw, c.source_id),
            )
            if candidates:
                chosen = candidates[int(rng.integers(len(candidates)))]
                notes["day_offset"] = (day - target).days
                break
        if chosen is None:
            unmatched.append(fake.unit_id)
            continue
        if chosen.day > corpus_date:
            raise RBuildError("real_after_corpus_date", f"{chosen.source_id} : {chosen.day}")
        used.add(chosen.raw)
        used_numbers.update((chosen.jurisdiction, n) for n in chosen.numbers)
        pairs.append(Pair(fake, chosen, notes))
    return pairs, unmatched


# --- Découpage (D5) ------------------------------------------------------------------------


def _stratum(pair: Pair) -> tuple[str, str, str]:
    fake = pair.fake
    visible = COHERENT_TYPE if fake.type_id == COHERENT_TYPE else "incoherent"
    return (fake.jurisdiction, visible, period_of(fake.year, fake.future))


def split_sizes(n_fakes: int) -> dict[str, int]:
    """Paires par jeu (D5) ; `RBuildError("too_few_fakes")` sous `MIN_FAKES`."""
    if n_fakes < MIN_FAKES:
        raise RBuildError("too_few_fakes", f"{n_fakes} fausses retenues (< {MIN_FAKES})")
    rest = n_fakes - SESSION_PAIRS
    train = rest // 2 if n_fakes >= TRAIN_MIN_FAKES else 0
    return {"session": SESSION_PAIRS, "train": train, "eval": rest - train}


def split_pairs(pairs: Sequence[Pair], *, seed: int) -> dict[str, list[Pair]]:
    """Par paire et par strate (juridiction × classe visible × période).

    Séance : 20 paires réparties entre strates au prorata (plus forts restes, ordre des strates
    en cas d'égalité) ; dans chaque strate, ordre tiré par `default_rng([seed, 1])`, les premières
    paires vont en séance, les suivantes alternent réservé et entraînement (alternance continue
    d'une strate à l'autre, réservé d'abord) : même composition à une paire près par strate.
    """
    sizes = split_sizes(len(pairs))
    strata: dict[tuple, list[Pair]] = {}
    for pair in sorted(pairs, key=lambda p: p.fake.unit_id):
        strata.setdefault(_stratum(pair), []).append(pair)
    keys = sorted(strata)
    total = len(pairs)
    exact = {k: SESSION_PAIRS * len(strata[k]) / total for k in keys}
    quota = {k: int(exact[k]) for k in keys}
    by_remainder = sorted(keys, key=lambda k: (-(exact[k] - quota[k]), keys.index(k)))
    for k in by_remainder[: SESSION_PAIRS - sum(quota.values())]:
        quota[k] += 1
    rng = np.random.default_rng([seed, 1])
    out: dict[str, list[Pair]] = {"session": [], "train": [], "eval": []}
    to_eval = True
    for k in keys:
        members = strata[k]
        order = [members[j] for j in rng.permutation(len(members))]
        out["session"].extend(order[: quota[k]])
        for pair in order[quota[k] :]:
            if sizes["train"] == 0 or to_eval:
                out["eval"].append(pair)
            else:
                out["train"].append(pair)
            to_eval = not to_eval if sizes["train"] else True
    assert {s: len(v) for s, v in out.items()} == sizes
    return out


# --- Écriture (D5, S12) --------------------------------------------------------------------


@dataclass(frozen=True)
class Example:
    id: str
    raw: str
    label: str  # "real" ou "fake"
    type_id: str
    source: dict


def _fake_source(fake: FakeRow) -> dict:
    return {
        "class": "fake",
        "source": f"slm:{fake.model}",
        "unit_id": fake.unit_id,
        "rules": list(fake.rules),
        "nuss_types": list(fake.nuss_types),
        "class_conflict": fake.class_conflict,
    }


def _real_source(real: RealCandidate, extracted_at: str) -> dict:
    return {
        "class": "real",
        "source": real.source,
        "source_id": real.source_id,
        "update_date": real.update_date,
        "extracted_at": extracted_at,
        "origin": dict(real.origin),
    }


def examples_of(pairs: Sequence[Pair], *, split: str, seed: int, extracted_at: dict) -> list:
    """Exemples mélangés par `default_rng([seed, 2, k])`, identifiants `jr-<s|t|e>NNNNN`."""
    letter, k = SPLITS[split]
    rows = []
    for pair in pairs:
        rows.append(("fake", pair.fake.raw, pair.fake.type_id, _fake_source(pair.fake)))
        real = pair.real
        rows.append(("real", real.raw, REAL_TYPE, _real_source(real, extracted_at[real.source])))
    order = np.random.default_rng([seed, 2, k]).permutation(len(rows))
    out = []
    for rank, j in enumerate(order, start=1):
        label, raw, type_id, source = rows[j]
        out.append(Example(f"{R_ID_PREFIX}{letter}{rank:05d}", raw, label, type_id, source))
    return out


def composition_counts(pairs: Sequence[Pair]) -> dict:
    fakes = [p.fake for p in pairs]
    reals = [p.real for p in pairs]
    incoherent = sum(1 for f in fakes if f.type_id != COHERENT_TYPE)

    def per_class(fake_values, real_values) -> dict:
        return {
            "fake": dict(sorted(Counter(fake_values).items())),
            "real": dict(sorted(Counter(real_values).items())),
        }

    return {
        "n": 2 * len(pairs),
        "pairs": len(pairs),
        "by_class": {"real": len(reals), "fake": len(fakes)},
        "by_jurisdiction": per_class(
            (f.jurisdiction for f in fakes), (r.jurisdiction for r in reals)
        ),
        "by_formation": per_class((f.formation for f in fakes), (r.formation for r in reals)),
        "by_period": per_class(
            (period_of(f.year, f.future) for f in fakes), (period_of(r.day.year) for r in reals)
        ),
        "by_type": dict(sorted(Counter(f.type_id for f in fakes).items())),
        "by_model_family": dict(sorted(Counter(family_of(f.model) for f in fakes).items())),
        "year_gap": per_class(
            (year_gap_class(f.jurisdiction, f.year, f.number) for f in fakes),
            (year_gap_class(r.jurisdiction, r.day.year, r.number) for r in reals),
        ),
        "day_kind": per_class(
            (day_kind(f.valid_date) if f.valid_date else "impossible" for f in fakes),
            (day_kind(r.day) for r in reals),
        ),
        "p_R": incoherent / len(fakes) if fakes else None,
    }


def write_r_dataset(
    directory: Path,
    pairs: Sequence[Pair],
    *,
    split: str,
    meta: Mapping,
    seed: int = 0,
) -> Path:
    """Un jeu de R au format d'AD-16, plus `sources.jsonl` (mêmes `id`, condition 3)."""
    examples = examples_of(pairs, split=split, seed=seed, extracted_at=meta["extraction_dates"])
    sources = "".join(
        json.dumps({"id": e.id, **e.source}, ensure_ascii=False) + "\n" for e in examples
    ).encode("utf-8")
    composition = {
        **meta,
        "task": R_TASK,
        "split": split,
        "seed": seed,
        **composition_counts(pairs),
    }
    return write_dataset(
        directory,
        [Row(e.id, e.raw, e.label, e.type_id) for e in examples],
        generator=R_TASK,
        version=R_DATASET_VERSION,
        seed=seed,
        composition=composition,
        extra_files={"sources.jsonl": sources},
    )
