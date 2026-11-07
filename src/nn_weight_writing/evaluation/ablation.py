"""Lisibilité par ablation (methodes-et-lots.md, décision Q8 de la story 1-14).

Éteindre une unité cachée `[couche, indice]`, c'est forcer sa sortie après activation à 0 pour
tous les exemples ; les couches suivantes sont recalculées. `network/` n'est pas modifié : la
passe masquée reprend ici, opération pour opération, celle de `network.layers.forward`.

Règle de lisibilité (Q8) : une unité est lisible si son extinction fait baisser l'exactitude sur
un type déclaré par son bloc d'au moins 5 points **et** de strictement plus du double de la plus
forte baisse sur un autre type (égalité : non lisible). Les baisses sont des fractions exactes
`(correct_complet − correct_éteint) / n` par `type_id`. Une unité sans baisse positive est
« neutre ». Score = unités lisibles / unités cachées (neutres et unités hors bloc au dénominateur).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from fractions import Fraction

import numpy as np

from nn_weight_writing.network.layers import ACTIVATIONS

MIN_DROP = Fraction(5, 100)  # 5 points d'exactitude sur le type déclaré
RATIO = 2  # au moins (strictement) le double de la plus forte baisse sur un autre type


def _layer(manifest: dict, weights: dict[str, np.ndarray], i: int, x: np.ndarray) -> np.ndarray:
    out = x @ weights[f"L{i}.W"] + weights[f"L{i}.b"]
    return ACTIVATIONS[manifest["layers"][i]["activation"]](out).astype(np.float32)


def _forward_from(
    manifest: dict,
    weights: dict[str, np.ndarray],
    x: np.ndarray,
    start: int,
    off: set[tuple[int, int]],
) -> np.ndarray:
    out = np.asarray(x, dtype=np.float32)
    for i in range(start, len(manifest["layers"])):
        out = _layer(manifest, weights, i, out)
        cols = sorted(unit for layer, unit in off if layer == i)
        if cols:
            out = out.copy()
            out[:, cols] = np.float32(0.0)
    return out


def forward_masked(
    manifest: dict, weights: dict[str, np.ndarray], x: np.ndarray, off: set[tuple[int, int]]
) -> np.ndarray:
    """Passe avant dont les unités de `off` sortent 0 ; sans masque, égale `network.forward`."""
    return _forward_from(manifest, weights, x, 0, set(off))


def _counts(predictions: Sequence[object], labels: Sequence[tuple[str, str]]) -> dict:
    """`{type_id: [correct, n]}` ; `labels` : (label, type_id) dans l'ordre des exemples."""
    table: dict[str, list[int]] = {}
    for pred, (label, type_id) in zip(predictions, labels, strict=True):
        entry = table.setdefault(type_id, [0, 0])
        entry[0] += int(pred == label)
        entry[1] += 1
    return table


def _correct(counts: dict) -> int:
    return sum(c for c, _ in counts.values())


def _fraction_text(value: Fraction) -> str:
    return str(value)  # « 1/20 », « 1 », « 0 »


def ablate(
    manifest: dict,
    weights: dict[str, np.ndarray],
    blocks: list[dict],
    inputs: np.ndarray,
    labels: Sequence[tuple[str, str]],
    decode: Callable[[np.ndarray], object],
) -> dict:
    """Ablation par bloc puis par unité cachée, et score de lisibilité (Q8)."""
    n_layers = len(manifest["layers"])
    # Activations complètes après chaque couche : une unité de la couche l ne demande que la
    # suite de la passe à partir de l + 1.
    acts = [np.asarray(inputs, dtype=np.float32)]
    for i in range(n_layers):
        acts.append(_layer(manifest, weights, i, acts[-1]))

    def predict(outputs: np.ndarray) -> list[object]:
        return [decode(row) for row in outputs]

    full = _counts(predict(acts[-1]), labels)
    types = sorted(full)
    unit_block: dict[tuple[int, int], int] = {}
    for index, block in enumerate(blocks):
        for layer, unit in block["units"]:
            unit_block.setdefault((int(layer), int(unit)), index)

    block_rows = []
    for index, block in enumerate(blocks):
        off = {(int(a), int(b)) for a, b in block["units"]}
        start = min((a for a, _ in off), default=n_layers)
        counts = _counts(predict(_forward_from(manifest, weights, acts[start], start, off)), labels)
        block_rows.append(
            {
                "index": index,
                "types": sorted(block["types"]),
                "units": sorted([a, b] for a, b in off),
                "accuracy": {"correct": _correct(counts), "n": len(labels)},
                "by_type": {t: {"correct": c, "n": n} for t, (c, n) in sorted(counts.items())},
            }
        )

    hidden = [(i, u) for i in range(n_layers - 1) for u in range(manifest["layers"][i]["out"])]
    unit_rows = []
    legible = neutral = 0
    for layer, unit in hidden:
        masked = acts[layer + 1].copy()
        masked[:, unit] = np.float32(0.0)
        outputs = _forward_from(manifest, weights, masked, layer + 1, set())
        counts = _counts(predict(outputs), labels)
        drops = {t: Fraction(full[t][0] - counts.get(t, [0, 0])[0], full[t][1]) for t in types}
        top = max(drops.values(), default=Fraction(0))
        block = unit_block.get((layer, unit))
        declared = set(blocks[block]["types"]) if block is not None else set()
        on_declared = max((d for t, d in drops.items() if t in declared), default=Fraction(0))
        on_other = max((d for t, d in drops.items() if t not in declared), default=Fraction(0))
        is_legible = (
            block is not None and on_declared >= MIN_DROP and on_declared > RATIO * on_other
        )
        if top <= 0:
            neutral += 1
        legible += int(is_legible)
        unit_rows.append(
            {
                "unit": [layer, unit],
                "block": block,
                "max_drop": _fraction_text(top),
                "max_drop_types": sorted(t for t, d in drops.items() if top > 0 and d == top),
                "declared_drop": _fraction_text(on_declared),
                "other_drop": _fraction_text(on_other),
                "legible": is_legible,
            }
        )
    total = len(hidden)
    score = Fraction(legible, total) if total else Fraction(0)
    return {
        "blocks": block_rows,
        "units": unit_rows,
        "legibility": {
            "units": total,
            "legible": legible,
            "neutral": neutral,
            "score": f"{legible}/{total}",
            "rate": round(float(score), 6),
        },
    }
