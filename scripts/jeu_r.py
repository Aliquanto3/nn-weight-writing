"""Jeu R (`legal_r`, story 1-13) : construction, plancher d'indice et coût du tirage.

Sous-commandes :
    construire     phase B : R depuis le classement de 1-12, après la porte (D1 à D5)
    plancher       phase B : témoins triviaux de S1 (écart d'année, longueur du raw)
    mesurer-cout   phase A : coût Judilibre du tirage, mesuré sur des jours tirés de la fenêtre

Exemples :
    uv run python scripts/jeu_r.py construire --ce-index data/r/ce_index \
        --ce-index-sha256 <hex> --s-root C:\\Users\\Utilisateur\\nnww-artefacts
    uv run python scripts/jeu_r.py plancher
    uv run python scripts/jeu_r.py mesurer-cout --jours 12

La clé Judilibre est lue dans l'environnement, sinon dans la ligne `JUDILIBRE_KEY_ID=` de
`--env-file` (défaut : `.env` du dépôt principal), chargée dans `os.environ` du processus pour
que `redact()` la masque dans tout ce qui est écrit. Elle n'est jamais affichée.
`construire` ne lit ni `data/r/collecte/` ni aucun texte de réponse : seulement le classement,
`interne/extraction.jsonl`, le manifeste et `resume.json` de la pré-étude.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import tomllib
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np

from nn_weight_writing.datasets.legal_r.ce_index import CeIndex
from nn_weight_writing.datasets.legal_r.classify import read_classement
from nn_weight_writing.datasets.legal_r.dataset import (
    EXCLUSIONS,
    MAX_DAY_TRIES,
    R_DATASET_VERSION,
    R_TASK,
    RBuildError,
    day_kind,
    match_reals,
    recheck_fakes,
    select_fakes,
    split_pairs,
    write_r_dataset,
)
from nn_weight_writing.datasets.legal_r.existence import CoverageWindow
from nn_weight_writing.datasets.legal_r.floor import floor_accuracies
from nn_weight_writing.datasets.legal_r.grid import GRID_VERSION
from nn_weight_writing.datasets.legal_r.judilibre import (
    KEY_ENV,
    JudilibreClient,
    JudilibreError,
    key_from_env,
)
from nn_weight_writing.datasets.legal_r.normalize import NORMALIZER_ID
from nn_weight_writing.datasets.legal_r.pool import CeDays, cc_day_candidates
from nn_weight_writing.datasets.legal_r.r_facts import load_r_facts, r_facts_sha256
from nn_weight_writing.journal.writer import redact
from nn_weight_writing.tasks.legal import TASKS as LEGAL_TASKS
from nn_weight_writing.tasks.legal.facts import facts_sha256

ROOT = Path(__file__).resolve().parents[1]
PRE = Path("data") / "r" / "pre_etude"
CACHE = Path("data") / "r" / "cache" / "judilibre"
CE_INDEX = Path("data") / "r" / "ce_index"
OUT = Path("data") / "r" / "jeu_r"
R_GATE = Path("config") / "r_gate.toml"
S_TASKS = ("legal_s", "legal_s_reserved")
TARGETS = {
    "session": Path("data") / R_TASK / "session",
    "train": Path("data") / R_TASK / "train",
    "eval": Path("heldout") / R_TASK / "eval",
}
COST_CHAMBERS = ("civ. 1re", "civ. 2e", "civ. 3e", "com.", "soc.", "crim.")
COST_FAKES = 300
COST_SEARCHES = ("99-99.991", "98-98.982", "97-97.973")

# Frontière réseau : transport HTTP (None = urllib) et options du client, remplacés par les tests.
FETCH = None
CLIENT_KW: dict = {}


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
    if not os.environ.get(KEY_ENV) and env_file is not None and Path(env_file).is_file():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{KEY_ENV}="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    os.environ[KEY_ENV] = value
                break
    return key_from_env()


def make_client(args) -> JudilibreClient:
    return JudilibreClient(
        load_key(args.env_file), fetch=FETCH, cache_dir=args.cache, log=print, **CLIENT_KW
    )


def write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(text), encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    ).stdout.strip()


def windows() -> dict[str, CoverageWindow]:
    return {
        j: CoverageWindow(j, start, end, "r_facts.toml")
        for j, (start, end) in load_r_facts().coverage.items()
    }


def read_jsonl(path: Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.split("\n") if line.strip()]


def s_raws(s_root: Path) -> tuple[frozenset[str], dict[str, int]]:
    """`raw` de S et S-réservé (tous leurs jeux sous `data/` et `heldout/`), et des exemples
    cités dans les descriptions des tâches juridiques (S7, D3)."""
    raws: set[str] = set()
    files: dict[str, int] = {}
    for task in S_TASKS:
        data = sorted(s_root.glob(f"data/{task}/*/examples.jsonl"))
        held = sorted(s_root.glob(f"heldout/{task}/*/examples.jsonl"))
        if not data or not held:
            raise RBuildError("s_missing", f"jeux de {task} absents sous {s_root}")
        for path in (*data, *held):
            rows = read_jsonl(path)
            files[path.relative_to(s_root).as_posix()] = len(rows)
            raws.update(r["raw"] for r in rows)
    for task in LEGAL_TASKS.values():
        raws.update(re.findall(r"« ((?:Cass\.|CE,|CA )[^»]*?) »", task.description))
    return frozenset(raws), files


# --- construire ----------------------------------------------------------------------------


def guards(args) -> tuple[dict, dict]:
    """Gardes de D1 (code 2, rien d'écrit) ; rend la porte et les empreintes lues."""
    pre = Path(args.pre_etude_dir)
    classement = pre / "classement.jsonl"
    extraction = pre / "interne" / "extraction.jsonl"
    gate_path = Path(args.r_gate)
    if not gate_path.is_file():
        raise RBuildError("gate_missing", f"{gate_path} absent : porte de 1-12 non jouée")
    gate = tomllib.loads(gate_path.read_text(encoding="utf-8"))
    for path in (classement, extraction, pre / "manifest.json", pre / "resume.json"):
        if not path.is_file():
            raise RBuildError("pre_etude_missing", f"{path.name} absent")
    sha = {
        "classement.jsonl": sha256_file(classement),
        "interne/extraction.jsonl": sha256_file(extraction),
        "resume.json": sha256_file(pre / "resume.json"),
    }
    if gate.get("classement_sha256") != sha["classement.jsonl"]:
        raise RBuildError("gate_mismatch", "classement_sha256 de r_gate.toml différent")
    manifest = json.loads((pre / "manifest.json").read_text(encoding="utf-8"))
    outputs = manifest.get("outputs", {})
    for name, value in sha.items():
        if outputs.get(name) != value:
            raise RBuildError("manifest_mismatch", f"empreinte de {name} différente du manifeste")
    ce_dir = Path(args.ce_index)
    ce_manifest_path = ce_dir / "manifest.json"
    if not ce_manifest_path.is_file() or not (ce_dir / "index.jsonl").is_file():
        raise RBuildError("ce_index_missing", f"index du CE absent : {ce_dir}")
    sha["ce_index_manifest"] = sha256_file(ce_manifest_path)
    if sha["ce_index_manifest"] != args.ce_index_sha256.lower():
        raise RBuildError("ce_index_mismatch", "sha256 du manifest.json de l'index différent")
    ce_manifest = json.loads(ce_manifest_path.read_text(encoding="utf-8"))
    if ce_manifest.get("index_sha256") != sha256_file(ce_dir / "index.jsonl"):
        raise RBuildError("ce_index_mismatch", "index.jsonl différent de son manifeste")
    root = Path(args.root)
    for target in TARGETS.values():
        path = root / target
        if path.exists() and any(path.iterdir()):
            raise RBuildError("already_built", f"{target.as_posix()} existe et n'est pas vide")
    head = git(args.repo, "rev-parse", "HEAD")
    if not head:
        raise RBuildError("not_a_repo", f"{args.repo} : HEAD illisible")
    if git(args.repo, "status", "--porcelain"):
        raise RBuildError("dirty_tree", "arbre de travail modifié (git status --porcelain)")
    sha["code_commit"] = head
    sha["ce_extraction_date"] = str(ce_manifest.get("finished_at", ""))[:10]
    return gate, sha


def check_versions(rows: list[dict]) -> None:
    expected = {"r_facts_sha256": r_facts_sha256(), "facts_sha256": facts_sha256()}
    for row in rows:
        versions = row.get("versions") or {}
        for key, value in expected.items():
            if versions.get(key) != value:
                raise RBuildError("versions_mismatch", f"{key} du classement différent")


def cmd_construire(args) -> int:
    try:
        return _construire(args)
    except RBuildError as error:
        print(f"refus : {error}", file=sys.stderr)
        return error.exit_code
    except JudilibreError as error:  # clé absente, 423, quota : rien n'est écrit
        print(f"arrêt : {error}", file=sys.stderr)
        return 3


def _construire(args) -> int:
    gate, sha = guards(args)
    pre = Path(args.pre_etude_dir)
    rows = read_classement(pre / "classement.jsonl")
    check_versions(rows)
    corpus_date = datetime.now(UTC).date()  # S5 : jour du tirage des vraies
    ce_date = sha["ce_extraction_date"]
    if not ce_date or date.fromisoformat(ce_date) > corpus_date:
        raise RBuildError("ce_index_mismatch", "date de l'index du CE illisible ou future")
    forbidden, s_files = s_raws(Path(args.s_root or args.root))
    win = windows()
    extraction = read_jsonl(pre / "interne" / "extraction.jsonl")
    selection = select_fakes(
        rows, extraction=extraction, windows=win, s_raws=forbidden, corpus_date=corpus_date
    )
    index = CeIndex.load(Path(args.ce_index) / "index.jsonl")
    client = make_client(args)
    found = recheck_fakes(selection, client=client, ce_index=index, windows=win, today=corpus_date)
    ce_days = CeDays(index)

    def pool(jurisdiction: str, day: date):
        if jurisdiction == "ce":
            return ce_days.candidates(day)
        try:
            return cc_day_candidates(client, day)
        except JudilibreError as error:
            raise RBuildError("api_error", str(error), exit_code=3) from error

    pairs, unmatched = match_reals(
        selection.fakes,
        pool,
        seed=args.seed,
        windows=win,
        corpus_date=corpus_date,
        forbidden_raws=forbidden,
    )
    selection.excluded["no_real_in_stratum"] += len(unmatched)
    splits = split_pairs(pairs, seed=args.seed)
    if max((p.real.day for p in pairs), default=corpus_date) > corpus_date:
        raise RBuildError("real_after_corpus_date", "vraie postérieure à corpus_date")
    funnel = {
        "units": len(rows),
        "excluded": {k: selection.excluded[k] for k in EXCLUSIONS},
        "before_window_by_jurisdiction": selection.before_window,
        "fakes": len(pairs),
    }
    incoherent = sum(1 for p in pairs if p.fake.type_id != "c00")
    meta = {
        "encoder": LEGAL_TASKS[R_TASK].encoder_id,
        "generator": R_TASK,
        "version": R_DATASET_VERSION,
        "extraction_date": corpus_date.isoformat(),
        "extraction_dates": {"judilibre": corpus_date.isoformat(), "ce-opendata": ce_date},
        "corpus_date": corpus_date.isoformat(),
        "windows": {j: [w.start.isoformat(), w.end.isoformat()] for j, w in win.items()},
        "classement_sha256": sha["classement.jsonl"],
        "r_gate": {
            "decision": gate.get("decision"),
            "p_d1": gate.get("p"),
            "interval": [gate.get("low"), gate.get("high")],
            "tight": gate.get("tight"),
        },
        "normalizer": NORMALIZER_ID,
        "grid": GRID_VERSION,
        "r_facts_sha256": r_facts_sha256(),
        "facts_sha256": facts_sha256(),
        "code_commit": sha["code_commit"],
        "ce_index_sha256": sha["ce_index_manifest"],
        "swagger_sha256": sha256_file(args.swagger) if args.swagger else None,
        "funnel": funnel,
        "p_R_all": incoherent / len(pairs) if pairs else None,
        "visible_types": [v["id"] for v in LEGAL_TASKS[R_TASK].vocabulary],
    }
    root = Path(args.root)
    written = {}
    for split, members in splits.items():
        if not members:
            continue
        path = write_r_dataset(
            root / TARGETS[split], members, split=split, meta=meta, seed=args.seed
        )
        written[split] = {
            "path": TARGETS[split].as_posix(),
            "pairs": len(members),
            "dataset_sha256": sha256_file(path / "dataset.json"),
        }
    out = root / OUT
    notes = Counter()
    with_notes = []
    for pair in pairs:
        for key in pair.notes:
            notes[key] += 1
        with_notes.append({"unit_id": pair.fake.unit_id, "real": pair.real.source_id, **pair.notes})
    write_text(
        out / "appariement.jsonl",
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in with_notes),
    )
    resume = {
        "written_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_date": corpus_date.isoformat(),
        "funnel": funnel,
        "found_at_build": found,
        "unmatched": unmatched,
        "p_R": meta["p_R_all"],
        "p_d1": gate.get("p"),
        "decision": gate.get("decision"),
        "splits": written,
        "notes": dict(notes),
        "day_offsets": dict(Counter(p.notes.get("day_offset", 0) for p in pairs)),
    }
    write_json(out / "resume.json", resume)
    write_json(
        out / "manifest.json",
        {
            "inputs": {**{k: v for k, v in sha.items() if k != "code_commit"}, "s_files": s_files},
            "code_commit": sha["code_commit"],
            "outputs": {s: w["dataset_sha256"] for s, w in written.items()},
            "judilibre": {
                "requests": client.requests,
                "cache_hits": client.cache_hits,
                "x_rate_limit": client.rate.raw,
            },
        },
    )
    sizes = ", ".join(f"{s} {w['pairs']} paires" for s, w in written.items())
    print(f"jeu R construit : {len(pairs)} fausses ; {sizes} ; corpus_date {corpus_date}")
    return 0


# --- plancher (S1) -------------------------------------------------------------------------


def labelled(directory: Path) -> list[tuple[str, str]]:
    raws = {r["id"]: r["raw"] for r in read_jsonl(directory / "examples.jsonl")}
    return [(raws[r["id"]], r["label"]) for r in read_jsonl(directory / "labels.jsonl")]


def cmd_plancher(args) -> int:
    root = Path(args.root)
    train, held = root / TARGETS["train"], root / TARGETS["eval"]
    if not (train / "labels.jsonl").is_file() or not (held / "labels.jsonl").is_file():
        print("plancher non joué : jeu d'entraînement ou réservé de R absent", file=sys.stderr)
        return 2
    result = floor_accuracies(labelled(train), labelled(held))
    result["train_sha256"] = sha256_file(train / "dataset.json")
    result["eval_sha256"] = sha256_file(held / "dataset.json")
    write_json(root / OUT / "plancher.json", result)
    print(
        f"plancher d'indice : écart {result['year_gap']:.3f}, longueur {result['raw_length']:.3f}, "
        f"numéro du CE {result['ce_number']:.3f}"
    )
    return 0


# --- mesurer-cout (S10, phase A) -----------------------------------------------------------


def sample_days(window: CoverageWindow, n: int, seed: int) -> list[date]:
    rng = np.random.default_rng([seed, 9])
    span = (window.end - window.start).days
    days: list[date] = []
    while len(days) < n:
        day = date.fromordinal(window.start.toordinal() + int(rng.integers(span + 1)))
        if day_kind(day) == "ouvre" and day not in days:
            days.append(day)
    return sorted(days)


def project_cost(days: list[dict], searches: list[int], fakes: int = COST_FAKES) -> dict:
    """Projection pour `fakes` fausses, toutes de la Cour de cassation (borne haute)."""
    pages = float(np.mean([d["requests"] for d in days]))
    tries = []
    for chamber in COST_CHAMBERS:
        share = sum(1 for d in days if d["by_chamber"].get(chamber)) / len(days)
        tries.append(min(1 / share, MAX_DAY_TRIES) if share else MAX_DAY_TRIES)
    expected_days = float(np.mean(tries))
    search_pages = float(np.mean(searches)) if searches else 0.0
    per_fake = pages * expected_days + search_pages
    fetched = [d["seconds"] / d["network"] for d in days if d.get("network")]
    seconds = float(np.mean(fetched)) if fetched else None
    return {
        "pages_per_scan_day": pages,
        "expected_days_per_fake": expected_days,
        "search_pages_per_fake": search_pages,
        "requests_per_fake": per_fake,
        "fakes": fakes,
        "requests": round(per_fake * fakes),
        "seconds_per_request": seconds,
        "minutes": round(per_fake * fakes * seconds / 60, 1) if seconds else None,
    }


def cmd_mesurer_cout(args) -> int:
    window = windows()["cc"]
    client = make_client(args)
    days = []
    try:
        for day in sample_days(window, args.jours, args.seed):
            before, hits, start = client.requests, client.cache_hits, time.monotonic()
            candidates = cc_day_candidates(client, day)
            network = client.requests - before
            days.append(
                {
                    "day": day.isoformat(),
                    "requests": network + client.cache_hits - hits,  # pages, cache comprise
                    "network": network,
                    "seconds": time.monotonic() - start,
                    "candidates": len(candidates),
                    "by_chamber": dict(Counter(c.formation for c in candidates)),
                }
            )
        searches = []
        for number in COST_SEARCHES:
            before, hits = client.requests, client.cache_hits
            client.search_number(number, "cc")
            searches.append(client.requests - before + client.cache_hits - hits)
    except JudilibreError as error:
        print(f"arrêt : {error}", file=sys.stderr)
        return 3
    result = {
        "measured_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": days,
        "search_requests": searches,
        "requests": client.requests,
        "cache_hits": client.cache_hits,
        "x_rate_limit": client.rate.raw,
        "projection": project_cost(days, searches),
    }
    write_json(Path(args.root) / OUT / "cout.json", result)
    p = result["projection"]
    print(
        f"{client.requests} requêtes ({client.cache_hits} en cache) ; projection pour "
        f"{p['fakes']} fausses : {p['requests']} requêtes, ~{p['minutes']} min"
    )
    if p["minutes"] is None:
        print("durée non projetée : tout venait du cache (relancer avec un --cache neuf)")
    return 0


# --- interface -----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("construire", help="phase B : R depuis le classement, après la porte")
    p.add_argument("--pre-etude-dir", type=Path, default=PRE)
    p.add_argument("--r-gate", type=Path, default=R_GATE)
    p.add_argument("--ce-index", type=Path, default=CE_INDEX)
    p.add_argument("--ce-index-sha256", required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--s-root", type=Path, default=None, help="racine des jeux de S (S7)")
    p.add_argument("--swagger", type=Path, default=None, help="Swagger Judilibre relu")
    p.add_argument("--repo", type=Path, default=ROOT, help="dépôt du code (garde git)")
    p = sub.add_parser("plancher", help="phase B : témoins triviaux de S1")
    p = sub.add_parser("mesurer-cout", help="phase A : coût Judilibre du tirage")
    p.add_argument("--jours", type=int, default=12)
    p.add_argument("--seed", type=int, default=0)
    for name in ("construire", "plancher", "mesurer-cout"):
        q = sub.choices[name]
        q.add_argument("--root", type=Path, default=Path("."))
        if name != "plancher":
            q.add_argument("--env-file", type=Path, default=None)
            q.add_argument("--cache", type=Path, default=CACHE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "env_file", "absent") is None:
        args.env_file = main_repo_env()
    handlers = {
        "construire": cmd_construire,
        "plancher": cmd_plancher,
        "mesurer-cout": cmd_mesurer_cout,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
