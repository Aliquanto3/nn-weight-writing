"""Générateur des jeux S et S-réservé (CAP-9, AD-16, story 1-9).

Cinq jeux tirés par graine, chacun sur son propre flux `default_rng([seed, k])`. Chaque ligne est
contrôlée par le vérificateur de règles (`legal_rules.violations`) : une vraie ne viole rien, une
fausse exactement son type ; sinon, ou si `raw` existe déjà dans un jeu précédent, elle est retirée.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from nn_weight_writing.datasets.io import Row, write_dataset
from nn_weight_writing.datasets.legal_rules import (
    easter,
    is_working_day,
    legal_holidays,
    violations,
)
from nn_weight_writing.tasks.legal import TASK_S, TASK_S_RESERVED
from nn_weight_writing.tasks.legal.facts import Facts, facts_sha256, load_facts
from nn_weight_writing.tasks.legal.reference import (
    Reference,
    format_reference,
    parse_reference,
)
from nn_weight_writing.tasks.legal.types import BY_ID, HELD_OUT, KNOWN, TYPES

GENERATOR = "legal"
GENERATOR_VERSION = 1
JURISDICTIONS = ("cc", "ce", "ca")
MAX_RETRIES = 1000
IMPOSSIBLE_DAYS = ((2, 30), (2, 31), (4, 31), (6, 31), (9, 31), (11, 31))
KEYS = ("eval", "s_session", "s_train", "r_session", "r_train")


@dataclass(frozen=True)
class Sizes:
    eval: int = 4000
    session: int = 40
    train: int = 8192

    def validate(self) -> None:
        for name in ("eval", "session", "train"):
            value = getattr(self, name)
            if value < 2 or value % 2:
                raise ValueError(f"taille {name} = {value} : paire et au moins 2 attendue")


# --- Calendrier --------------------------------------------------------------------------


@dataclass(frozen=True)
class Calendar:
    window_days: tuple[date, ...]  # jours ouvrés de la fenêtre
    future_days: tuple[date, ...]
    chamber_era_days: tuple[date, ...]  # jours ouvrés jusqu'à la fin des sous-sections
    subsection_era_days: tuple[date, ...]  # jours ouvrés depuis le retour des chambres
    sundays: tuple[date, ...]
    mobile_holidays: tuple[date, ...]  # lundi de Pâques et Ascension de la fenêtre (O3)


def _days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def build_calendar(facts: Facts) -> Calendar:
    window = _days(facts.window_start, facts.window_end)
    working = [d for d in window if is_working_day(d, facts)]
    future = [d for d in _days(facts.future_start, facts.future_end) if is_working_day(d, facts)]
    cut = bisect.bisect_right(working, facts.subsection_until)
    since = bisect.bisect_left(working, facts.chamber_from)
    mobile_names = [n for n in facts.easter_offsets if n not in facts.t12_excluded]
    mobile = sorted(
        d
        for year in range(facts.window_start.year, facts.window_end.year + 1)
        for d, name in legal_holidays(year, facts).items()
        if name in mobile_names and facts.window_start <= d <= facts.window_end
    )
    assert all(easter(d.year) < d for d in mobile)
    return Calendar(
        tuple(working),
        tuple(future),
        tuple(working[:cut]),
        tuple(working[since:]),
        tuple(d for d in window if d.weekday() == 6),
        tuple(mobile),
    )


# --- Tirages ------------------------------------------------------------------------------


def _pick(rng, items):
    return items[int(rng.integers(len(items)))]


def _weighted(rng, weights) -> int:
    w = np.asarray(list(weights), dtype=float)
    return int(rng.choice(len(w), p=w / w.sum()))


def _between(rng, low_high: tuple[int, int]) -> int:
    return int(rng.integers(low_high[0], low_high[1] + 1))


def _rank(k: int) -> str:
    return f"{k}{'re' if k == 1 else 'e'}"


def _aa(year: int) -> str:
    return f"{year % 100:02d}"


def _cc_number(year: int, serial: int) -> str:
    return f"{_aa(year)}-{serial // 1000:02d}.{serial % 1000:03d}"


def _number(rng, f: Facts, jurisdiction: str, year: int, *, criminal: bool = False) -> str:
    if jurisdiction == "cc":
        gap = _weighted(rng, f.cc_gap_weights)
        serial = _between(rng, f.criminal_serial if criminal else f.civil_serial)
        return _cc_number(year - gap, serial)
    if jurisdiction == "ce":
        return str(_between(rng, f.ce_number_range))
    gap = _weighted(rng, f.ca_gap_weights)
    return f"{_aa(year - gap)}/{_between(rng, f.ca_serial):05d}"


def _ce_formation(rng, f: Facts, day: date) -> str:
    if f.subsection_until < day < f.chamber_from:  # zone grise : aucune formation numérotée
        return f.ce_assembly if int(rng.integers(7)) < 2 else f.ce_section
    kinds = list(f.ce_formation_weights)
    kind = kinds[_weighted(rng, f.ce_formation_weights.values())]
    if kind == "assembly":
        return f.ce_assembly
    if kind == "section":
        return f.ce_section
    k = int(rng.integers(1, f.ce_numbered_max + 1))
    return f"{_rank(k)} {'sous-sect.' if day <= f.subsection_until else 'ch.'}"


def draw_real(rng, f: Facts, cal: Calendar, jurisdiction: str, day: date | None = None):
    """Une référence vraie de la juridiction ; la date est tirée si elle n'est pas donnée."""
    day = day or _pick(rng, cal.window_days)
    if jurisdiction == "cc":
        chambers = list(f.chamber_weights)
        chamber = chambers[_weighted(rng, f.chamber_weights.values())]
        number = _number(rng, f, "cc", day.year, criminal=chamber in f.criminal)
        formation = chamber
    elif jurisdiction == "ce":
        formation = _ce_formation(rng, f, day)
        number = _number(rng, f, "ce", day.year)
    else:
        seats = [s for s in f.all_seats if s not in f.seats_excluded_from_real]
        formation = _pick(rng, seats)
        number = _number(rng, f, "ca", day.year)
    return Reference(jurisdiction, formation, day.day, day.month, day.year, number)


def _malformed(rng, jurisdiction: str, number: str) -> str:
    digit = str(int(rng.integers(10)))
    variants = {
        "cc": (
            number.replace(".", ""),
            number.replace("-", ""),
            number + digit,
            number[1:],
        ),
        "ce": (number[:-1], number + digit, number[:3] + "." + number[3:]),
        "ca": (number.replace("/", ""), number + digit, number.replace("/", "-")),
    }[jurisdiction]
    return _pick(rng, variants)


def _with_year_offset(ref: Reference, years_before: int) -> Reference:
    """Remplace AA par l'année de la décision moins `years_before` (négatif : après)."""
    return replace(ref, number=_aa(ref.year - years_before) + ref.number[2:])


def draw_fake(rng, f: Facts, cal: Calendar, type_id: str, jurisdiction: str) -> Reference:
    """Une référence qui doit violer `type_id` seulement (le contrôle est fait par l'appelant)."""
    if type_id == "t06":
        return draw_real(rng, f, cal, jurisdiction, _pick(rng, cal.future_days))
    if type_id == "t07":
        if int(rng.integers(2)):
            day = _pick(rng, cal.chamber_era_days)
            formation = f"{_rank(int(rng.integers(1, f.ce_numbered_max + 1)))} ch."
        else:
            day = _pick(rng, cal.subsection_era_days)
            formation = f"{_rank(int(rng.integers(1, f.ce_numbered_max + 1)))} sous-sect."
        return replace(draw_real(rng, f, cal, "ce", day), formation=formation)
    if type_id == "t12":
        day = _pick(rng, cal.sundays if int(rng.integers(2)) == 0 else cal.mobile_holidays)
        return draw_real(rng, f, cal, jurisdiction, day)
    if type_id == "t15":
        years = [y for y in range(2001, 2027) if y % 4 or (y % 100 == 0 and y % 400)]
        year = _pick(rng, years)
        base = draw_real(rng, f, cal, jurisdiction, date(year, 2, 28))
        return replace(base, day=29)
    ref = draw_real(rng, f, cal, jurisdiction)
    if type_id == "t01":
        return _with_year_offset(ref, -_between(rng, f.cc_after_gap))
    if type_id == "t02":
        month, day = _pick(rng, IMPOSSIBLE_DAYS)
        return replace(ref, month=month, day=day)
    if type_id == "t03":
        return replace(ref, formation=_pick(rng, f.nonexistent))
    if type_id == "t04":
        return replace(ref, formation=_pick(rng, f.fake_seats))
    if type_id == "t05":
        if jurisdiction == "cc":
            pool = [f.ce_assembly, f.ce_section]
            pool += [f"{_rank(k)} ch." for k in range(1, f.ce_numbered_max + 1)]
        else:
            pool = list(f.chambers)
        return replace(ref, formation=_pick(rng, pool))
    if type_id == "t08":
        return _with_year_offset(ref, _between(rng, f.cc_old_gap))
    if type_id == "t09":
        return _with_year_offset(ref, -_between(rng, f.ca_after_gap))
    if type_id == "t10":
        return replace(ref, number=_malformed(rng, jurisdiction, ref.number))
    if type_id == "t11":
        other = _pick(rng, [j for j in JURISDICTIONS if j != jurisdiction])
        return replace(ref, number=_number(rng, f, other, ref.year))
    if type_id == "t13":
        return _with_year_offset(ref, _between(rng, f.ca_old_gap))
    if type_id == "t14":
        chamber = _pick(rng, [*f.civil, *f.criminal])
        low_high = f.civil_serial if chamber in f.criminal else f.criminal_serial
        serial = _between(rng, low_high)
        number = ref.number[:3] + f"{serial // 1000:02d}.{serial % 1000:03d}"
        return replace(ref, formation=chamber, number=number)
    raise ValueError(f"type inconnu : {type_id}")


# --- Proportions --------------------------------------------------------------------------


def _largest_remainder(quota: int, weights: list[int]) -> list[int]:
    """Répartit `quota` au plus fort reste ; égalités dans l'ordre des indices."""
    total = sum(weights)
    if total == 0:
        weights, total = [1] * len(weights), len(weights)
    shares = [quota * w // total for w in weights]
    remainders = [quota * w % total for w in weights]
    order = sorted(range(len(weights)), key=lambda i: -remainders[i])
    for i in order[: quota - sum(shares)]:
        shares[i] += 1
    return shares


def allocate(n: int, type_ids: tuple[str, ...]) -> list[tuple[str, str, int]]:
    """(type, juridiction, nombre) des n/2 fausses d'un jeu, sans aléa (D6)."""
    n_fake = n // 2
    base, extra = divmod(n_fake, len(type_ids))
    quota = {tid: base + (i < extra) for i, tid in enumerate(type_ids)}
    third, rest = divmod(n_fake, 3)
    target = {"cc": third + (rest > 0), "ce": third + (rest > 1), "ca": third}
    got = dict.fromkeys(JURISDICTIONS, 0)
    plan: dict[tuple[str, str], int] = {}

    def add(tid: str, jurisdiction: str, count: int) -> None:
        if count:
            plan[(tid, jurisdiction)] = count
            got[jurisdiction] += count

    for tid in type_ids:
        if len(BY_ID[tid].jurisdictions) == 1:
            add(tid, BY_ID[tid].jurisdictions[0], quota[tid])
    for tid in type_ids:
        if BY_ID[tid].jurisdictions == ("cc", "ce"):
            add(tid, "cc", (quota[tid] + 1) // 2)
            add(tid, "ce", quota[tid] // 2)
    for tid in type_ids:
        if len(BY_ID[tid].jurisdictions) == 3:
            deficits = [max(target[j] - got[j], 0) for j in JURISDICTIONS]
            shares = _largest_remainder(quota[tid], deficits)
            for jurisdiction, share in zip(JURISDICTIONS, shares, strict=True):
                add(tid, jurisdiction, share)
    order = {tid: i for i, tid in enumerate(type_ids)}
    return [
        (tid, j, plan[(tid, j)])
        for tid, j in sorted(plan, key=lambda k: (order[k[0]], JURISDICTIONS.index(k[1])))
    ]


# --- Jeux ---------------------------------------------------------------------------------


def _draw_line(rng, f, cal, type_id, jurisdiction, seen: set[str]) -> str:
    expected = frozenset() if type_id == "real" else frozenset({type_id})
    for _ in range(MAX_RETRIES):
        if type_id == "real":
            ref = draw_real(rng, f, cal, jurisdiction)
        else:
            ref = draw_fake(rng, f, cal, type_id, jurisdiction)
        raw = format_reference(ref)
        if raw in seen or violations(ref, f) != expected:
            continue
        seen.add(raw)
        return raw
    raise RuntimeError(
        f"{type_id}/{jurisdiction} : aucune référence valide en {MAX_RETRIES} essais"
    )


def draw_set(
    seed: int, k: int, n: int, type_ids: tuple[str, ...], prefix: str, seen: set[str], f, cal
) -> list[Row]:
    rng = np.random.default_rng([seed, k])
    plan = allocate(n, type_ids)
    per_jurisdiction = dict.fromkeys(JURISDICTIONS, 0)
    for _, jurisdiction, count in plan:
        per_jurisdiction[jurisdiction] += count
    lines: list[tuple[str, str]] = []
    for jurisdiction in JURISDICTIONS:
        for _ in range(per_jurisdiction[jurisdiction]):
            lines.append((_draw_line(rng, f, cal, "real", jurisdiction, seen), "real"))
    for tid, jurisdiction, count in plan:
        for _ in range(count):
            lines.append((_draw_line(rng, f, cal, tid, jurisdiction, seen), tid))
    shuffled = [lines[int(i)] for i in rng.permutation(len(lines))]
    return [
        Row(
            f"legal-{prefix}{i:05d}",
            raw,
            "real" if tid == "real" else "fake",
            tid,
        )
        for i, (raw, tid) in enumerate(shuffled, start=1)
    ]


def generate_rows(seed: int, sizes: Sizes | None = None) -> dict[str, list[Row]]:
    """Les cinq jeux tirés, dans l'ordre de D6, sans `raw` commun entre eux."""
    sizes = sizes or Sizes()
    sizes.validate()
    f = load_facts()
    cal = build_calendar(f)
    everything = tuple(t.id for t in TYPES)
    seen: set[str] = set()
    plan = (
        ("eval", 0, sizes.eval, everything, "e"),
        ("s_session", 1, sizes.session, everything, "s"),
        ("s_train", 2, sizes.train, everything, "t"),
        ("r_session", 3, sizes.session, KNOWN, "r"),
        ("r_train", 4, sizes.train, KNOWN, "u"),
    )
    return {key: draw_set(seed, k, n, ids, prefix, seen, f, cal) for key, k, n, ids, prefix in plan}


def composition(rows: list[Row], task, split: str, f: Facts | None = None) -> dict:
    """Contenu de la clé `composition` de `dataset.json` (D6)."""
    f = f or load_facts()
    by_type = {t.id: 0 for t in TYPES}
    by_jurisdiction = {
        "real": dict.fromkeys(JURISDICTIONS, 0),
        "fake": dict.fromkeys(JURISDICTIONS, 0),
    }
    for row in rows:
        if row.label == "fake":
            by_type[row.type_id] += 1
        by_jurisdiction[row.label][parse_reference(row.raw).jurisdiction] += 1
    return {
        "task": task.name,
        "split": split,
        "encoder": task.encoder_id,
        "corpus_date": f.corpus_date.isoformat(),
        "window": [f.window_start.isoformat(), f.window_end.isoformat()],
        "facts_sha256": facts_sha256(),
        "n_real": sum(1 for r in rows if r.label == "real"),
        "n_fake": sum(1 for r in rows if r.label == "fake"),
        "by_type": by_type,
        "by_jurisdiction": by_jurisdiction,
        "types": [
            {
                "id": t.id,
                "name": t.name,
                "status": t.status,
                "jurisdictions": list(t.jurisdictions),
                "nuss": t.nuss,
            }
            for t in TYPES
        ],
        "visible_types": [entry["id"] for entry in task.vocabulary],
        "held_out_types": list(HELD_OUT) if task is TASK_S_RESERVED else [],
    }


def targets(root: Path) -> dict[str, Path]:
    return {
        "eval": root / "heldout" / "legal_s" / "eval",
        "r_eval": root / "heldout" / "legal_s_reserved" / "eval",
        "s_session": root / "data" / "legal_s" / "session",
        "s_train": root / "data" / "legal_s" / "train",
        "r_session": root / "data" / "legal_s_reserved" / "session",
        "r_train": root / "data" / "legal_s_reserved" / "train",
    }


def generate(*, seed: int, root: Path, sizes: Sizes | None = None) -> list[Path]:
    """Écrit les six dossiers de D6 sous `root` ; refuse, avant d'écrire, si l'un existe."""
    paths = targets(Path(root))
    for path in paths.values():
        if path.exists() and any(path.iterdir()):
            raise FileExistsError(f"jeu déjà présent : {path}")
    rows = generate_rows(seed, sizes)
    plan = (
        ("eval", rows["eval"], TASK_S, "eval"),
        ("r_eval", rows["eval"], TASK_S_RESERVED, "eval"),
        ("s_session", rows["s_session"], TASK_S, "session"),
        ("s_train", rows["s_train"], TASK_S, "train"),
        ("r_session", rows["r_session"], TASK_S_RESERVED, "session"),
        ("r_train", rows["r_train"], TASK_S_RESERVED, "train"),
    )
    f = load_facts()
    return [
        write_dataset(
            paths[key],
            data,
            generator=GENERATOR,
            version=GENERATOR_VERSION,
            seed=seed,
            composition=composition(data, task, split, f),
        )
        for key, data, task, split in plan
    ]
