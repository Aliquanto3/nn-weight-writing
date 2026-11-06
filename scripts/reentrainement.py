"""Réentraîne à N = 8 192 les architectures gelées des séances A (story 1-11, seconde partie).

Usage : uv run --group train python scripts/reentrainement.py run --table <compte-rendu 1-10.md>
            --runs-from <dossier runs/1 des séances> [--root .] [--seeds 0 1 2] [--n 8192]
        uv run --group train python scripts/reentrainement.py table [--root .]

La liste des séances vient de la dernière colonne du tableau « Résultats (… séances A …) » du
compte rendu 1-10 (lecture seule ; `retrain` vérifie les empreintes). Les séances B et les
dossiers absents du tableau sont ignorés. Résultats ajoutés à `<root>/runs/1/reentrainement.jsonl`.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from nn_weight_writing.baselines.curve import append_jsonl, measure, read_jsonl
from nn_weight_writing.baselines.train import retrain

ROW = re.compile(r"^\|(?P<cells>.*)\|\s*$")


def parse_table(text: str) -> list[dict]:
    """Lignes du tableau des séances A : modèle, tâche, case, paramètres, exactitude, dossier."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 14 or not cells[-1].startswith("`runs/1/"):
            continue
        accuracy = re.search(r"(\d+)/(\d+)", cells[8])
        rows.append(
            {
                "model": cells[0],
                "task": cells[1],
                "case": cells[2],
                "attempt": cells[3],
                "params": int(cells[7]),
                "session_correct": int(accuracy.group(1)),
                "session_n": int(accuracy.group(2)),
                "session": cells[-1].strip("`").split("/")[-1],
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["run"])
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--runs-from", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--n", type=int, default=8192)
    args = parser.parse_args(argv)
    out = args.root / "runs" / "1" / "reentrainement.jsonl"
    done = {(r["session"], r["seed"]) for r in read_jsonl(out)}
    for row in parse_table(args.table.read_text("utf-8")):
        for seed in args.seeds:
            if (row["session"], seed) in done:
                continue
            run_dir = retrain(
                args.runs_from / row["session"],
                args.root / "data" / row["task"] / "train",
                n=args.n,
                seed=seed,
                runs_root=args.root / "runs",
                lot="1",
            )
            accuracy = measure(run_dir, row["task"], args.root / "heldout" / row["task"] / "eval")
            record = {**row, "seed": seed, "n": args.n, "run": run_dir.name, "accuracy": accuracy}
            append_jsonl(out, record)
            print(run_dir.name, accuracy["all"], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
