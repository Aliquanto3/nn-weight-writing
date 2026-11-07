"""Index local de l'open data du Conseil d'État (story 1-12, D5) : métadonnées seules.

`parse_archive` lit chaque XML d'une archive zip en flux et ne garde que `KEPT_TAGS` ; le texte
intégral n'est jamais copié. `CeIndex` cherche par numéro normalisé.
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterable, Iterator
from pathlib import Path

from nn_weight_writing.datasets.legal_r.normalize import normalize_number

KEPT_TAGS = (
    "Numero_Dossier",
    "Date_Lecture",
    "Numero_ECLI",
    "Formation_Jugement",
    "Code_Publication",
    "Type_Decision",
    "Date_Mise_Jour",
)


def parse_archive(path: Path) -> Iterator[dict]:
    """Une décision par XML de l'archive : `KEPT_TAGS` seulement (texte nettoyé des espaces)."""
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.lower().endswith(".xml"):
                continue
            record: dict[str, str] = {}
            try:
                with archive.open(name) as handle:
                    for _event, element in ET.iterparse(handle, events=("end",)):
                        tag = element.tag
                        if tag in KEPT_TAGS and tag not in record:
                            record[tag] = " ".join((element.text or "").split())
                        element.clear()
            except ET.ParseError:
                # XML mal formé (préfixe non déclaré, vu en 2024) : balises gardées seules.
                record = _tolerant(archive.read(name))
            if record.get("Numero_Dossier"):
                yield record


def _tolerant(data: bytes) -> dict[str, str]:
    text = data.decode("utf-8", "replace")
    record = {}
    for tag in KEPT_TAGS:
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        if match:
            record[tag] = " ".join(html.unescape(match.group(1)).split())
    return record


class CeIndex:
    def __init__(self, records: Iterable[dict] = ()) -> None:
        self.records: list[dict] = []
        self._by_number: dict[str, list[dict]] = {}
        for record in records:
            self.add(record)

    def add(self, record: dict) -> None:
        clean = {k: record[k] for k in KEPT_TAGS if k in record}
        self.records.append(clean)
        number = normalize_number(clean.get("Numero_Dossier"), "ce")
        if number:
            self._by_number.setdefault(number, []).append(clean)

    def lookup(self, number: str | None) -> list[dict]:
        return list(self._by_number.get(normalize_number(number, "ce") or "", []))

    def max_date(self) -> str | None:
        dates = [r["Date_Lecture"] for r in self.records if r.get("Date_Lecture")]
        return max(dates) if dates else None

    def __len__(self) -> int:
        return len(self.records)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(
            self.records, key=lambda r: (r.get("Date_Lecture", ""), r.get("Numero_Dossier", ""))
        )
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in ordered:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    @classmethod
    def load(cls, path: Path) -> CeIndex:
        with Path(path).open(encoding="utf-8") as handle:
            return cls(json.loads(line) for line in handle if line.strip())
