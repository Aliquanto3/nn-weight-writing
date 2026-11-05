"""Lecteur des étiquettes (AD-16) : réservé à `evaluation/` et aux témoins, jamais à la séance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LABEL_KEYS = frozenset({"id", "label", "type_id"})


class LabelsError(ValueError):
    """Fichier d'étiquettes non conforme."""


@dataclass(frozen=True)
class Label:
    id: str
    label: str
    type_id: str


def read_labels(path: Path) -> dict[str, Label]:
    """Lit `labels.jsonl` : exactement `id`, `label`, `type_id` par ligne, identifiants uniques."""
    labels: dict[str, Label] = {}
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or set(record) != LABEL_KEYS:
                raise LabelsError(f"ligne {number} : clés attendues {sorted(LABEL_KEYS)}")
            if not all(isinstance(record[k], str) for k in LABEL_KEYS):
                raise LabelsError(f"ligne {number} : id, label et type_id doivent être du texte")
            if record["id"] in labels:
                raise LabelsError(f"ligne {number} : id en double {record['id']!r}")
            labels[record["id"]] = Label(record["id"], record["label"], record["type_id"])
    if not labels:
        raise LabelsError("aucune étiquette")
    return labels
