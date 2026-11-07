"""Plancher d'indice de R (story 1-13, S1) : deux témoins triviaux à une seule variable.

Une régression logistique sur l'écart d'année du numéro seul (classes de S1, en indicatrices),
une autre sur la longueur du `raw` seule (centrée réduite sur l'entraînement). Entraînées sur
l'entraînement de R, évaluées sur son réservé : une méthode qui ne fait pas mieux n'a rien appris
au-delà de ces indices. Descente de gradient complète, déterministe, sans dépendance optionnelle.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from nn_weight_writing.datasets.legal_r.dataset import GAP_CLASSES, raw_gap_class

ITERATIONS = 2000
LEARNING_RATE = 0.5
L2 = 1e-4
FLOORS = ("year_gap", "raw_length")


def gap_features(raws: Sequence[str]) -> np.ndarray:
    x = np.zeros((len(raws), len(GAP_CLASSES)))
    for i, raw in enumerate(raws):
        x[i, GAP_CLASSES.index(raw_gap_class(raw))] = 1.0
    return x


def length_features(raws: Sequence[str], mean: float, std: float) -> np.ndarray:
    lengths = np.array([len(r) for r in raws], dtype=float)
    return ((lengths - mean) / (std or 1.0)).reshape(-1, 1)


def fit_logistic(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    """Poids et biais ; `y` vaut 1 pour `fake`."""
    w, b = np.zeros(x.shape[1]), 0.0
    for _ in range(ITERATIONS):
        p = 1.0 / (1.0 + np.exp(-(x @ w + b)))
        grad = p - y
        w -= LEARNING_RATE * (x.T @ grad / len(y) + L2 * w)
        b -= LEARNING_RATE * float(grad.mean())
    return w, b


def predict(x: np.ndarray, w: np.ndarray, b: float) -> list[str]:
    """`fake` au-dessus de 1/2 strictement, `real` en cas d'égalité (comme `decode`)."""
    return ["fake" if s > 0 else "real" for s in x @ w + b]


def accuracy(predicted: Sequence[str], labels: Sequence[str]) -> float:
    return sum(p == t for p, t in zip(predicted, labels, strict=True)) / len(labels)


def floor_accuracies(
    train: Sequence[tuple[str, str]], heldout: Sequence[tuple[str, str]]
) -> dict[str, float]:
    """`(raw, label)` de l'entraînement et du réservé -> exactitude réservée de chaque témoin."""
    if not train or not heldout:
        raise ValueError("plancher : entraînement et réservé non vides requis")
    train_raws, train_labels = [r for r, _ in train], [label for _, label in train]
    held_raws, held_labels = [r for r, _ in heldout], [label for _, label in heldout]
    y = np.array([1.0 if label == "fake" else 0.0 for label in train_labels])
    out = {}
    w, b = fit_logistic(gap_features(train_raws), y)
    out["year_gap"] = accuracy(predict(gap_features(held_raws), w, b), held_labels)
    lengths = np.array([len(r) for r in train_raws], dtype=float)
    mean, std = float(lengths.mean()), float(lengths.std())
    w, b = fit_logistic(length_features(train_raws, mean, std), y)
    out["raw_length"] = accuracy(predict(length_features(held_raws, mean, std), w, b), held_labels)
    return out
