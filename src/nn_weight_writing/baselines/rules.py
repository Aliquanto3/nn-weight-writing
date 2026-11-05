"""Témoin B exécutable : règles en code, exécutées par le bac à sable de profil B (CAP-6, AD-5).

Les règles ne lisent aucun jeu ; chaque programme définit `predict(raw) -> label`.
"""

from __future__ import annotations

from pathlib import Path

from nn_weight_writing.evaluation.labels import read_labels
from nn_weight_writing.evaluation.score import Score, accuracy, check_alignment
from nn_weight_writing.sandbox.runner import SandboxResult, run
from nn_weight_writing.tasks.io import read_examples

RULES: dict[str, str] = {
    "parity": ("def predict(raw):\n    return 'odd' if raw.count('1') % 2 else 'even'\n"),
    "compare": (
        "def predict(raw):\n"
        "    left, right = raw.split(' ')\n"
        "    a, b = int(left), int(right)\n"
        "    if a < b:\n"
        "        return 'less'\n"
        "    return 'equal' if a == b else 'greater'\n"
    ),
    "automaton": (
        "import re\n"
        "\n"
        "def predict(raw):\n"
        "    return 'accept' if re.search('101', raw) else 'reject'\n"
    ),
}


class RulesError(RuntimeError):
    """Les règles ont été refusées ou ont échoué dans le bac à sable."""


def run_rules(task: str, raws: list[str], *, timeout_s: float | None = None) -> list[object]:
    """Exécute les règles de `task` sur `raws` par `sandbox.run` en profil B."""
    try:
        code = RULES[task]
    except KeyError:
        raise KeyError(f"pas de règles B pour {task!r}") from None
    result: SandboxResult = run(code, "B", {"examples": raws}, timeout_s=timeout_s)
    if not result.ok:
        raise RulesError(f"{task} : {result.error} {result.violations or ''}".strip())
    return [item["label"] for item in result.value]


def score_rules(task: str, examples_path: Path, labels_path: Path) -> Score:
    examples = read_examples(examples_path)
    labels = read_labels(labels_path)
    check_alignment(examples, labels)
    predictions = run_rules(task, [e.raw for e in examples])
    return accuracy({e.id: p for e, p in zip(examples, predictions, strict=True)}, labels)
