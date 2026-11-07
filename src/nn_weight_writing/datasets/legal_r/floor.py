"""Plancher d'indice de R (story 1-13, S1) : trois témoins triviaux à une seule variable.

Une régression logistique sur l'écart d'année du numéro seul (classes de S1, en indicatrices),
une autre sur la longueur du `raw` seule (centrée réduite sur l'entraînement), une troisième sur
le numéro du Conseil d'État rapporté à sa date (`ce_number`) : le numéro du CE n'a pas d'année
mais suit l'ordre d'enregistrement, que les vraies respectent et que les fausses ignorent ; il
n'est pas apparié (une vraie est tirée du jour de sa fausse). Entraînées sur
l'entraînement de R, évaluées sur son réservé : une méthode qui ne fait pas mieux n'a rien appris
au-delà de ces indices. Descente de gradient complète, déterministe, sans dépendance optionnelle.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from nn_weight_writing.datasets.legal_r.dataset import GAP_CLASSES, raw_gap_class
from nn_weight_writing.tasks.legal.reference import parse_reference

ITERATIONS = 2000
LEARNING_RATE = 0.5
L2 = 1e-4
FLOORS = ("year_gap", "raw_length", "ce_number")


def gap_features(raws: Sequence[str]) -> np.ndarray:
    x = np.zeros((len(raws), len(GAP_CLASSES)))
    for i, raw in enumerate(raws):
        x[i, GAP_CLASSES.index(raw_gap_class(raw))] = 1.0
    return x


def length_features(raws: Sequence[str], mean: float, std: float) -> np.ndarray:
    lengths = np.array([len(r) for r in raws], dtype=float)
    return ((lengths - mean) / (std or 1.0)).reshape(-1, 1)


def _ce_point(raw: str) -> tuple[float, float] | None:
    """(date décimale, numéro) d'une référence du CE à numéro entier ; None sinon."""
    ref = parse_reference(raw)
    if ref.jurisdiction != "ce" or not (ref.number or "").isdigit():
        return None
    return ref.year + (ref.month - 1) / 12 + (ref.day - 1) / 365, float(ref.number)


def ce_number_model(raws: Sequence[str], labels: Sequence[str]) -> tuple[float, float, float]:
    """Droite numéro ~ date ajustée sur les vraies du CE de l'entraînement ; écart-type résiduel.

    Moins de deux vraies du CE (ou dates toutes égales) : pente nulle, numéro moyen."""
    points = [
        pt
        for raw, label in zip(raws, labels, strict=True)
        if label == "real" and (pt := _ce_point(raw)) is not None
    ]
    if not points:
        return 0.0, 0.0, 1.0
    t, n = np.array(points).T
    slope = float(np.polyfit(t, n, 1)[0]) if len(points) >= 2 and np.ptp(t) > 0 else 0.0
    intercept = float(n.mean() - slope * t.mean())
    std = float((n - (slope * t + intercept)).std()) or 1.0
    return slope, intercept, std


def ce_number_features(raws: Sequence[str], model: tuple[float, float, float]) -> np.ndarray:
    """Indicatrice CE et log(1 + écart absolu réduit du numéro à la droite) (0 hors CE)."""
    slope, intercept, std = model
    x = np.zeros((len(raws), 2))
    for i, raw in enumerate(raws):
        point = _ce_point(raw)
        if point is not None:
            t, n = point
            x[i] = 1.0, np.log1p(abs(n - (slope * t + intercept)) / std)
    return x


def _scale(x: np.ndarray, train: np.ndarray) -> np.ndarray:
    """Colonnes centrées réduites sur l'entraînement (descente stable, mêmes prédictions)."""
    mean, std = train.mean(axis=0), train.std(axis=0)
    return (x - mean) / np.where(std > 0, std, 1.0)


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
    model = ce_number_model(train_raws, train_labels)
    x_train = ce_number_features(train_raws, model)
    x_held = _scale(ce_number_features(held_raws, model), x_train)
    w, b = fit_logistic(_scale(x_train, x_train), y)
    out["ce_number"] = accuracy(predict(x_held, w, b), held_labels)
    return out
