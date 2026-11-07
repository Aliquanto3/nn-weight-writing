"""Index local de l'open data du Conseil d'État (story 1-12, D5).

Télécharge les archives mensuelles du Conseil d'État (`opendata.justice-administrative.fr/DCE/`,
Licence Ouverte 2.0) de septembre 2021 au dernier mois publié, garde les métadonnées de chaque
décision (`ce_index.KEPT_TAGS`) et supprime l'archive après indexation (elle porte le texte
intégral).

Usage :
    uv run python scripts/index_ce_opendata.py [--sortie data/r/ce_index] [--confirmer]

Le premier mois est téléchargé et mesuré ; si l'estimation du total dépasse 2 Go, le script
s'arrête et demande `--confirmer`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from nn_weight_writing.datasets.legal_r.ce_index import CeIndex, parse_archive

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://opendata.justice-administrative.fr"
LISTING = f"{BASE}/DCE/"
FIRST_MONTH = "202109"
CONFIRM_ABOVE = 2 * 1024**3
_HREF = re.compile(r'href="(/DCE/(\d{4})/(\d{2})/CE_(\d{6})\.zip)"', re.IGNORECASE)


def _get(url: str, timeout: int = 600) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "nn-weight-writing/1-12"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - https fixe
        return response.read()


def list_archives(listing_html: str) -> list[tuple[str, str]]:
    """(mois AAAAMM, URL) des archives du Conseil d'État à partir de septembre 2021."""
    found = {m[4]: BASE + m[1] for m in _HREF.finditer(listing_html)}
    return sorted((month, url) for month, url in found.items() if month >= FIRST_MONTH)


def _download(url: str, workdir: Path) -> Path:
    """Télécharge dans un dossier neuf et vide (données non fiables)."""
    target_dir = Path(tempfile.mkdtemp(dir=workdir))
    target = target_dir / url.rsplit("/", 1)[1]
    for attempt in range(3):
        try:
            target.write_bytes(_get(url))
            return target
        except OSError:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("inatteignable")


def build(out_dir: Path, *, confirm: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = out_dir / "tmp"
    workdir.mkdir(exist_ok=True)
    archives = list_archives(_get(LISTING, timeout=60).decode("utf-8", "replace"))
    if not archives:
        raise SystemExit("aucune archive trouvée sur la page de téléchargement")
    index = CeIndex()
    manifest: dict = {
        "source": LISTING,
        "licence": "Licence Ouverte 2.0 (CGU du 18 janvier 2022)",
        "started_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "archives": {},
    }
    total_bytes = 0
    for i, (month, url) in enumerate(archives):
        path = _download(url, workdir)
        data = path.read_bytes()
        size = len(data)
        total_bytes += size
        records = list(parse_archive(path))
        shutil.rmtree(path.parent)
        for record in records:
            index.add(record)
        manifest["archives"][path.name] = {
            "month": month,
            "url": url,
            "sha256": hashlib.sha256(data).hexdigest(),
            "octets": size,
            "decisions": len(records),
            "downloaded_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if i == 0:
            estimate = size * len(archives)
            print(
                f"premier mois {month} : {size / 1e6:.1f} Mo, {len(records)} décisions ; "
                f"estimation {estimate / 1e6:.0f} Mo pour {len(archives)} archives",
                flush=True,
            )
            if estimate > CONFIRM_ABOVE and not confirm:
                raise SystemExit("estimation au-delà de 2 Go : relancer avec --confirmer")
        elif i % 10 == 0:
            print(f"{i + 1}/{len(archives)} archives", flush=True)
    shutil.rmtree(workdir, ignore_errors=True)
    index.save(out_dir / "index.jsonl")
    manifest["finished_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest["total_octets"] = total_bytes
    manifest["decisions"] = len(index)
    manifest["max_date_lecture"] = index.max_date()
    manifest["index_sha256"] = hashlib.sha256((out_dir / "index.jsonl").read_bytes()).hexdigest()
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sortie", type=Path, default=ROOT / "data" / "r" / "ce_index")
    parser.add_argument("--confirmer", action="store_true")
    args = parser.parse_args(argv)
    manifest = build(args.sortie, confirm=args.confirmer)
    print(
        f"{manifest['decisions']} décisions, {len(manifest['archives'])} archives, "
        f"{manifest['total_octets'] / 1e6:.1f} Mo téléchargés ; "
        f"dernière lecture {manifest['max_date_lecture']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
