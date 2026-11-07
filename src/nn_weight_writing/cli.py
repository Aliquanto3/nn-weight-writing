"""Point d'entrée unique `nnww` (argparse).

Les autres sous-commandes arrivent avec leurs stories.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

# --- evaluate (story 1-14 : mesures, --lot-dir, évaluation croisée) ---------------------------


def _evaluate(args: argparse.Namespace) -> int:
    from nn_weight_writing.evaluation.score import run_task
    from nn_weight_writing.evaluation.verify import EvaluationRefused, evaluate, lot_dirs

    if bool(args.run_dirs) == bool(args.lot_dir):
        print("evaluate : RUN_DIR ou --lot-dir, l'un des deux seulement", file=sys.stderr)
        return 2
    on = None
    if args.on:
        task, sep, dataset = args.on.partition(":")
        if not sep or not task or not dataset:
            print("--on attend TASK:DATASET", file=sys.stderr)
            return 2
        on = (task, dataset)
    heldout_root = Path(args.heldout_root) if args.heldout_root else None
    if (on or args.dataset) and heldout_root is None:
        print("--on et --dataset demandent --heldout-root", file=sys.stderr)
        return 2
    if heldout_root is None:
        print(
            "avertissement : sans --heldout-root, vérification seule (metrics vide)",
            file=sys.stderr,
        )
    if args.lot_dir:
        frozen, unfrozen, baselines = lot_dirs(Path(args.lot_dir))
        for path in unfrozen:
            print(f"non gelée : {path.name}", file=sys.stderr)
        targets = frozen + baselines
    else:
        targets = [Path(d) for d in args.run_dirs]
    status = 0
    for run_dir in targets:
        try:
            if args.from_task and run_task(run_dir) != args.from_task:
                continue
            out = evaluate(run_dir, heldout_root, dataset=args.dataset, on=on)
        except EvaluationRefused as exc:
            print(
                f"évaluation refusée : {run_dir.name} : {exc.code} ({exc.detail})", file=sys.stderr
            )
            status = 1
            continue
        except ValueError as exc:
            print(f"évaluation refusée : {run_dir.name} : {exc}", file=sys.stderr)
            status = 1
            continue
        print(out)
    return status


# --- fin du bloc evaluate ------------------------------------------------------------------------


def _datagen_legal(args: argparse.Namespace) -> int:
    from nn_weight_writing.datasets.legal import generate

    if args.n is not None or args.n_heldout is not None:
        print("datagen legal : tailles fixées, --n et --n-heldout refusés", file=sys.stderr)
        return 2
    try:
        paths = generate(seed=args.seed, root=Path(args.root))
    except (FileExistsError, ValueError, RuntimeError) as exc:
        print(f"datagen refusé : {exc}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


def _datagen(args: argparse.Namespace) -> int:
    if args.task == "legal":
        return _datagen_legal(args)
    from nn_weight_writing.datasets.toy import generate
    from nn_weight_writing.tasks.toy import TASKS

    n = 256 if args.n is None else args.n
    n_heldout = 400 if args.n_heldout is None else args.n_heldout
    names = sorted(TASKS) if args.task == "all" else [args.task]
    for name in names:
        try:
            data_dir, held_dir = generate(
                name, seed=args.seed, n=n, n_heldout=n_heldout, root=Path(args.root)
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
            prepared=args.prepared,
        )
    except (FileExistsError, ValueError) as exc:
        print(f"train refusé : {exc}", file=sys.stderr)
        return 1
    print(run_dir)
    return 0


def _retrain(args: argparse.Namespace) -> int:
    try:
        from nn_weight_writing.baselines.train import retrain  # PyTorch : groupe `train` (AD-13)
    except ModuleNotFoundError as exc:
        if exc.name != "torch":
            raise
        print(f"torch absent ({exc}) : uv sync --group train", file=sys.stderr)
        return 2
    from nn_weight_writing.evaluation.verify import EvaluationRefused

    try:
        run_dir = retrain(
            Path(args.session_dir),
            Path(args.data),
            n=args.n,
            seed=args.seed,
            runs_root=Path(args.runs_root),
            lot=args.lot,
        )
    except (FileExistsError, ValueError, EvaluationRefused) as exc:
        print(f"retrain refusé : {exc}", file=sys.stderr)
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
    if args.dataset == "train":
        print("jeu d'entraînement des témoins, pas un jeu de séance", file=sys.stderr)
        return 2
    try:
        examples = examples_path(args.task, args.dataset, args.data_dir and Path(args.data_dir))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.dataset not in task.session_datasets:
        allowed = ", ".join(task.session_datasets)
        print(f"jeu de séance inconnu : {args.dataset} ; autorisés : {allowed}", file=sys.stderr)
        return 2
    # --- 1-13 : prompt de R seulement après le commit « jeu R figé » (D6, S5) ---
    if args.task == "legal_r":
        from nn_weight_writing.tasks.legal.task import R_CORPUS_DATE

        if R_CORPUS_DATE is None:
            print("legal_r : R_CORPUS_DATE non fixée, jeu R pas encore figé", file=sys.stderr)
            return 2
    # --- fin 1-13 ---
    if not examples.is_file():
        print(f"exemples absents : {examples}", file=sys.stderr)
        return 2
    from nn_weight_writing.session.tools import check_size_target

    try:
        check_size_target(args.method, args.size_target)
    except ValueError as exc:
        print(exc, file=sys.stderr)
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
            size_target=args.size_target,
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


# --- table (story 1-14) -----------------------------------------------------------------------


def _table(args: argparse.Namespace) -> int:
    from nn_weight_writing.budget.ledger import LEDGER_PATH
    from nn_weight_writing.report.decisions import DecisionsError
    from nn_weight_writing.report.table import build, write

    decisions = Path(args.decisions or Path(args.out) / f"decisions-lot{args.lot}.toml")
    try:
        result = build(
            Path(args.root),
            args.lot,
            decisions_path=decisions,
            ledger_path=Path(args.ledger) if args.ledger else LEDGER_PATH,
        )
    except DecisionsError as exc:
        print(f"table refusée : {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"table refusée : {exc}", file=sys.stderr)
        return 2
    for issue in result.issues:
        print(issue, file=sys.stderr)
    # Q3 : ce que `table` écrit, et le fichier de décisions, passent les contrôles de publish.
    # Écriture dans un dossier temporaire, contrôle, puis remplacement seulement sans refus :
    # un tableau refusé ne reste jamais dans `docs/` (fichiers commités).
    import os
    import tempfile

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out, prefix=".table-") as tmp:
        staged = write(result, Path(tmp), args.lot)
        checked = [*staged, decisions] if decisions.is_file() else list(staged)
        status = _check_published(checked, Path(args.root), args.config, args.env_file)
        if status:
            print("tableau non écrit", file=sys.stderr)
            return status
        for path in staged:
            os.replace(path, out / path.name)
            print(out / path.name)
    return 1 if args.strict and result.issues else 0


# --- fin du bloc table -------------------------------------------------------------------------


# --- publish (story 1-14 : AD-18, R2, R6, décisions Q1-Q5, Q10, Q11) ---------------------------


def _publish_rules(root: Path, config: str | None, env_file: str | None):
    """Règles des contrôles : `publish.toml`, secrets de l'environnement et du `.env` (Q5)."""
    import os

    from nn_weight_writing.config import CONFIG_DIR, load_publish
    from nn_weight_writing.publish.checks import Rules, collect_secrets, load_reserved

    settings = load_publish(Path(config) if config else None)
    if env_file:
        env_files = [Path(env_file)]
        if not env_files[0].is_file():
            raise FileNotFoundError(f"{env_file} : fichier .env introuvable")
    else:
        candidates = {Path(".env").resolve(), (CONFIG_DIR.parent / ".env").resolve()}
        env_files = sorted(p for p in candidates if p.is_file())
    secrets = collect_secrets(os.environ, env_files)
    print(f"valeurs de secret contrôlées : {secrets.count}")
    if not secrets.count:
        print("avertissement : aucune valeur de secret à contrôler", file=sys.stderr)
    reserved = load_reserved(root / "heldout")
    if reserved is not None:
        print(
            f"raw réservés contrôlés : {reserved.count} ; sautés (moins de 12 caractères) : "
            f"{reserved.skipped}"
        )
    rules = Rules(secrets, reserved, frozenset(settings.r_tasks), settings.r_republish)
    return rules


def _print_refusals(violations) -> int:
    for violation in violations:
        print(violation, file=sys.stderr)
    print(f"publication refusée : {len(violations)} refus, rien n'est écrit", file=sys.stderr)
    return 1


def _check_published(paths, root: Path, config: str | None, env_file: str | None) -> int:
    from nn_weight_writing.publish.checks import check_paths

    try:
        rules = _publish_rules(root, config, env_file)
        violations, count = check_paths(paths, rules, root)
    except (OSError, ValueError) as exc:
        print(f"contrôle impossible : {exc}", file=sys.stderr)
        return 2
    print(f"fichiers contrôlés : {count}")
    return _print_refusals(violations) if violations else 0


def _publish(args: argparse.Namespace) -> int:
    from nn_weight_writing.publish import archive

    root = Path(args.root)
    if args.check:
        if args.lot is not None:
            print("publish : N ou --check, l'un des deux seulement", file=sys.stderr)
            return 2
        return _check_published([Path(p) for p in args.check], root, args.config, args.env_file)
    if args.lot is None:
        print("publish : numéro de lot N ou --check PATH...", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else root / "dist" / f"lot{args.lot}"
    notice = Path(args.notice) if args.notice else Path(__file__).resolve().parents[2] / "NOTICE"
    try:
        rules = _publish_rules(root, args.config, args.env_file)
        result = archive.plan(root, args.lot, out, rules, notice)
    except (OSError, ValueError) as exc:
        print(f"publication impossible : {exc}", file=sys.stderr)
        return 2
    print(
        f"séances : {result.sessions} ; témoins : {result.baselines} ; membres : {len(result.runs)}"
    )
    print(f"archive de R : {result.r_status}")
    print(f"ignorés : {len(result.ignored)}")
    print("data/ hors r_tasks et heldout/ : hors archives (collecte de 1-12a non publiée, Q11)")
    if args.dry_run:
        for name in sorted(result.runs):
            print(f"inclus : {name}")
        for name in sorted(result.r or {}):
            print(f"inclus (R) : {name}")
        for name in result.ignored:
            print(f"ignoré : {name}")
    if result.violations:
        return _print_refusals(result.violations)
    if args.dry_run:
        print("à blanc : aucun refus, rien n'est écrit")
        return 0
    for path in archive.write(result, out):
        print(path)
    return 0


# --- fin du bloc publish -----------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nnww", description="nn-weight-writing")
    sub = parser.add_subparsers(dest="command", required=True)
    # --- evaluate (story 1-14) ---
    evaluate = sub.add_parser("evaluate", help="évalue des dossiers gelés, hors séance (AD-9)")
    evaluate.add_argument(
        "run_dirs", nargs="*", help="runs/<lot>/<session_id> ou runs/<lot>/train/<run_id>"
    )
    evaluate.add_argument("--lot-dir", help="évalue chaque dossier gelé de runs/<lot>/")
    evaluate.add_argument("--heldout-root", help="racine des jeux réservés : mesures obligatoires")
    evaluate.add_argument("--dataset", help="jeu réservé natif, si la tâche en a plusieurs")
    evaluate.add_argument("--on", help="évaluation croisée TASK:DATASET")
    evaluate.add_argument("--from-task", help="seulement les réseaux écrits pour cette tâche")
    evaluate.set_defaults(handler=_evaluate)
    # --- fin evaluate ---
    datagen = sub.add_parser(
        "datagen", help="génère les jeux jouet ou ceux de S et S-réservé (AD-16)"
    )
    datagen.add_argument("task", choices=["parity", "compare", "automaton", "all", "legal"])
    datagen.add_argument("--seed", type=int, required=True, help="graine explicite")
    datagen.add_argument("--n", type=int, default=None, help="jouet : jeu de séance (256)")
    datagen.add_argument("--n-heldout", type=int, default=None, help="jouet : jeu réservé (400)")
    datagen.add_argument("--root", default=".", help="racine de data/ et heldout/")
    datagen.set_defaults(handler=_datagen)
    train = sub.add_parser("train", help="témoin C : entraîne l'architecture de référence")
    train.add_argument(
        "task",
        # --- 1-13 : legal_r (témoins C et F sur l'entraînement de R) ---
        choices=["parity", "compare", "automaton", "legal_s", "legal_s_reserved", "legal_r"],
        # --- fin 1-13 ---
    )
    train.add_argument("--prepared", action="store_true", help="témoin F : entrées préparées")
    train.add_argument("--data", required=True, help="data/<task>/<dataset>")
    train.add_argument("--n", type=int, required=True, help="nombre d'exemples étiquetés")
    train.add_argument("--seed", type=int, required=True)
    train.add_argument("--lot", default="toy")
    train.add_argument("--runs-root", default="runs")
    train.set_defaults(handler=_train)
    retrain = sub.add_parser(
        "retrain", help="C « même réseau » : réentraîne l'architecture gelée d'une séance"
    )
    retrain.add_argument("session_dir", help="runs/<lot>/<session_id> (gelée)")
    retrain.add_argument("--data", required=True, help="data/<task>/train")
    retrain.add_argument("--n", type=int, required=True, help="nombre d'exemples (8192)")
    retrain.add_argument("--seed", type=int, required=True)
    retrain.add_argument("--lot", default="1")
    retrain.add_argument("--runs-root", default="runs")
    retrain.set_defaults(handler=_retrain)

    session = sub.add_parser("session", help="mène une séance d'écriture (AD-10, AD-11, AD-14)")
    session.add_argument("--task", required=True)
    session.add_argument("--dataset", required=True, help="data/<task>/<dataset>/examples.jsonl")
    session.add_argument("--method", required=True, choices=["A-program", "A-literal", "B"])
    session.add_argument("--model", required=True, help="nom dans config/models.toml")
    session.add_argument(
        "--size-target",
        type=int,
        help="taille visée en paramètres (10000 ou 100000) : obligatoire pour A, interdite pour B",
    )
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

    # --- table (story 1-14) ---
    table = sub.add_parser("table", help="tableau des mesures d'un lot, depuis les artefacts")
    table.add_argument("--lot", type=int, required=True)
    table.add_argument("--root", default=".", help="racine qui contient runs/<lot>/")
    table.add_argument("--out", default="docs/mesures", help="dossier de lot<N>.md et .json")
    table.add_argument("--decisions", help="défaut : <out>/decisions-lot<N>.toml")
    table.add_argument("--ledger", help="défaut : budget/ledger.csv")
    table.add_argument("--strict", action="store_true", help="code 1 s'il reste un point ouvert")
    table.add_argument("--config", help="publish.toml des contrôles (défaut : config/)")
    table.add_argument("--env-file", help="fichier .env des secrets (défaut : .env du dépôt)")
    table.set_defaults(handler=_table)
    # --- fin table ---
    # --- publish (story 1-14) ---
    publish = sub.add_parser("publish", help="archives contrôlées des artefacts d'un lot (AD-18)")
    publish.add_argument("lot", type=int, nargs="?", help="numéro du lot")
    publish.add_argument("--check", nargs="+", metavar="PATH", help="contrôle seul de fichiers")
    publish.add_argument("--root", default=".", help="racine de runs/, heldout/ et data/")
    publish.add_argument("--out", help="défaut : <root>/dist/lot<N>")
    publish.add_argument("--config", help="défaut : config/publish.toml")
    publish.add_argument("--notice", help="défaut : NOTICE à la racine du dépôt")
    publish.add_argument("--env-file", help="fichier .env des secrets (défaut : .env du dépôt)")
    publish.add_argument("--dry-run", action="store_true", help="contrôles et listes, sans écrire")
    publish.set_defaults(handler=_publish)
    # --- fin publish ---
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
