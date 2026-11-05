"""Lecteur d'exemples et paquet de séance (AD-2, AD-16).

Le paquet `bundle/` se matérialise depuis le seul fichier d'exemples non annotés : chaque
ligne n'y porte que `id` et `raw`, et toute autre clé fait refuser le fichier. La
description de tâche et le vocabulaire fermé des types visibles sont fournis par la tâche.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

EXAMPLE_KEYS = frozenset({"id", "raw"})
VOCAB_KEYS = frozenset({"id", "description"})
TASK_FILE = "task.json"
EXAMPLES_FILE = "examples.jsonl"


class BundleError(ValueError):
    """Fichier d'exemples ou paquet de séance non conforme."""


@dataclass(frozen=True)
class Example:
    id: str
    raw: object


@dataclass(frozen=True)
class VocabularyEntry:
    id: str
    description: str


@dataclass(frozen=True)
class Bundle:
    task: str
    description: str
    encoder: str
    vocabulary: tuple[VocabularyEntry, ...]
    examples: tuple[Example, ...]

    @property
    def vocabulary_ids(self) -> frozenset[str]:
        return frozenset(entry.id for entry in self.vocabulary)


def read_examples(path: Path) -> list[Example]:
    """Lit `id` et `raw` seulement ; refuse toute ligne qui porte une autre clé."""
    examples: list[Example] = []
    seen: set[str] = set()
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or set(record) != EXAMPLE_KEYS:
                keys = sorted(record) if isinstance(record, dict) else type(record).__name__
                raise BundleError(f"ligne {number} : clés {keys}, attendu exactement id et raw")
            if not isinstance(record["id"], str) or record["id"] in seen:
                raise BundleError(f"ligne {number} : id absent ou en double")
            seen.add(record["id"])
            examples.append(Example(record["id"], record["raw"]))
    if not examples:
        raise BundleError("aucun exemple")
    return examples


def _vocabulary(entries: list[dict]) -> tuple[VocabularyEntry, ...]:
    out: list[VocabularyEntry] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != VOCAB_KEYS:
            raise BundleError("entrée de vocabulaire : clés id et description seulement")
        if not all(isinstance(entry[k], str) and entry[k].strip() for k in VOCAB_KEYS):
            raise BundleError("entrée de vocabulaire : id et description non vides")
        out.append(VocabularyEntry(entry["id"], entry["description"]))
    if not out or len({e.id for e in out}) != len(out):
        raise BundleError("vocabulaire vide ou identifiant en double")
    return tuple(out)


def materialize_bundle(
    examples_path: Path,
    bundle_dir: Path,
    *,
    task: str,
    description: str,
    encoder: str,
    vocabulary: list[dict],
) -> Bundle:
    """Écrit `bundle/` (`task.json`, `examples.jsonl`) dans un dossier neuf ou vide."""
    bundle_dir = Path(bundle_dir)
    if bundle_dir.exists() and any(bundle_dir.iterdir()):
        raise BundleError(f"paquet déjà matérialisé : {bundle_dir}")
    examples = read_examples(examples_path)
    vocab = _vocabulary(vocabulary)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "task": task,
        "description": description,
        "encoder": encoder,
        "vocabulary": [{"id": e.id, "description": e.description} for e in vocab],
    }
    (bundle_dir / TASK_FILE).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with open(bundle_dir / EXAMPLES_FILE, "w", encoding="utf-8", newline="\n") as handle:
        for example in examples:
            line = json.dumps({"id": example.id, "raw": example.raw}, ensure_ascii=False)
            handle.write(line + "\n")
    return read_bundle(bundle_dir)


def read_bundle(bundle_dir: Path) -> Bundle:
    """Lit le paquet : les outils de séance ne lisent que ce dossier (AD-2)."""
    bundle_dir = Path(bundle_dir)
    meta = json.loads((bundle_dir / TASK_FILE).read_text("utf-8"))
    if set(meta) != {"task", "description", "encoder", "vocabulary"}:
        raise BundleError("task.json : clés inattendues")
    return Bundle(
        task=meta["task"],
        description=meta["description"],
        encoder=meta["encoder"],
        vocabulary=_vocabulary(meta["vocabulary"]),
        examples=tuple(read_examples(bundle_dir / EXAMPLES_FILE)),
    )
