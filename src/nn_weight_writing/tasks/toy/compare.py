"""Comparaison de nombres : deux entiers de 0 à 999, plus petit, égal ou plus grand ?"""

from __future__ import annotations

import numpy as np

from nn_weight_writing.tasks.toy.base import ToyTask

MAX_VALUE = 999
SCALE = 1000.0


def parse(raw: str) -> tuple[int, int]:
    parts = raw.split(" ")
    if len(parts) != 2 or not all(p.isascii() and p.isdigit() for p in parts):
        raise ValueError(f"comparaison : deux entiers séparés par une espace, reçu {raw!r}")
    a, b = int(parts[0]), int(parts[1])
    if not (0 <= a <= MAX_VALUE and 0 <= b <= MAX_VALUE):
        raise ValueError(f"comparaison : entiers de 0 à {MAX_VALUE}, reçu {raw!r}")
    return a, b


def _encode(raw: str) -> np.ndarray:
    a, b = parse(raw)
    return np.array([a / SCALE, b / SCALE], dtype=np.float32)


TASK = ToyTask(
    name="compare",
    description=(
        f"Chaque exemple est « a b » : deux entiers de 0 à {MAX_VALUE} séparés par une espace. "
        "Dire si a est plus petit que b, égal à b, ou plus grand que b."
    ),
    classes=(
        ("less", "a est strictement plus petit que b"),
        ("equal", "a est égal à b"),
        ("greater", "a est strictement plus grand que b"),
    ),
    encoder_name="pair",
    encoder_version=1,
    n_inputs=2,
    _encode=_encode,
)
