"""Petit automate : une chaîne de 10 bits contient-elle le motif 101 ?"""

from __future__ import annotations

import numpy as np

from nn_weight_writing.tasks.toy.base import ToyTask

LENGTH = 10
PATTERN = "101"


def _encode(raw: str) -> np.ndarray:
    if len(raw) != LENGTH or set(raw) - {"0", "1"}:
        raise ValueError(f"automate : {LENGTH} caractères 0 ou 1 attendus, reçu {raw!r}")
    return np.array([int(c) for c in raw], dtype=np.float32)


TASK = ToyTask(
    name="automaton",
    description=(
        f"Chaque exemple est une chaîne de {LENGTH} caractères '0' ou '1', lue de gauche à droite "
        "par un automate fini à quatre états. L'automate accepte la chaîne si elle contient, à "
        "un endroit quelconque, trois caractères consécutifs '1', '0', '1', et la rejette sinon."
    ),
    classes=(("accept", "chaîne acceptée par l'automate"), ("reject", "chaîne rejetée")),
    encoder_name="bits",
    encoder_version=1,
    n_inputs=LENGTH,
    _encode=_encode,
)
