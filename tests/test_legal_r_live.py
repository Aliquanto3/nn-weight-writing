"""Appels réels à Judilibre (story 1-12, D5), marqués `live` et désélectionnés par défaut.

Lancer : `uv run pytest -m live tests/test_legal_r_live.py`. La clé est lue dans
`JUDILIBRE_KEY_ID`, sinon dans le `.env` du dépôt principal ; elle n'est jamais affichée.
Trois requêtes au plus, sans cache.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from nn_weight_writing.datasets.legal_r.judilibre import JudilibreClient

pytestmark = pytest.mark.live
SCRIPT = Path(__file__).parents[1] / "scripts" / "pre_etude_r.py"


@pytest.fixture(scope="module")
def client():
    spec = importlib.util.spec_from_file_location("pre_etude_r_live", SCRIPT)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    try:
        key = script.load_key(script.main_repo_env())
    except Exception:
        pytest.skip("JUDILIBRE_KEY_ID absente")
    return JudilibreClient(key)


def test_perruche_scan_abridged(client):
    results = client.scan_day("cc", "2000-11-17")
    (perruche,) = [r for r in results if r.get("number") == "99-13.701"]
    assert perruche["chamber"] == "pl" and perruche["decision_date"] == "2000-11-17"
    assert "99-13.701" in perruche["numbers"]
    for field in ("number", "numbers", "chamber", "decision_date"):
        assert field in perruche


def test_invented_number_absent(client):
    found = client.search_number("99-99.999", "cc", max_pages=1)
    assert all("99-99.999" not in {r.get("number"), *(r.get("numbers") or [])} for r in found)
    perruche = client.search_number("99-13.701", "cc", max_pages=1)
    assert any(r.get("number") == "99-13.701" for r in perruche)
