"""Courbe des témoins C et F sur S et S-réservé (story 1-11, première partie).

Usage :
  uv run --group train python scripts/temoins_c_f.py run [--root .] [--lot 1] [--n 64 256 ...]
      [--seeds 0 1 2] [--tasks legal_s legal_s_reserved] [--methods C F]
  uv run --group train python scripts/temoins_c_f.py table [--lot 1]

Les jeux d'entraînement viennent de `<root>/data/<tâche>/train/` (à générer à la taille voulue
par `scripts/jeux_temoins.py`), le réservé de `<root>/heldout/<tâche>/eval/`. Les enregistrements
sont ajoutés à `runs/<lot>/courbe-c-f.jsonl` ; un run déjà enregistré est sauté (reprise).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nn_weight_writing.baselines.curve import append_jsonl, read_jsonl, run_curve, summarize


def _fmt(cell: tuple[float, float] | None) -> str:
    return "-" if cell is None else f"{100 * cell[0]:.1f} ± {100 * cell[1]:.1f}"


def table(records: list[dict]) -> str:
    lines = []
    for task in sorted({r["task"] for r in records}):
        lines += [f"\n### {task}\n"]
        held = task == "legal_s_reserved"
        head = (
            "| Méthode | N | Graines | Durée moy. (s) | Exactitude (%) | vraies | fausses connues |"
        )
        sep = "|---|---|---|---|---|---|---|"
        if held:
            head += " fausses tenues à l'écart |"
            sep += "---|"
        lines += [head, sep]
        for row in summarize([r for r in records if r["task"] == task]):
            cols = [
                row["method"],
                str(row["n"]),
                ",".join(map(str, row["seeds"])),
                f"{row['seconds_mean']:.1f}",
                _fmt(row.get("all")),
                _fmt(row.get("real")),
                _fmt(row.get("fake_known")),
            ]
            if held:
                cols.append(_fmt(row.get("fake_held_out")))
            lines.append("| " + " | ".join(cols) + " |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["run", "table"])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--lot", default="1")
    parser.add_argument("--n", type=int, nargs="+")
    parser.add_argument("--seeds", type=int, nargs="+")
    parser.add_argument("--tasks", nargs="+", default=["legal_s", "legal_s_reserved"])
    parser.add_argument("--methods", nargs="+", default=["C", "F"], choices=["C", "F"])
    args = parser.parse_args(argv)
    out = args.root / "runs" / args.lot / "courbe-c-f.jsonl"
    if args.action == "table":
        print(table(read_jsonl(out)))
        return 0
    done = {(r["task"], r["method"], r["n"], r["seed"]) for r in read_jsonl(out)}
    for task in args.tasks:
        for method in args.methods:
            run_curve(
                task,
                args.root / "data" / task / "train",
                args.root / "heldout" / task / "eval",
                prepared=method == "F",
                runs_root=args.root / "runs",
                lot=args.lot,
                n_values=tuple(args.n) if args.n else None,
                seeds=tuple(args.seeds) if args.seeds else None,
                skip=lambda n, s, t=task, m=method: (t, m, n, s) in done,
                log=lambda r: (
                    append_jsonl(out, r),
                    print(r["run"], r["seconds"], r["accuracy"]["all"], flush=True),
                ),
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
