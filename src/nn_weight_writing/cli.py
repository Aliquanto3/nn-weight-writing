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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nnww", description="nn-weight-writing")
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate", help="évalue un dossier gelé, hors séance (AD-9)")
    evaluate.add_argument("run_dir", help="runs/<lot>/<session_id> ou runs/<lot>/train/<run_id>")
    evaluate.set_defaults(handler=_evaluate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
