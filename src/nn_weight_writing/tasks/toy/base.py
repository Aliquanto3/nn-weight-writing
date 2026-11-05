"""Contrat commun des tâches jouet : description, vocabulaire fermé, encodeur et décodeur (AD-4)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ToyTask:
    """Une tâche jouet. `classes` fixe l'ordre des sorties du réseau ; `decode` prend l'argmax."""

    name: str
    description: str
    classes: tuple[tuple[str, str], ...]  # (identifiant, description), ordre des sorties
    encoder_name: str
    encoder_version: int
    n_inputs: int
    _encode: Callable[[str], np.ndarray]

    @property
    def encoder_id(self) -> str:
        """Identifiant `{task}.{encoder}@{version}` (AD-4)."""
        return f"{self.name}.{self.encoder_name}@{self.encoder_version}"

    @property
    def vocabulary(self) -> list[dict]:
        """Vocabulaire fermé du paquet de séance : un identifiant par classe de sortie."""
        return [{"id": cid, "description": text} for cid, text in self.classes]

    @property
    def class_ids(self) -> tuple[str, ...]:
        return tuple(cid for cid, _ in self.classes)

    def encode(self, raw: object) -> np.ndarray:
        if not isinstance(raw, str):
            raise TypeError(f"{self.name} : l'exemple brut doit être une chaîne")
        vector = np.asarray(self._encode(raw), dtype=np.float32)
        if vector.shape != (self.n_inputs,):
            raise ValueError(f"{self.name} : {vector.shape} reçu, ({self.n_inputs},) attendu")
        return vector

    def decode(self, outputs: np.ndarray) -> str:
        """Identifiant de la classe de plus forte sortie (premier en cas d'égalité)."""
        scores = np.asarray(outputs, dtype=np.float32).reshape(-1)
        if scores.shape != (len(self.classes),):
            raise ValueError(f"{self.name} : {scores.size} sorties, {len(self.classes)} attendues")
        return self.class_ids[int(np.argmax(scores))]
