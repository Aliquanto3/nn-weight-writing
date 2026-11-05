"""Écrivain unique du journal de séance (AD-7) : ajout seul, `seq` croissant, aucun secret."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from nn_weight_writing.journal.schema import Event

# Motifs de clé d'API et d'en-têtes HTTP d'authentification : masqués avant écriture.
SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-or-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)\b(x-api-key|authorization)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}"),
)
SECRET_ENV_VARS = ("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY")
REDACTED = "[secret masqué]"


def json_safe(value: object) -> object:
    """Remplace les flottants non finis par leur texte : le journal reste du JSON strict."""
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [json_safe(v) for v in value]
    return value


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def redact(text: str) -> str:
    """Masque les motifs de clé et les valeurs des variables de clé présentes."""
    for name in SECRET_ENV_VARS:
        value = os.environ.get(name)
        if value and len(value) >= 8:
            text = text.replace(value, REDACTED)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text


class JournalWriter:
    """Ouvre un journal neuf (jamais un journal existant) et y ajoute des événements."""

    def __init__(self, path: Path, schema_version: int) -> None:
        self.path = Path(path)
        self.schema_version = schema_version
        self.seq = 0
        self._handle = open(self.path, "x", encoding="utf-8", newline="\n")

    def write(self, event: Event) -> dict:
        record = {
            "schema_version": self.schema_version,
            "seq": self.seq,
            "ts": utc_now(),
            "type": event.TYPE,
            **json_safe(asdict(event)),
        }
        line = json.dumps(record, ensure_ascii=False, allow_nan=False)
        try:
            line.encode("utf-8")
        except UnicodeEncodeError:
            # Substitut isolé (échappement JSON `\ud800`) : échappé, le journal reste UTF-8.
            line = json.dumps(record, ensure_ascii=True, allow_nan=False)
        line = redact(line)
        self._handle.write(line + "\n")
        self._handle.flush()
        self.seq += 1
        return record

    def close(self) -> None:
        if not self._handle.closed:
            self._handle.close()
