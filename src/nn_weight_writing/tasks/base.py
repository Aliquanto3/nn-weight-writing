"""Contrat d'une tâche côté séance (AD-4) : encodeur et décodeur purs et fixes."""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Codec(Protocol):
    """`encode(raw) -> ndarray[float32]` et `decode(outputs) -> label`, sous `encoder_id`."""

    name: str  # tâche, contrôlée par l'évaluation (1-9 O4)
    encoder_id: str

    def encode(self, raw: object) -> np.ndarray: ...

    def decode(self, outputs: np.ndarray) -> object: ...
