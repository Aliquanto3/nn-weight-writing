"""Lecteur du journal de séance (AD-7), sur le même schéma que l'écrivain."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from nn_weight_writing.journal.schema import ENVELOPE, EVENT_TYPES, OPTIONAL_FIELDS, event_fields


class JournalError(ValueError):
    """Ligne de journal non conforme au schéma."""


def read_records(path: Path) -> Iterator[dict]:
    """Lit les lignes, vérifie l'enveloppe, `seq` croissant depuis 0 et les champs du type."""
    with open(path, encoding="utf-8") as handle:
        for expected, line in enumerate(handle):
            record = json.loads(line)
            if any(key not in record for key in ENVELOPE):
                raise JournalError(f"ligne {expected} : enveloppe incomplète")
            if record["seq"] != expected:
                raise JournalError(f"ligne {expected} : seq {record['seq']}")
            cls = EVENT_TYPES.get(record["type"])
            if cls is None:
                raise JournalError(f"ligne {expected} : type inconnu {record['type']!r}")
            missing = [
                name
                for name in event_fields(cls)
                if name not in record and name not in OPTIONAL_FIELDS
            ]
            if missing:
                raise JournalError(f"ligne {expected} : champs manquants {missing}")
            yield record


def find_last(path: Path, event_type: str) -> dict | None:
    found = None
    for record in read_records(path):
        if record["type"] == event_type:
            found = record
    return found
