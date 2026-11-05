"""Registre des couches et passe NumPy (AD-3)."""

from __future__ import annotations

import numpy as np

LAYER_TYPES = frozenset({"dense"})


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return (1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))).astype(np.float32)


ACTIVATIONS = {
    "identity": lambda x: x,
    "relu": lambda x: np.maximum(x, np.float32(0.0)),
    "sigmoid": _sigmoid,
    "tanh": np.tanh,
}


def forward(manifest: dict, weights: dict[str, np.ndarray], x: np.ndarray) -> np.ndarray:
    """Passe avant : `x` de forme (n, in) en float32, sortie (n, out) en float32."""
    out = np.asarray(x, dtype=np.float32)
    for i, layer in enumerate(manifest["layers"]):
        out = out @ weights[f"L{i}.W"] + weights[f"L{i}.b"]
        out = ACTIVATIONS[layer["activation"]](out).astype(np.float32)
    return out
