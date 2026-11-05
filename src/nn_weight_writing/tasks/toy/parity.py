"""Parité : le nombre de 1 d'une chaîne de 10 bits est-il pair ou impair ?"""

from __future__ import annotations

import numpy as np

from nn_weight_writing.tasks.toy.base import ToyTask

LENGTH = 10


def _encode(raw: str) -> np.ndarray:
    if len(raw) != LENGTH or set(raw) - {"0", "1"}:
        raise ValueError(f"parité : {LENGTH} caractères 0 ou 1 attendus, reçu {raw!r}")
    return np.array([int(c) for c in raw], dtype=np.float32)


TASK = ToyTask(
    name="parity",
    description=(
        f"Chaque exemple est une chaîne de {LENGTH} caractères '0' ou '1'. "
        "Dire si le nombre de '1' est pair ou impair."
    ),
    classes=(("even", "nombre de 1 pair"), ("odd", "nombre de 1 impair")),
    encoder_name="bits",
    encoder_version=1,
    n_inputs=LENGTH,
    _encode=_encode,
)
