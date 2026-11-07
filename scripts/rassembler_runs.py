"""Rassemble les artefacts des worktrees dans un seul emplacement hors dépôt (story 1-14).

Copie, jamais de déplacement, de `runs/`, `heldout/` et `data/` de chaque source vers `--to`,
sans `data/r/` (collecte brute de 1-12a) ni `eval.json` et `eval-cross-*.json` (régénérés à
destination par `nnww evaluate`). Deux phases : plan complet, puis copie seulement si aucun
conflit (même chemin, sha256 différent, à destination ou entre deux sources). Un fichier déjà
présent au même sha256 est sauté : le script se relance pour ajouter une source (1-13).
Chaque fichier copié ajoute une ligne à `<to>/provenance.jsonl`. `--only runs heldout` écarte
le `data/` d'une source (jeu d'entraînement régénéré ailleurs, par exemple).

    uv run python scripts/rassembler_runs.py --to C:\\Users\\Utilisateur\\nnww-artefacts \\
        --from .claude/worktrees/1-8 .claude/worktrees/1-11 [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

TOPS = ("runs", "heldout", "data")
PROVENANCE = "provenance.jsonl"


def excluded(rel: Path) -> bool:
    parts = tuple(p.lower() for p in rel.parts)  # Windows : casse indifférente
    if parts[:2] == ("data", "r"):
        return True
    name = parts[-1]
    return parts[0] == "runs" and (name == "eval.json" or name.startswith("eval-cross-"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:  # lecture seule
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class GatherPlan:
    copies: list[tuple[Path, Path, str, str]] = field(default_factory=list)  # src, rel, sha, from
    skipped: int = 0
    excluded: int = 0
    conflicts: list[str] = field(default_factory=list)


def make_plan(sources: Sequence[Path], dest: Path, tops: Sequence[str] = TOPS) -> GatherPlan:
    plan = GatherPlan()
    planned: dict[Path, tuple[str, str]] = {}
    for source in sources:
        source = Path(source)
        for top in tops:
            base = source / top
            if not base.is_dir():
                continue
            for path in sorted(p for p in base.rglob("*") if p.is_file()):
                rel = path.relative_to(source)
                if excluded(rel):
                    plan.excluded += 1
                    continue
                sha = sha256_file(path)
                if rel in planned:
                    other_sha, other = planned[rel]
                    if other_sha != sha:
                        plan.conflicts.append(f"{rel.as_posix()} : {other} et {source} diffèrent")
                    else:
                        plan.skipped += 1
                    continue
                planned[rel] = (sha, str(source))
                target = dest / rel
                if target.exists():
                    if target.is_file() and sha256_file(target) == sha:
                        plan.skipped += 1
                    else:
                        plan.conflicts.append(f"{rel.as_posix()} : diffère à destination")
                    continue
                plan.copies.append((path, rel, sha, str(source)))
    return plan


def execute(plan: GatherPlan, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with open(dest / PROVENANCE, "a", encoding="utf-8") as log:
        for path, rel, sha, source in plan.copies:
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            line = {
                "src": source,
                "path": rel.as_posix(),
                "sha256": sha,
                "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            log.write(json.dumps(line, ensure_ascii=False) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--to", required=True, help="emplacement rassemblé")
    parser.add_argument("--from", dest="sources", nargs="+", required=True, help="worktrees")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=TOPS,
        default=list(TOPS),
        help="dossiers à copier (défaut : runs heldout data)",
    )
    parser.add_argument("--dry-run", action="store_true", help="plan seul, aucune copie")
    args = parser.parse_args(argv)
    dest = Path(args.to)
    sources = [Path(s) for s in args.sources]
    missing = [s for s in sources if not s.is_dir()]
    if missing:
        print(f"sources introuvables : {', '.join(map(str, missing))}", file=sys.stderr)
        return 2
    plan = make_plan(sources, dest, args.only)
    print(
        f"à copier : {len(plan.copies)} ; déjà présents : {plan.skipped} ; "
        f"exclus : {plan.excluded} ; conflits : {len(plan.conflicts)}"
    )
    if plan.conflicts:
        for conflict in plan.conflicts:
            print(f"conflit : {conflict}", file=sys.stderr)
        print("rien n'est copié", file=sys.stderr)
        return 1
    if not args.dry_run:
        execute(plan, dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
