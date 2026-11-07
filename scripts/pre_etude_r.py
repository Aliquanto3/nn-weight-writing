"""Pré-étude R et porte des 30 % (story 1-12).

Sous-commandes :
    mesurer-base   phase A : faits de R mesurés sur la base réelle seule (r_facts.toml)
    classer        phase B : classement de la collecte figée, sans aucune part (P1)
    echantillons   phase B : tirages du contrôle de qualité (D7)
    porte          phase B : parts, intervalle et décision, après le verdict du contrôle (P1)

Exemples :
    uv run python scripts/pre_etude_r.py mesurer-base
    uv run python scripts/pre_etude_r.py classer --collecte ../data/r/collecte \
        --manifeste-sha256 <hex> --grille-figee <sha>
    uv run python scripts/pre_etude_r.py echantillons --collecte ... --manifeste-sha256 <hex>
    uv run python scripts/pre_etude_r.py porte --verdict data/r/pre_etude/controle.json

La clé Judilibre est lue dans l'environnement, sinon dans la ligne `JUDILIBRE_KEY_ID=` de
`--env-file` (défaut : `.env` du dépôt principal), chargée dans `os.environ` du processus pour
que `redact()` la masque dans tout ce qui est écrit (P9). Elle n'est jamais affichée.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np

from nn_weight_writing.datasets.legal_r.ce_index import CeIndex
from nn_weight_writing.datasets.legal_r.classify import (
    Unit,
    build_units,
    citation_from,
    classify_unit,
    read_classement,
    write_classement,
    write_extraction,
)
from nn_weight_writing.datasets.legal_r.existence import (
    CoverageWindow,
    check_existence,
    coverage_windows,
)
from nn_weight_writing.datasets.legal_r.extract import extract_references
from nn_weight_writing.datasets.legal_r.frozen import CollectionError, read_collection
from nn_weight_writing.datasets.legal_r.gate import (
    THRESHOLD,
    dominant_family,
    family_of,
    family_shares,
    gate,
    leave_one_out,
    maybe_gate,
)
from nn_weight_writing.datasets.legal_r.grid import (
    ECLI_RULES,
    ECLI_STRUCTURE,
    GRID_VERSION,
    incoherences,
)
from nn_weight_writing.datasets.legal_r.judilibre import (
    KEY_ENV,
    JudilibreClient,
    JudilibreError,
    key_from_env,
)
from nn_weight_writing.datasets.legal_r.normalize import (
    NORMALIZER_ID,
    fields_from_ce_opendata,
    fields_from_extracted,
    fields_from_judilibre,
    normalize,
)
from nn_weight_writing.datasets.legal_r.r_facts import (
    R_FACTS_PATH,
    RFacts,
    load_r_facts,
    load_seat_tables,
    r_facts_sha256,
)
from nn_weight_writing.journal.writer import redact
from nn_weight_writing.tasks.legal.facts import facts_sha256, load_facts

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "r"
PRE = DATA / "pre_etude"
CACHE = DATA / "cache" / "judilibre"
CE_INDEX = DATA / "ce_index" / "index.jsonl"
R_GATE = ROOT / "config" / "r_gate.toml"
SPEC = ROOT / "_bmad-output" / "implementation-artifacts" / "stories" / "1-12-pre-etude-r.md"
# Ordre fixe des modèles de 1-12a (scripts/collecte_hallucinations.py, MODELES).
MODELES = (
    "qwen3.5:0.8b",
    "qwen3.5:2b",
    "qwen3.5:4b",
    "gemma4:e2b-it-qat",
    "gemma4:e4b-it-qat",
    "ministral-3:3b",
    "phi4-mini:3.8b",
    "granite4.2:3b",
    "lfm3:1.7b-q4_K_M",
    "nemotron-3-nano:4b",
)
FAMILIES = (
    "qwen3.5",
    "gemma4",
    "ministral-3",
    "phi4-mini",
    "granite4.2",
    "lfm3",
    "nemotron-3-nano",
)
CC_YEARS = (2005, 2012, 2019, 2024)
CA_YEARS = (2023, 2025)
PER_MONTH = 84  # 12 lots mensuels de 84 : 1 008 décisions par année (écart consigné)
SPECIFICITY_MAX = 0.005
ADOPTION_MIN = 0.99
RECALL_DRAWN = 60
RECALL_MIN = 57
RECALL_SEED = [0, 5]
API_ERROR_MAX = 0.01
QC_SIZES = {1: 60, 2: 20, 3: (30, 10), 4: 30}
VERDICTS = {"accepte", "echec"}


# --- Outils communs ------------------------------------------------------------------------


def main_repo_env() -> Path:
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return (Path(common).parent if common else ROOT) / ".env"


def load_key(env_file: Path | None) -> str:
    """Clé de l'environnement, sinon de la ligne `JUDILIBRE_KEY_ID=` de `env_file` (P9)."""
    if not os.environ.get(KEY_ENV) and env_file is not None and Path(env_file).is_file():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{KEY_ENV}="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    os.environ[KEY_ENV] = value
                break
    return key_from_env()


def write_text(path: Path, text: str) -> None:
    """Toute écriture du script passe par `redact()` (la clé est dans `os.environ`, P9)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(text), encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    ).stdout.strip()


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# Transport HTTP de Judilibre : None = urllib ; remplacé par les tests (frontière réseau).
FETCH = None


def make_client(args) -> JudilibreClient:
    key = load_key(args.env_file)
    return JudilibreClient(
        key, fetch=FETCH, cache_dir=args.cache, refresh=args.rafraichir, log=print
    )


def windows_from(r_facts: RFacts) -> dict[str, CoverageWindow]:
    return {
        j: CoverageWindow(j, start, end, "r_facts.toml")
        for j, (start, end) in r_facts.coverage.items()
    }


def fmt(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


# --- TOML minimal ----------------------------------------------------------------------------


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(round(value, 6))
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    if isinstance(value, dict):
        inner = ", ".join(f"{json.dumps(str(k))} = {_toml_value(v)}" for k, v in value.items())
        return "{ " + inner + " }" if inner else "{}"
    raise TypeError(f"valeur TOML non gérée : {value!r}")


def toml_table(name: str, values: dict) -> str:
    lines = [f"[{name}]"]
    lines += [f"{k} = {_toml_value(v)}" for k, v in values.items()]
    return "\n".join(lines) + "\n"


# --- mesurer-base (phase A) ----------------------------------------------------------------


def _month_lot(client: JudilibreClient, jurisdiction: str, year: int, month: int) -> list[dict]:
    end_day = (date(year + (month == 12), month % 12 + 1, 1).toordinal()) - 1
    params = {
        "jurisdiction": jurisdiction,
        "date_start": f"{year}-{month:02d}-01",
        "date_end": date.fromordinal(end_day).isoformat(),
        "date_type": "creation",
        "abridged": "true",
        "batch_size": PER_MONTH,
    }
    if jurisdiction == "ca":
        params["type"] = "arret"
    return client.get("/scan", params)["results"]


def _ecli_facts(samples: dict[str, list], ce_records: list[dict]) -> dict:
    """Faits ECLI mesurés (R-E2, R-E4, R-E5) sur les références réelles qui portent un ECLI."""
    codes: dict[str, Counter] = {j: Counter() for j in ("cc", "ca", "ce")}
    for j in ("cc", "ca"):
        for meta in samples[j]:
            ecli = (meta.get("ecli") or "").upper()
            if ECLI_STRUCTURE.fullmatch(ecli):
                codes[j][ecli.split(":")[2]] += 1
    ce_ok = ce_total = 0
    for record in ce_records:
        ecli = (record.get("Numero_ECLI") or "").upper()
        if not ECLI_STRUCTURE.fullmatch(ecli):
            continue
        codes["ce"][ecli.split(":")[2]] += 1
        ref = normalize(fields_from_ce_opendata(record))
        if ref.number and ref.has_date():
            ce_total += 1
            expected = f"{ref.number}.{ref.year:04d}{ref.month:02d}{ref.day:02d}"
            ce_ok += ecli.split(":")[4] == expected
    owners: dict[str, set[str]] = defaultdict(set)
    for j, counter in codes.items():
        for code in counter:
            owners[code].add(j)
    total = sum(sum(c.values()) for c in codes.values())
    unique = sum(n for j, c in codes.items() for code, n in c.items() if owners[code] == {j})
    # R-E5 : chambres exemptées de la règle de série (ch. mixte, ass. plén.) hors de la table,
    # puisqu'elles jugent des pourvois civils comme pénaux (facts.toml, series_exempt).
    exempt = set(load_facts().series_exempt)
    prefixes: dict[str, Counter] = defaultdict(Counter)
    for meta in samples["cc"]:
        ecli = (meta.get("ecli") or "").upper()
        ref = normalize(fields_from_judilibre(meta))
        if ECLI_STRUCTURE.fullmatch(ecli) and ref.formation and ref.formation not in exempt:
            prefixes[ref.formation][ecli.split(":")[4][:2]] += 1
    prefix_owner: dict[str, set[str]] = defaultdict(set)
    for chamber, counter in prefixes.items():
        for prefix in counter:
            prefix_owner[prefix].add(chamber)
    cc_total = sum(sum(c.values()) for c in prefixes.values())
    cc_unique = sum(
        n for ch, c in prefixes.items() for p, n in c.items() if prefix_owner[p] == {ch}
    )
    share = {
        "R-E2": unique / total if total else 0.0,
        "R-E4": ce_ok / ce_total if ce_total else 0.0,
        "R-E5": cc_unique / cc_total if cc_total else 0.0,
    }
    return {
        "codes": {j: dict(sorted(c.items())) for j, c in codes.items()},
        "cc_prefixes": {ch: dict(sorted(c.items())) for ch, c in sorted(prefixes.items())},
        "share": share,
        "n": {"R-E2": total, "R-E4": ce_total, "R-E5": cc_total},
        "adopted": {rule: value >= ADOPTION_MIN for rule, value in share.items()},
    }


def _provisional_r_facts(ecli: dict, windows: dict[str, CoverageWindow]) -> RFacts:
    aliases, codes = load_seat_tables()
    adopted = ecli["adopted"]
    disabled: dict[str, frozenset[str]] = {}
    for j in ("cc", "ce", "ca"):
        off = {r for r in ("R-E2", "R-E5") if not adopted[r]}
        if j == "ce" and not adopted["R-E4"]:
            off.add("R-E4")
        disabled[j] = frozenset(off)
    return RFacts(
        seat_aliases=aliases,
        location_codes=codes,
        ecli_codes={j: frozenset(c) for j, c in ecli["codes"].items()} if adopted["R-E2"] else {},
        cc_prefixes={ch: frozenset(c) for ch, c in ecli["cc_prefixes"].items()}
        if adopted["R-E5"]
        else {},
        disabled_rules=disabled,
        coverage={j: (w.start, w.end) for j, w in windows.items()},
        recall_reliable={},
    )


def _real_refs(samples: dict[str, list], ce_records: list[dict]):
    for j in ("cc", "ca"):
        for meta in samples[j]:
            yield j, meta, normalize(fields_from_judilibre(meta))
    for record in ce_records:
        yield "ce", record, normalize(fields_from_ce_opendata(record))


def _specificity(samples, ce_records, provisional: RFacts, today: date) -> dict:
    facts = load_facts()
    counts: dict[str, Counter] = {j: Counter() for j in ("cc", "ca", "ce")}
    totals: Counter = Counter()
    examples: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    flagged: dict[str, list[frozenset]] = defaultdict(list)
    for j, raw, ref in _real_refs(samples, ce_records):
        totals[j] += 1
        rules = incoherences(ref, generation_date=today, facts=facts, r_facts=provisional)
        flagged[j].append(rules)
        for rule in rules:
            counts[j][rule] += 1
            if len(examples[j][rule]) < 5:
                examples[j][rule].append(
                    {
                        "id": raw.get("id") or raw.get("Numero_Dossier"),
                        "formation": ref.formation,
                        "number": ref.number,
                        "date": f"{ref.year}-{ref.month}-{ref.day}",
                        "ecli": ref.ecli,
                    }
                )
    rates = {j: {rule: counts[j][rule] / totals[j] for rule in sorted(counts[j])} for j in counts}
    disabled = {
        j: {rule: rate for rule, rate in rates[j].items() if rate > SPECIFICITY_MAX} for j in rates
    }
    residual = {}
    for j in counts:
        off = set(disabled[j]) | set(provisional.disabled(j))
        hit = sum(1 for rules in flagged[j] if rules - off)
        residual[j] = hit / totals[j] if totals[j] else 0.0
    return {
        "n": dict(totals),
        "counts": {j: dict(c) for j, c in counts.items()},
        "rates": rates,
        "disabled": disabled,
        "residual_false_positive_rate": residual,
        "examples": {j: dict(e) for j, e in examples.items()},
    }


def _recall(samples, ce_records, client, ce_index, windows, today: date) -> dict:
    rng = np.random.default_rng(RECALL_SEED)
    out = {}
    pools = {
        "cc": [normalize(fields_from_judilibre(m)) for m in samples["cc"]],
        "ce": [normalize(fields_from_ce_opendata(r)) for r in ce_records],
    }
    for j, refs in pools.items():
        eligible = sorted(
            (r for r in refs if r.is_complete() and _in_window(r, windows[j])),
            key=lambda r: (r.source_id or "", r.number or ""),
        )
        picks = rng.choice(len(eligible), size=min(RECALL_DRAWN, len(eligible)), replace=False)
        found, missed = 0, []
        for i in sorted(int(x) for x in picks):
            ref = eligible[i]
            verification = check_existence(
                ref, client=client, ce_index=ce_index, windows=windows, today=today
            )
            if verification.status == "exists":
                found += 1
            else:
                missed.append(
                    {
                        "id": ref.source_id,
                        "number": ref.number,
                        "formation": ref.formation,
                        "status": verification.status,
                        "reason": verification.reason,
                        "partial_match": verification.partial_match,
                    }
                )
        drawn = len(picks)
        out[j] = {
            "drawn": drawn,
            "found": found,
            "reliable": drawn == RECALL_DRAWN and found >= RECALL_MIN,
            "missed": missed,
        }
    return out


def _in_window(ref, window: CoverageWindow) -> bool:
    try:
        day = date(ref.year, ref.month, ref.day)
    except TypeError, ValueError:
        return False
    return window.position(day) is None


def render_r_facts(measures: dict) -> str:
    seats_text = R_FACTS_PATH.read_text(encoding="utf-8")
    start = seats_text.index("[seats]")
    end = seats_text.index("\n[", start + 1)
    header = seats_text[: seats_text.index("schema = 1")]
    ecli = measures["ecli"]
    spec = measures["specificity"]
    windows = measures["windows"]
    recall = measures["recall"]
    when = measures["measured_at"][:10]
    parts = [
        header + f'schema = 1\nchecked = "{when}"\n',
        seats_text[start:end].rstrip() + "\n",
        toml_table(
            "ecli",
            {
                "status": "sample",
                "source": f"mesurer-base du {when} : /scan abrégé cc {list(CC_YEARS)} "
                f"et ca {list(CA_YEARS)}, index CE complet ; seuil d'adoption 99 %",
                "adopted": ecli["adopted"],
                "share": ecli["share"],
                "n": ecli["n"],
                "codes": {j: sorted(c) for j, c in ecli["codes"].items()},
                "code_counts": {j: c for j, c in ecli["codes"].items()},
                "cc_prefixes": {ch: sorted(c) for ch, c in ecli["cc_prefixes"].items()},
            },
        ),
        toml_table(
            "coverage",
            {
                "status": "sample",
                "source": f"mesurer-base du {when} : /stats cc (keys=year) et ca, index CE (D5)",
                **{
                    j: {"start": w["start"], "end": w["end"], "basis": w["basis"]}
                    for j, w in windows.items()
                },
            },
        ),
        "[disabled_rules]\n"
        'status = "sample"\n'
        f'source = "mesurer-base du {when} : règle qui signale plus de 0,5 % des vraies '
        "d'une juridiction (taux mesuré)\"\n"
        + "".join(f"{j} = {_toml_value(spec['disabled'][j])}\n" for j in ("cc", "ce", "ca")),
        toml_table(
            "specificity",
            {
                "status": "sample",
                "source": f"mesurer-base du {when} : toutes les règles sur toutes les vraies (P11)",
                "n": spec["n"],
                "residual_false_positive_rate": spec["residual_false_positive_rate"],
            },
        ),
        toml_table(
            "recall",
            {
                "status": "sample",
                "source": f"mesurer-base du {when} : {RECALL_DRAWN} vraies par juridiction, graine "
                f"{RECALL_SEED}, au moins {RECALL_MIN} retrouvées (P6)",
                **{
                    j: {"drawn": r["drawn"], "found": r["found"], "reliable": r["reliable"]}
                    for j, r in recall.items()
                },
            },
        ),
    ]
    return "\n".join(parts)


def cmd_mesurer_base(args) -> int:
    client = make_client(args)
    today = datetime.now(UTC).date()
    ce_index = CeIndex.load(args.ce_index)
    ce_records = ce_index.records
    cc_stats = client.stats("cc", "year")
    ca_stats = client.stats("ca")
    windows = coverage_windows(
        cc_stats=cc_stats, ca_stats=ca_stats, ce_max_date=ce_index.max_date()
    )
    samples: dict[str, list] = {"cc": [], "ca": []}
    for j, years in (("cc", CC_YEARS), ("ca", CA_YEARS)):
        for year in years:
            for month in range(1, 13):
                samples[j].extend(_month_lot(client, j, year, month))
    ecli = _ecli_facts(samples, ce_records)
    provisional = _provisional_r_facts(ecli, windows)
    spec = _specificity(samples, ce_records, provisional, today)
    recall = _recall(samples, ce_records, client, ce_index, windows, today)
    fields_seen = sorted({k for j in samples for m in samples[j] for k in m})
    measures = {
        "measured_at": now_utc(),
        "grid_version": GRID_VERSION,
        "windows": {
            j: {"start": w.start.isoformat(), "end": w.end.isoformat(), "basis": w.basis}
            for j, w in windows.items()
        },
        "samples": {j: len(v) for j, v in samples.items()} | {"ce": len(ce_records)},
        "abridged_fields": fields_seen,
        "ecli": ecli,
        "specificity": spec,
        "recall": recall,
        "requests": client.requests,
        "cache_hits": client.cache_hits,
        "x_rate_limit": client.rate.raw,
        "ce_index_sha256": sha256_file(args.ce_index),
    }
    write_json(args.sortie / "mesure.json", measures)
    if args.ecrire_r_facts:
        write_text(R_FACTS_PATH, render_r_facts(measures))
    print(json.dumps({k: measures[k] for k in ("windows", "samples", "requests")}, indent=1))
    print("adoption ECLI :", ecli["adopted"], {k: round(v, 4) for k, v in ecli["share"].items()})
    print("désactivées :", spec["disabled"])
    print("faux positifs résiduels :", spec["residual_false_positive_rate"])
    print("rappel :", {j: (r["found"], r["drawn"], r["reliable"]) for j, r in recall.items()})
    return 0


# --- classer (phase B) ---------------------------------------------------------------------


def guard_frozen_grid(expected: str, repo: Path = ROOT) -> str | None:
    """Message d'erreur si HEAD diffère de `expected` ou si l'arbre n'est pas propre."""
    head = git("rev-parse", "HEAD", cwd=repo)
    if not head or not expected or not head.startswith(expected.lower()) or len(expected) < 7:
        return f"HEAD {head[:12]} différent de --grille-figee {expected}"
    if git("status", "--porcelain", cwd=repo):
        return "arbre de travail modifié (git status --porcelain non vide)"
    return None


def collect_units(generations, facts, r_facts) -> tuple[list[Unit], int]:
    citations = []
    extracted = 0
    for gen in generations:
        gen_date = date.fromisoformat(gen.generation_date)
        for ref in extract_references(gen.response):
            extracted += 1
            citations.append(
                citation_from(
                    ref,
                    normalize(fields_from_extracted(ref)),
                    model=gen.model,
                    digest=gen.digest,
                    request_id=gen.request_id,
                    generation_date=gen_date,
                )
            )
    return build_units(citations, MODELES), extracted


def cmd_classer(args) -> int:
    problem = guard_frozen_grid(args.grille_figee, args.depot)
    if problem:
        print(f"refus : {problem}", file=sys.stderr)
        return 2
    try:
        generations = read_collection(
            args.collecte, manifest_sha256=args.manifeste_sha256, requests_path=args.requetes
        )
    except CollectionError as error:
        print(f"refus : {error}", file=sys.stderr)
        return 2
    facts = load_facts()
    r_facts = load_r_facts()
    windows = windows_from(r_facts)
    client = make_client(args)
    ce_index = CeIndex.load(args.ce_index)
    units, extracted = collect_units(generations, facts, r_facts)
    attempts = errors = 0

    def verify(ref):
        nonlocal attempts, errors
        result = check_existence(ref, client=client, ce_index=ce_index, windows=windows)
        if result.reason not in {
            "before_window",
            "after_window",
            "penal_ca",
            "invalid_date",
            "future",
            "incomplete",
            "no_window",
        }:
            attempts += 1
            errors += result.reason == "api_error"
        return result

    try:
        for unit in units:
            classify_unit(unit, facts=facts, r_facts=r_facts, verify=verify)
    except JudilibreError as error:
        print(f"arrêt : {error}", file=sys.stderr)
        return 3
    if attempts and errors / attempts > API_ERROR_MAX:
        print(
            f"arrêt (P8) : {errors} requêtes d'existence en api_error sur {attempts} (> 1 %) ; "
            "aucun classement écrit",
            file=sys.stderr,
        )
        return 3
    versions = {
        "normalizer": NORMALIZER_ID,
        "grid": GRID_VERSION,
        "r_facts_sha256": r_facts_sha256(),
        "facts_sha256": facts_sha256(),
    }
    out = args.sortie
    write_classement(out / "classement.jsonl", units, versions)
    write_extraction(out / "interne" / "extraction.jsonl", units)
    manifest = {
        "written_at": now_utc(),
        "grid_commit": git("rev-parse", "HEAD", cwd=args.depot),
        "spec_commit": git(
            "log", "-1", "--format=%H", "--", str(SPEC.relative_to(ROOT)), cwd=args.depot
        ),
        "inputs": {
            "collecte_manifest_sha256": args.manifeste_sha256.lower(),
            "collecte.jsonl": sha256_file(Path(args.collecte) / "collecte.jsonl"),
            "r_facts.toml": r_facts_sha256(),
            "facts.toml": facts_sha256(),
            "ce_index": sha256_file(args.ce_index),
        },
        "outputs": {
            "classement.jsonl": sha256_file(out / "classement.jsonl"),
            "interne/extraction.jsonl": sha256_file(out / "interne" / "extraction.jsonl"),
        },
        "funnel": {
            "generations": len(generations),
            "references_extracted": extracted,
            "units": len(units),
        },
        "existence": {"attempts": attempts, "api_error": errors},
        "judilibre": {
            "requests": client.requests,
            "cache_hits": client.cache_hits,
            "x_rate_limit": client.rate.raw,
        },
    }
    write_json(out / "manifest.json", manifest)
    print(
        f"classement écrit : {len(generations)} générations, {extracted} références extraites, "
        f"{len(units)} unités ; sha256 {manifest['outputs']['classement.jsonl']}. "
        "Aucune part calculée (P1) : contrôle de qualité, puis `porte`."
    )
    return 0


# --- echantillons (phase B) ----------------------------------------------------------------


def draw(ids: list[str], size: int, k: int) -> list[str]:
    ordered = sorted(ids)
    rng = np.random.default_rng([0, k])
    picks = rng.choice(len(ordered), size=min(size, len(ordered)), replace=False)
    return sorted(ordered[int(i)] for i in picks)


def samples_for(rows: list[dict], responses: list[str], with_refs: set[str], offset: int) -> dict:
    by_class = defaultdict(list)
    for row in rows:
        by_class[row["class"]].append(row["unit_id"])
    denominator = by_class["incoherent"] + by_class["coherent_absent"]
    excluded = by_class["partial"] + by_class["unverifiable"] + by_class["out_of_scope"]
    with_ref = [r for r in responses if r in with_refs]
    without = [r for r in responses if r not in with_refs]
    n_with, n_without = QC_SIZES[3]
    return {
        "offset": offset,
        "k1_denominator": draw(denominator, QC_SIZES[1], 1 + offset),
        "k2_excluded": draw(excluded, QC_SIZES[2], 2 + offset),
        "k3_responses_with_refs": draw(with_ref, n_with, 3 + offset),
        "k3_responses_without_refs": draw(without, n_without, 3 + offset),
        "k4_coherent_absent": draw(by_class["coherent_absent"], QC_SIZES[4], 4 + offset),
        "exhaustive": sorted(
            row["unit_id"]
            for row in rows
            if row["grid_false_positive"] or row["partial_match"] == "formation"
        ),
    }


def cmd_echantillons(args) -> int:
    rows = read_classement(args.classement)
    generations = read_collection(args.collecte, manifest_sha256=args.manifeste_sha256)
    responses = [f"{g.model}|{g.request_id}" for g in generations]
    with_refs = set()
    extraction = args.classement.parent / "interne" / "extraction.jsonl"
    for line in extraction.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        with_refs.add(f"{row['model']}|{row['request_id']}")
    result = samples_for(rows, responses, with_refs, args.decalage)
    result["classement_sha256"] = sha256_file(args.classement)
    target = args.classement.parent / f"echantillons_{args.decalage}.json"
    write_json(target, result)
    print(f"tirages écrits : {target}")
    return 0


# --- porte (phase B) -----------------------------------------------------------------------


def read_verdict(path: Path, classement_sha: str) -> tuple[dict | None, str | None]:
    if path is None or not Path(path).is_file():
        return None, "verdict du contrôle de qualité absent (P1)"
    verdict = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        date.fromisoformat(str(verdict.get("date")))
    except ValueError:
        return None, "verdict non daté (champ `date` AAAA-MM-JJ)"
    if verdict.get("classement_sha256") != classement_sha:
        return None, "verdict d'un autre classement (sha256 différent)"
    if verdict.get("verdict") not in VERDICTS or verdict.get("tour") not in (0, 1):
        return None, "verdict illisible (`verdict` accepte|echec, `tour` 0|1)"
    if verdict["verdict"] == "echec" and verdict["tour"] == 0:
        return None, "contrôle en échec au tour 0 : tour de correction d'abord (P1)"
    return verdict, None


def _unit_date(row: dict) -> date | None:
    try:
        return date(row["year"], row["month"], row["day"])
    except TypeError, ValueError:
        return None


def _counts(rows) -> tuple[int, int]:
    inc = sum(1 for r in rows if r["class"] == "incoherent")
    ca = sum(1 for r in rows if r["class"] == "coherent_absent")
    return inc, ca


def _result(rows) -> dict | None:
    result = maybe_gate(*_counts(rows))
    if result is None:
        return None
    return {
        "k": result.k,
        "n": result.n,
        "p": result.p,
        "low": result.low,
        "high": result.high,
        "side_comparatif": result.side,
    }


def compute_gate(rows: list[dict], windows: dict[str, CoverageWindow], verdict: dict) -> dict:
    denominator = [r for r in rows if r["class"] in {"incoherent", "coherent_absent"}]
    ecli_only = [
        r for r in denominator if r["class"] == "incoherent" and set(r["rules"]) <= ECLI_RULES
    ]
    d1 = [r for r in denominator if r not in ecli_only]
    in_window = []
    for r in denominator:
        day = _unit_date(r)
        w = windows.get(r["jurisdiction"])
        if day and w and w.position(day) is None:
            in_window.append(r)
    decision = gate(*_counts(d1))
    p_all = _result(denominator)
    p_window = _result(in_window)
    incoherent = [r for r in denominator if r["class"] == "incoherent"]
    n_inc = len(incoherent) or 1
    format_only = sum(1 for r in incoherent if set(r["rules"]) <= {"R-F1", "R-F2"}) / n_inc
    empirical_only = sum(1 for r in incoherent if set(r["rules"]) <= {"R-H2", "R-H4"}) / n_inc
    typed = sum(1 for r in incoherent if r["nuss_types"]) / n_inc
    attested = sum(1 for r in incoherent if set(r["nuss_types"]) & {"t01", "t02", "t03"}) / n_inc
    untyped_only = sum(1 for r in incoherent if not r["nuss_types"]) / n_inc
    by_jurisdiction = {j: _result([r for r in d1 if r["jurisdiction"] == j]) for j in ("cc", "ce")}
    by_model = {
        m: _result([r for r in d1 if any(c["model"] == m for c in r["citations"])]) for m in MODELES
    }
    fam_units = [
        (r["class"] == "incoherent", frozenset(family_of(c["model"]) for c in r["citations"]))
        for r in d1
    ]
    shares = family_shares(fam_units)
    loo = leave_one_out(fam_units, FAMILIES)
    dominant = dominant_family(decision, fam_units)
    reserves = []
    tight = decision.tight
    if p_window is not None and p_window["side_comparatif"] != decision.side:
        tight = True
        reserves.append("sensibilité : p_window de l'autre côté de 30 % (P0, serrée)")
    if decision.n < 100:
        reserves.append("effectif faible")
    if p_all is not None and p_all["side_comparatif"] != decision.side:
        reserves.append("sensibilité : p (ECLI compris) de l'autre côté de 30 %")
    found = (verdict.get("fausses_absences") or {}).get("trouvees", 0)
    drawn = (verdict.get("fausses_absences") or {}).get("tirees", 0)
    f = found / drawn if drawn else 0.0
    p_corr = None
    if f > 0:
        inc, ca = _counts(d1)
        p_corr = inc / (inc + ca * (1 - f)) if inc + ca * (1 - f) else None
        if p_corr is not None and (p_corr >= THRESHOLD) != decision.side:
            reserves.append("sensibilité : p_corr (fausses absences) de l'autre côté de 30 %")
    if dominant:
        reserves.append(f"famille dominante : {dominant}")
    if verdict["verdict"] == "echec":
        reserves.append("réserve forte : contrôle de qualité en échec après le tour de correction")
    partial = [r for r in rows if r["class"] == "partial"]
    out_of_scope = Counter(
        r["jurisdiction"] or "inconnue" for r in rows if r["class"] == "out_of_scope"
    )
    rule_counts = Counter(rule for r in incoherent for rule in r["rules"])
    nuss_counts = Counter(t for r in incoherent for t in r["nuss_types"])
    return {
        "decision": decision.decision,
        "basis": "p_d1 (P0)",
        "p_d1": {
            "k": decision.k,
            "n": decision.n,
            "p": decision.p,
            "low": decision.low,
            "high": decision.high,
        },
        "tight": tight,
        "reserves": reserves,
        "p": p_all,
        "p_window": p_window,
        "p_corr": p_corr,
        "false_absences": {"drawn": drawn, "found": found, "f": f},
        "ecli_only_units": len(ecli_only),
        "share_format_only": format_only,
        "share_empirical_only": empirical_only,
        "overlap_15_types": {
            "typed": typed,
            "attested_t01_t03": attested,
            "untyped_only": untyped_only,
        },
        "rule_counts": dict(sorted(rule_counts.items())),
        "nuss_counts": dict(sorted(nuss_counts.items())),
        "by_jurisdiction": by_jurisdiction,
        "by_model": by_model,
        "family_shares": shares,
        "leave_one_family_out": {
            fam: (None if g is None else {"p": g.p, "n": g.n}) for fam, g in loo.items()
        },
        "classes": dict(Counter(r["class"] for r in rows)),
        "partial_incoherent": sum(1 for r in partial if r["rules"]),
        "out_of_scope": dict(out_of_scope),
        "class_conflict": sum(1 for r in rows if r["class_conflict"]),
        "grid_false_positive": sum(1 for r in rows if r["grid_false_positive"]),
        "partial_match": dict(Counter(r["partial_match"] for r in rows if r["partial_match"])),
        "unverifiable_reasons": dict(
            Counter(r["unverifiable_reason"] for r in rows if r["class"] == "unverifiable")
        ),
    }


def decision_line(result: dict) -> str:
    d = result["p_d1"]
    parts = [
        f"1.12 · décision · porte R : p = {fmt(d['p'])} [{fmt(d['low'])} ; {fmt(d['high'])}] "
        f"sur {d['n']}, {result['decision']}"
    ]
    if result["tight"]:
        parts.append("serrée")
    if result["reserves"]:
        parts.append("réserves : " + " ; ".join(result["reserves"]))
    return ", ".join(parts)


def render_r_gate(result: dict, classement_sha: str, grid_commit: str, spec_commit: str) -> str:
    d = result["p_d1"]
    return (
        "# Décision de la porte R (story 1-12, R4 et P0), écrite par `pre_etude_r.py porte`.\n"
        "# Pas dans protocol.toml (empreinté par séance) : P12.\n"
        f"decision = {_toml_value(result['decision'])}\n"
        f'basis = "p_d1"\n'
        f"p = {_toml_value(d['p'])}\nlow = {_toml_value(d['low'])}\n"
        f"high = {_toml_value(d['high'])}\nn = {d['n']}\n"
        f"tight = {_toml_value(result['tight'])}\n"
        f"reserves = {_toml_value(result['reserves'])}\n"
        f"classement_sha256 = {_toml_value(classement_sha)}\n"
        f"grid_commit = {_toml_value(grid_commit)}\n"
        f"spec_commit = {_toml_value(spec_commit)}\n"
    )


def cmd_porte(args) -> int:
    classement = args.sortie / "classement.jsonl"
    if not classement.is_file():
        print("refus : classement absent", file=sys.stderr)
        return 2
    sha = sha256_file(classement)
    verdict, problem = read_verdict(args.verdict, sha)
    if problem:
        print(f"refus : {problem}", file=sys.stderr)
        return 2
    resume_path = args.sortie / "resume.json"
    if resume_path.exists():
        print("refus : la porte a déjà été calculée (une seule fois, P1)", file=sys.stderr)
        return 2
    manifest_path = args.sortie / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["outputs"]["classement.jsonl"] != sha:
        print("refus : classement différent de celui écrit par `classer`", file=sys.stderr)
        return 2
    rows = read_classement(classement)
    result = compute_gate(rows, windows_from(load_r_facts()), verdict)
    result["classement_sha256"] = sha
    result["verdict"] = {k: verdict[k] for k in ("date", "verdict", "tour")}
    result["grid_commit"] = manifest["grid_commit"]
    result["spec_commit"] = manifest["spec_commit"]
    result["computed_at"] = now_utc()
    result["line"] = decision_line(result)
    write_json(resume_path, result)
    write_text(
        args.r_gate, render_r_gate(result, sha, manifest["grid_commit"], manifest["spec_commit"])
    )
    manifest["outputs"]["resume.json"] = sha256_file(resume_path)
    write_json(manifest_path, manifest)
    print(result["line"])
    return 0


# --- CLI -------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pré-étude R et porte des 30 % (story 1-12)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p, network: bool = True):
        p.add_argument("--sortie", type=Path, default=PRE)
        if network:
            p.add_argument("--env-file", type=Path, default=None)
            p.add_argument("--cache", type=Path, default=CACHE)
            p.add_argument("--rafraichir", action="store_true")
            p.add_argument("--ce-index", type=Path, default=CE_INDEX)

    p = sub.add_parser("mesurer-base", help="phase A : faits de R sur la base réelle")
    common(p)
    p.set_defaults(sortie=PRE / "base")
    p.add_argument("--ecrire-r-facts", action="store_true")
    p = sub.add_parser("classer", help="phase B : classement, sans aucune part")
    common(p)
    p.add_argument("--collecte", type=Path, required=True)
    p.add_argument("--manifeste-sha256", required=True)
    p.add_argument("--grille-figee", required=True)
    p.add_argument("--requetes", type=Path, default=None)
    p.add_argument("--depot", type=Path, default=ROOT, help=argparse.SUPPRESS)
    p = sub.add_parser("echantillons", help="phase B : tirages du contrôle de qualité")
    p.add_argument("--classement", type=Path, default=PRE / "classement.jsonl")
    p.add_argument("--collecte", type=Path, required=True)
    p.add_argument("--manifeste-sha256", required=True)
    p.add_argument("--decalage", type=int, choices=(0, 10), default=0)
    p = sub.add_parser("porte", help="phase B : parts et décision, après le verdict")
    common(p, network=False)
    p.add_argument("--verdict", type=Path, default=None)
    p.add_argument("--r-gate", type=Path, default=R_GATE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "env_file", "absent") is None:
        args.env_file = main_repo_env()
    handlers = {
        "mesurer-base": cmd_mesurer_base,
        "classer": cmd_classer,
        "echantillons": cmd_echantillons,
        "porte": cmd_porte,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
