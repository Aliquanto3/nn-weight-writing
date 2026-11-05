"""Implémentation PyTorch du registre de couches de AD-3 (importé par `baselines/` seul, AD-13).

Même architecture que `network.layers` : `dense` est `x @ W + b` avec `W` de forme (in, out),
et les activations `identity`, `relu`, `sigmoid`, `tanh`. Parité avec NumPy : `test_torch_parity`.
"""

from __future__ import annotations

import numpy as np
import torch
from torch import nn

from nn_weight_writing.network.layers import ACTIVATIONS, LAYER_TYPES

TORCH_ACTIVATIONS = {
    "identity": nn.Identity,
    "relu": nn.ReLU,
    "sigmoid": nn.Sigmoid,
    "tanh": nn.Tanh,
}

if set(TORCH_ACTIVATIONS) != set(ACTIVATIONS) or LAYER_TYPES != {"dense"}:
    raise RuntimeError(
        "registre PyTorch différent du registre NumPy (AD-3) : ajouter l'implémentation"
    )


def build_module(manifest: dict) -> nn.Sequential:
    """Module séquentiel qui suit les couches du manifeste, poids à l'initialisation par défaut."""
    modules: list[nn.Module] = []
    for layer in manifest["layers"]:
        modules.append(nn.Linear(layer["in"], layer["out"]))
        modules.append(TORCH_ACTIVATIONS[layer["activation"]]())
    return nn.Sequential(*modules)


def _linears(module: nn.Sequential) -> list[nn.Linear]:
    return [m for m in module if isinstance(m, nn.Linear)]


def load_weights(module: nn.Sequential, weights: dict[str, np.ndarray]) -> None:
    """Copie les poids du format AD-3 (`L{i}.W` (in, out), `L{i}.b`) dans le module."""
    with torch.no_grad():
        for i, linear in enumerate(_linears(module)):
            linear.weight.copy_(torch.from_numpy(np.ascontiguousarray(weights[f"L{i}.W"].T)))
            linear.bias.copy_(torch.from_numpy(np.ascontiguousarray(weights[f"L{i}.b"])))


def export_weights(module: nn.Sequential) -> dict[str, np.ndarray]:
    """Poids du module au format AD-3, en `float32`."""
    weights: dict[str, np.ndarray] = {}
    for i, linear in enumerate(_linears(module)):
        weights[f"L{i}.W"] = linear.weight.detach().cpu().numpy().T.astype(np.float32).copy()
        weights[f"L{i}.b"] = linear.bias.detach().cpu().numpy().astype(np.float32).copy()
    return weights
