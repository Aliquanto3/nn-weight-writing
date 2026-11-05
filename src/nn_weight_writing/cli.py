"""Point d'entrée unique `nnww` (argparse).

Les autres sous-commandes arrivent avec leurs stories.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path


def _evaluate(args: argparse.Namespace) -> int:
    from nn_weight_writing.evaluation.verify import EvaluationRefused, evaluate

    try:
        out = evaluate(Path(args.run_dir))
    except EvaluationRefused as exc:
        print(f"évaluation refusée : {exc.code} ({exc.detail})", file=sys.stderr)
        return 1
    print(out)
    return 0


def _datagen(args: argparse.Namespace) -> int:
    from nn_weight_writing.datasets.toy import generate
    from nn_weight_writing.tasks.toy import TASKS

    names = sorted(TASKS) if args.task == "all" else [args.task]
    for name in names:
        try:
            data_dir, held_dir = generate(
                name, seed=args.seed, n=args.n, n_heldout=args.n_heldout, root=Path(args.root)
            )
        except (FileExistsError, ValueError) as exc:
            print(f"datagen refusé : {exc}", file=sys.stderr)
            return 1
        print(data_dir)
        print(held_dir)
    return 0


def _train(args: argparse.Namespace) -> int:
    try:
        from nn_weight_writing.baselines.train import train  # PyTorch : groupe `train` (AD-13)
    except ModuleNotFoundError as exc:
        if exc.name != "torch":
            raise
        print(f"torch absent ({exc}) : uv sync --group train", file=sys.stderr)
        return 2
    try:
        run_dir = train(
            args.task,
            Path(args.data),
            n=args.n,
            seed=args.seed,
            runs_root=Path(args.runs_root),
            lot=args.lot,
        )
    except (FileExistsError, ValueError) as exc:
        print(f"train refusé : {exc}", file=sys.stderr)
        return 1
    print(run_dir)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nnww", description="nn-weight-writing")
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate", help="évalue un dossier gelé, hors séance (AD-9)")
    evaluate.add_argument("run_dir", help="runs/<lot>/<session_id> ou runs/<lot>/train/<run_id>")
    evaluate.set_defaults(handler=_evaluate)
    datagen = sub.add_parser("datagen", help="génère un jeu jouet et son jeu réservé (AD-16)")
    datagen.add_argument("task", choices=["parity", "compare", "automaton", "all"])
    datagen.add_argument("--seed", type=int, required=True, help="graine explicite")
    datagen.add_argument("--n", type=int, default=256, help="taille du jeu de séance")
    datagen.add_argument("--n-heldout", type=int, default=400, help="taille du jeu réservé")
    datagen.add_argument("--root", default=".", help="racine de data/ et heldout/")
    datagen.set_defaults(handler=_datagen)
    train = sub.add_parser("train", help="témoin C : entraîne l'architecture de référence")
    train.add_argument("task", choices=["parity", "compare", "automaton"])
    train.add_argument("--data", required=True, help="data/<task>/<dataset>")
    train.add_argument("--n", type=int, required=True, help="nombre d'exemples étiquetés")
    train.add_argument("--seed", type=int, required=True)
    train.add_argument("--lot", default="toy")
    train.add_argument("--runs-root", default="runs")
    train.set_defaults(handler=_train)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
