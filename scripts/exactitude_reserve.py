"""Exactitude d'une séance gelée sur le jeu réservé, hors séance (en attendant 1-14).

Usage : uv run python scripts/exactitude_reserve.py runs/1/<session_id> [...] [--dataset toy]

Pour chaque séance : `verify_frozen` (empreintes de `frozen/` et `tree_sha256` du journal) d'abord,
lecture de `heldout/<tâche>/<jeu>/` ensuite seulement. A : `score_frozen` ; B : `rules.py` gelé
exécuté par `sandbox.run` profil B, comme en séance. Imprime session, tree_sha256, correct/n.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nn_weight_writing import sandbox
from nn_weight_writing.evaluation.labels import read_labels
from nn_weight_writing.evaluation.score import accuracy, check_alignment, score_frozen
from nn_weight_writing.evaluation.verify import FROZEN_DIR, verify_frozen
from nn_weight_writing.sandbox import Profile
from nn_weight_writing.tasks.io import read_examples
from nn_weight_writing.tasks.registry import get_task

HELDOUT = Path("heldout")


def _open_record(run_dir: Path) -> dict:
    with (run_dir / "journal.jsonl").open(encoding="utf-8") as f:
        return json.loads(f.readline())


def predict(run_dir: Path, dataset: str) -> tuple[str, dict[str, object], dict]:
    """Empreinte, prédictions et étiquettes du réservé (empreintes vérifiées d'abord)."""
    _, _, tree, _ = verify_frozen(run_dir)  # refuse avant toute lecture du réservé
    task = _open_record(run_dir)["task"]
    examples_path = HELDOUT / task / dataset / "examples.jsonl"
    labels_path = HELDOUT / task / dataset / "labels.jsonl"
    rules = run_dir / FROZEN_DIR / "rules.py"
    examples = read_examples(examples_path)
    labels = read_labels(labels_path)
    if not rules.exists():
        score = score_frozen(run_dir, get_task(task).codec, examples_path, labels_path)
        return tree, {"__score__": score}, labels
    check_alignment(examples, labels)
    result = sandbox.run(
        rules.read_text(encoding="utf-8"), Profile.B, {"examples": [e.raw for e in examples]}
    )
    if not result.ok or not isinstance(result.value, list):
        raise RuntimeError(f"règles B en échec : {result.error}")
    predictions = {e.id: item.get("label") for e, item in zip(examples, result.value, strict=True)}
    return tree, predictions, labels


def measure(run_dir: Path, dataset: str) -> tuple[str, int, int]:
    tree, predictions, labels = predict(run_dir, dataset)
    if "__score__" in predictions:
        return tree, predictions["__score__"].correct, predictions["__score__"].n
    score = accuracy(predictions, labels)
    return tree, score.correct, score.n


def by_type(run_dir: Path, dataset: str) -> dict[str, tuple[int, int]]:
    """Exactitude par `type_id` (règles B seulement : A n'expose pas les prédictions)."""
    _, predictions, labels = predict(run_dir, dataset)
    if "__score__" in predictions:
        raise RuntimeError("--par-type n'est défini que pour la méthode B")
    table: dict[str, tuple[int, int]] = {}
    for lid, lab in labels.items():
        ok, n = table.get(lab.type_id, (0, 0))
        table[lab.type_id] = (ok + (predictions.get(lid) == lab.label), n + 1)
    return dict(sorted(table.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--dataset", default="toy")
    parser.add_argument("--par-type", action="store_true", help="détail par type_id (méthode B)")
    args = parser.parse_args(argv)
    for run_dir in args.run_dirs:
        tree, correct, n = measure(run_dir, args.dataset)
        print(f"{run_dir.name}\t{tree}\t{correct}/{n}")
        if args.par_type:
            for type_id, (ok, total) in by_type(run_dir, args.dataset).items():
                print(f"  {type_id}	{ok}/{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
