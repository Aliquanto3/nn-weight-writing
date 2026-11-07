"""Écriture d'un jeu (AD-16) : `examples.jsonl`, `labels.jsonl`, `dataset.json`."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from nn_weight_writing.network.io import atomic_write_bytes, sha256_bytes

EXAMPLES_FILE = "examples.jsonl"
LABELS_FILE = "labels.jsonl"
META_FILE = "dataset.json"


@dataclass(frozen=True)
class Row:
    id: str
    raw: str
    label: str
    type_id: str


def _jsonl(records: list[dict]) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records).encode("utf-8")


def write_dataset(
    directory: Path,
    rows: list[Row],
    *,
    generator: str,
    version: int,
    seed: int,
    composition: dict | None = None,
    extra_files: dict[str, bytes] | None = None,
) -> Path:
    """Écrit le jeu dans un dossier neuf ou vide ; `dataset.json` porte les sha256 des fichiers.

    `extra_files` : fichiers compagnons (par exemple `sources.jsonl` de R), écrits et empreintés
    dans `files` comme les deux autres."""
    for name in extra_files or {}:
        if name in {EXAMPLES_FILE, LABELS_FILE, META_FILE} or Path(name).name != name:
            raise ValueError(f"fichier compagnon refusé : {name!r}")
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"jeu déjà présent : {directory}")
    directory.mkdir(parents=True, exist_ok=True)
    examples = _jsonl([{"id": r.id, "raw": r.raw} for r in rows])
    labels = _jsonl([{"id": r.id, "label": r.label, "type_id": r.type_id} for r in rows])
    atomic_write_bytes(directory / EXAMPLES_FILE, examples)
    atomic_write_bytes(directory / LABELS_FILE, labels)
    files = {EXAMPLES_FILE: sha256_bytes(examples), LABELS_FILE: sha256_bytes(labels)}
    for name, data in (extra_files or {}).items():
        atomic_write_bytes(directory / name, data)
        files[name] = sha256_bytes(data)
    meta = {
        "generator": generator,
        "version": version,
        "seed": seed,
        "n": len(rows),
        "files": files,
    }
    if composition is not None:
        meta["composition"] = composition
    atomic_write_bytes(
        directory / META_FILE,
        (json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return directory
