"""Configuration du protocole : seul lecteur de `config/protocol.toml` (AD-6)."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
PROTOCOL_PATH = CONFIG_DIR / "protocol.toml"


@dataclass(frozen=True)
class ProtocolConfig:
    """Paramètres figés du protocole d'écriture."""

    pass_budget: int
    turn_limit: int
    exec_timeout_s: float
    max_freeze_attempts: int
    journal_schema_version: int
    protocol_sha256: str


def _positive_int(table: dict, key: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"protocol.toml : {key} doit être un entier strictement positif")
    return value


def load_protocol(path: Path | None = None) -> ProtocolConfig:
    """Lit et valide `protocol.toml` ; l'empreinte sha256 couvre les octets du fichier."""
    path = path or PROTOCOL_PATH
    raw = path.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    session = data.get("session", {})
    journal = data.get("journal", {})
    return ProtocolConfig(
        pass_budget=_positive_int(session, "pass_budget"),
        turn_limit=_positive_int(session, "turn_limit"),
        exec_timeout_s=float(_positive_int(session, "exec_timeout_s")),
        max_freeze_attempts=_positive_int(session, "max_freeze_attempts"),
        journal_schema_version=_positive_int(journal, "schema_version"),
        protocol_sha256=hashlib.sha256(raw).hexdigest(),
    )
