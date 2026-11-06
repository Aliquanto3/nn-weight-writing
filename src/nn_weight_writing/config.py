"""Configuration : seul lecteur de `config/protocol.toml` (AD-6), `models.toml` et `pricing.toml`
(AD-10, AD-11)."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
PROTOCOL_PATH = CONFIG_DIR / "protocol.toml"
MODELS_PATH = CONFIG_DIR / "models.toml"
PRICING_PATH = CONFIG_DIR / "pricing.toml"
DRIVERS = frozenset({"claude_code", "api"})
PROVIDERS = frozenset({"subscription", "openrouter", "anthropic", "fake"})


@dataclass(frozen=True)
class ProtocolConfig:
    """Paramètres figés du protocole d'écriture."""

    pass_budget: int
    turn_limit: int
    exec_timeout_s: float
    session_timeout_s: float
    max_freeze_attempts: int
    journal_schema_version: int
    protocol_sha256: str
    max_session_usd: float
    project_cap_usd: float
    lot_caps_usd: dict[int, float]

    def lot_cap_usd(self, lot: int) -> float:
        if lot not in self.lot_caps_usd:
            raise ValueError(f"lot {lot} sans plafond dans protocol.toml")
        return self.lot_caps_usd[lot]


def _positive_int(table: dict, key: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"protocol.toml : {key} doit être un entier strictement positif")
    return value


def _positive_number(table: dict, key: str, where: str = "protocol.toml") -> float:
    value = table.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool) or not value > 0:
        raise ValueError(f"{where} : {key} doit être un nombre strictement positif")
    return float(value)


def _budget(table: dict) -> tuple[float, float, dict[int, float]]:
    session = _positive_number(table, "max_session_usd")
    project = _positive_number(table, "project_cap_usd")
    raw = table.get("lot_caps_usd") or {}
    if not raw or not all(key.isdigit() for key in raw):
        raise ValueError(
            "protocol.toml : lot_caps_usd doit associer des lots (entiers) à des plafonds"
        )
    lots = {int(key): _positive_number(raw, key, "protocol.toml lot_caps_usd") for key in raw}
    if sum(lots.values()) > project + 1e-9:
        raise ValueError("protocol.toml : la somme des plafonds de lot dépasse project_cap_usd")
    if session > min(lots.values()):
        raise ValueError("protocol.toml : max_session_usd dépasse un plafond de lot")
    return session, project, lots


def load_protocol(path: Path | None = None) -> ProtocolConfig:
    """Lit et valide `protocol.toml` ; l'empreinte sha256 couvre les octets du fichier."""
    path = path or PROTOCOL_PATH
    raw = path.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    session = data.get("session", {})
    journal = data.get("journal", {})
    max_session, project_cap, lot_caps = _budget(data.get("budget", {}))
    return ProtocolConfig(
        pass_budget=_positive_int(session, "pass_budget"),
        turn_limit=_positive_int(session, "turn_limit"),
        exec_timeout_s=float(_positive_int(session, "exec_timeout_s")),
        session_timeout_s=_positive_number(session, "session_timeout_s"),
        max_freeze_attempts=_positive_int(session, "max_freeze_attempts"),
        journal_schema_version=_positive_int(journal, "schema_version"),
        protocol_sha256=hashlib.sha256(raw).hexdigest(),
        max_session_usd=max_session,
        project_cap_usd=project_cap,
        lot_caps_usd=lot_caps,
    )


@dataclass(frozen=True)
class ModelConfig:
    """Un modèle de séance : pilote, fournisseur, identifiant et réglages explicites."""

    name: str
    driver: str
    provider: str
    id: str
    effort: str | None = None
    max_tokens: int = 16000
    sampling: dict = field(default_factory=dict)
    provider_order: tuple[str, ...] = ()

    @property
    def billed(self) -> bool:
        """Faux par l'abonnement (0 $ facturé), vrai par une API (AD-11)."""
        return self.provider != "subscription"


def load_models(path: Path | None = None) -> dict[str, ModelConfig]:
    data = tomllib.loads((path or MODELS_PATH).read_text("utf-8")).get("models", {})
    models = {}
    for name, entry in data.items():
        model = ModelConfig(
            name=name,
            driver=entry["driver"],
            provider=entry["provider"],
            id=entry["id"],
            effort=entry.get("effort"),
            max_tokens=int(entry.get("max_tokens", 16000)),
            sampling=dict(entry.get("sampling", {})),
            provider_order=tuple(entry.get("provider_order", ())),
        )
        if model.driver not in DRIVERS or model.provider not in PROVIDERS:
            raise ValueError(f"models.toml : {name} : pilote ou fournisseur inconnu")
        if (model.driver == "claude_code") != (model.provider == "subscription"):
            raise ValueError(f"models.toml : {name} : claude_code va avec subscription, seul")
        models[name] = model
    return models


@dataclass(frozen=True)
class Price:
    """Tarif daté d'un modèle, en dollars par million de jetons (AD-11)."""

    input: float
    output: float
    cache_read: float
    cache_write: float
    date: str = ""
    source: str = ""
    # Écriture du cache en tranche d'une heure ; absente, celle de 5 minutes (`cache_write`).
    cache_write_1h: float | None = None


def load_pricing(path: Path | None = None) -> dict[str, Price]:
    data = tomllib.loads((path or PRICING_PATH).read_text("utf-8")).get("models", {})
    prices = {}
    for model_id, entry in data.items():
        values = {}
        for key in ("input", "output", "cache_read", "cache_write"):
            value = entry.get(key)
            if not isinstance(value, int | float) or isinstance(value, bool) or value < 0:
                raise ValueError(f"pricing.toml : {model_id} : {key} invalide")
            values[key] = float(value)
        if "cache_write_1h" in entry:
            value = entry["cache_write_1h"]
            if not isinstance(value, int | float) or isinstance(value, bool) or value < 0:
                raise ValueError(f"pricing.toml : {model_id} : cache_write_1h invalide")
            values["cache_write_1h"] = float(value)
        if not entry.get("date") or not entry.get("source"):
            raise ValueError(f"pricing.toml : {model_id} : date et source obligatoires")
        prices[model_id] = Price(**values, date=str(entry["date"]), source=entry["source"])
    return prices
