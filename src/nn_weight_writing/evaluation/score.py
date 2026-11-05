"""Exactitude d'un réseau gelé ou de prédictions sur un jeu étiqueté.

`score_frozen` passe par `verify_frozen` (la même vérification d'empreintes que
`nnww evaluate`) avant de charger le réseau. Les mesures complètes (par type, ablation) : 1-14.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from nn_weight_writing import network
from nn_weight_writing.evaluation.labels import Label, read_labels
from nn_weight_writing.evaluation.verify import FROZEN_DIR, verify_frozen
from nn_weight_writing.tasks.base import Codec
from nn_weight_writing.tasks.io import Example, read_examples


@dataclass(frozen=True)
class Score:
    n: int
    correct: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.n


def accuracy(predictions: Mapping[str, object], labels: Mapping[str, Label]) -> Score:
    """Compare les prédictions aux étiquettes ; un exemple sans prédiction compte faux."""
    if not labels:
        raise ValueError("aucune étiquette")
    correct = sum(1 for lid, lab in labels.items() if predictions.get(lid) == lab.label)
    return Score(n=len(labels), correct=correct)


def check_alignment(examples: list[Example], labels: Mapping[str, Label]) -> None:
    ids = {e.id for e in examples}
    if ids != set(labels):
        raise ValueError("exemples et étiquettes ne portent pas les mêmes identifiants")


def score_frozen(run_dir: Path, codec: Codec, examples_path: Path, labels_path: Path) -> Score:
    """Vérifie les empreintes de `run_dir`, charge `frozen/` et mesure l'exactitude."""
    run_dir = Path(run_dir)
    verify_frozen(run_dir)
    manifest, weights = network.load(run_dir / FROZEN_DIR)
    if manifest["encoder"] != codec.encoder_id:
        raise ValueError(f"encodeur {manifest['encoder']!r} différent de {codec.encoder_id!r}")
    examples = read_examples(examples_path)
    labels = read_labels(labels_path)
    check_alignment(examples, labels)
    inputs = np.stack([codec.encode(e.raw) for e in examples])
    outputs = network.forward(manifest, weights, inputs)
    predictions = {e.id: codec.decode(row) for e, row in zip(examples, outputs, strict=True)}
    return accuracy(predictions, labels)
