"""Point d'entrée unique `nnww` (argparse).

Les autres sous-commandes arrivent avec leurs stories.
"""

from __future__ import annotations

import argparse
import json
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


def _session(args: argparse.Namespace) -> int:
    from nn_weight_writing.budget.ledger import BudgetRefused
    from nn_weight_writing.config import load_models, load_pricing, load_protocol
    from nn_weight_writing.session.run import RUNS_DIR, run_session
    from nn_weight_writing.tasks.registry import examples_path, get_task

    models = load_models()
    if args.model not in models:
        print(f"modèle inconnu : {args.model} ; connus : {', '.join(models)}", file=sys.stderr)
        return 2
    model = models[args.model]
    prices = load_pricing()
    if model.id not in prices:
        print(f"pricing.toml : aucun tarif pour {model.id}", file=sys.stderr)
        return 2
    try:
        task = get_task(args.task)
    except KeyError as exc:
        print(exc.args[0], file=sys.stderr)
        return 2
    examples = examples_path(args.task, args.dataset, args.data_dir and Path(args.data_dir))
    if not examples.is_file():
        print(f"exemples absents : {examples}", file=sys.stderr)
        return 2
    try:
        outcome = run_session(
            task=task,
            dataset=args.dataset,
            examples=examples,
            method=args.method,
            model=model,
            price=prices[model.id],
            protocol=load_protocol(),
            attempt=args.attempt,
            seed=args.seed,
            lot=args.lot,
            runs_dir=Path(args.runs_dir) if args.runs_dir else RUNS_DIR,
            ledger_path=Path(args.ledger) if args.ledger else None,
            claude_executable=json.loads(args.claude_command),
        )
    except BudgetRefused as exc:
        print(f"séance refusée : {exc}", file=sys.stderr)
        return 3
    summary = {
        "session_id": outcome.session_id,
        "run_dir": str(outcome.run_dir),
        "reason": outcome.reason,
        "detail": outcome.detail,
        "billed_usd": outcome.billed_usd,
        "cost_equiv_usd": outcome.cost_equiv_usd,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if outcome.reason == "error" else 0


def _ledger_reconcile(args: argparse.Namespace) -> int:
    from nn_weight_writing.budget.ledger import reconcile
    from nn_weight_writing.session.run import RUNS_DIR

    rows = reconcile(
        Path(args.runs_dir) if args.runs_dir else RUNS_DIR,
        Path(args.ledger) if args.ledger else None,
    )
    for row in rows:
        print(f"{row.session_id} clos : {row.billed_usd:.6f} $ facturés")
    print(f"{len(rows)} réservation(s) orpheline(s) close(s)")
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

    session = sub.add_parser("session", help="mène une séance d'écriture (AD-10, AD-11, AD-14)")
    session.add_argument("--task", required=True)
    session.add_argument("--dataset", required=True, help="data/<task>/<dataset>/examples.jsonl")
    session.add_argument("--method", required=True, choices=["A-program", "A-literal", "B"])
    session.add_argument("--model", required=True, help="nom dans config/models.toml")
    session.add_argument("--attempt", type=int, required=True)
    session.add_argument("--seed", type=int, required=True)
    session.add_argument("--lot", type=int, required=True)
    session.add_argument("--data-dir", help="défaut : data/")
    session.add_argument("--runs-dir", help="défaut : runs/")
    session.add_argument("--ledger", help="défaut : budget/ledger.csv")
    session.add_argument(
        "--claude-command",
        default='["claude"]',
        help='commande de Claude Code, liste JSON (défaut : ["claude"])',
    )
    session.set_defaults(handler=_session)

    ledger = sub.add_parser("ledger", help="registre budgétaire (AD-11)")
    ledger_sub = ledger.add_subparsers(dest="ledger_command", required=True)
    reconcile = ledger_sub.add_parser("reconcile", help="clôt les réservations orphelines")
    reconcile.add_argument("--runs-dir", help="défaut : runs/")
    reconcile.add_argument("--ledger", help="défaut : budget/ledger.csv")
    reconcile.set_defaults(handler=_ledger_reconcile)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
