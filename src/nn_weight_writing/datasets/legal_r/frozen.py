"""Lecture de la collecte figée de 1-12a (story 1-12, D1).

L'empreinte du manifeste est comparée à celle consignée, puis celle de chaque fichier lu est
comparée au manifeste, **avant** de décoder la moindre ligne. Seul `collecte.jsonl` est lu
(`pilote.jsonl` est exclu : il doublerait des citations).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

COLLECTION_FILE = "collecte.jsonl"
REQUESTS_FILE = "requetes.json"
MANIFEST_FILE = "manifest.json"
FIELDS = ("request_id", "model", "digest", "response", "done_reason", "timestamp_utc")


class CollectionError(ValueError):
    """Collecte refusée : fichier manquant, empreinte différente ou ligne tronquée."""


@dataclass(frozen=True)
class Generation:
    request_id: str
    model: str
    digest: str
    response: str
    done_reason: str | None
    timestamp_utc: str

    @property
    def generation_date(self) -> str:
        return self.timestamp_utc[:10]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _checked(directory: Path, manifest: dict, name: str) -> bytes:
    path = directory / name
    if not path.is_file():
        raise CollectionError(f"fichier absent : {name}")
    entry = (manifest.get("fichiers") or {}).get(name)
    if not entry or "sha256" not in entry:
        raise CollectionError(f"{name} absent du manifeste")
    data = path.read_bytes()
    if sha256_bytes(data) != entry["sha256"]:
        raise CollectionError(f"empreinte de {name} différente du manifeste")
    return data


def read_collection(
    directory: Path, *, manifest_sha256: str, requests_path: Path | None = None
) -> list[Generation]:
    """Générations de `collecte.jsonl`, après contrôle des empreintes (D1, AC1).

    `requests_path` : `requetes.json` figé ; s'il est donné, son empreinte doit être celle du
    manifeste et chaque `prompt` et `settings` relus sont contrôlés contre lui.
    """
    directory = Path(directory)
    manifest_path = directory / MANIFEST_FILE
    if not manifest_path.is_file():
        raise CollectionError("manifest.json absent")
    manifest_bytes = manifest_path.read_bytes()
    if sha256_bytes(manifest_bytes) != manifest_sha256.lower():
        raise CollectionError("empreinte du manifeste différente de --manifeste-sha256")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    data = _checked(directory, manifest, COLLECTION_FILE)
    prompts: dict[str, str] | None = None
    if requests_path is not None:
        request_bytes = Path(requests_path).read_bytes()
        entry = (manifest.get("fichiers") or {}).get(REQUESTS_FILE) or {}
        if sha256_bytes(request_bytes) != entry.get("sha256"):
            raise CollectionError("empreinte de requetes.json différente du manifeste")
        prompts = {r["id"]: r["prompt"] for r in json.loads(request_bytes.decode("utf-8"))}
    text = data.decode("utf-8")
    if text and not text.endswith("\n"):
        raise CollectionError("collecte.jsonl : dernière ligne tronquée")
    out: list[Generation] = []
    settings_seen: set[str] = set()
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise CollectionError(f"collecte.jsonl : ligne {number} illisible") from error
        missing = [k for k in FIELDS if k not in row]
        if missing:
            raise CollectionError(f"collecte.jsonl : ligne {number} sans {missing}")
        if prompts is not None and prompts.get(row["request_id"]) != row.get("prompt"):
            raise CollectionError(f"collecte.jsonl : ligne {number}, prompt différent")
        settings_seen.add(json.dumps(row.get("settings"), sort_keys=True))
        out.append(Generation(**{k: row[k] for k in FIELDS}))
    if len(settings_seen) > 1:
        raise CollectionError("collecte.jsonl : réglages différents entre générations")
    return out
