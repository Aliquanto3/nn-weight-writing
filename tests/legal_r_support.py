"""Doubles de frontière pour les tests de la pré-étude R (story 1-12) : transport HTTP et horloge.

Aucun module du projet n'est remplacé : seul le transport réseau de `JudilibreClient` et
l'horloge sont injectés.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from nn_weight_writing.datasets.legal_r.judilibre import BASE_URL, JudilibreClient

FIXTURES = Path(__file__).parent / "fixtures" / "legal_r"
KEY = "KeyId-fictive-123"
RATE_OK = (
    '[{"window":62204,"type":"throttle","remaining":999999},'
    '{"window":0,"type":"throttle","remaining":19}]'
)


def body(name: str) -> bytes:
    return (FIXTURES / "judilibre" / name).read_bytes()


def ok(name_or_data, rate: str = RATE_OK) -> tuple[int, dict, bytes]:
    data = body(name_or_data) if isinstance(name_or_data, str) else json.dumps(name_or_data)
    if isinstance(data, str):
        data = data.encode("utf-8")
    return 200, {"x-rate-limit": rate, "content-type": "application/json"}, data


EMPTY_SCAN = {"total": 0, "next_batch": None, "previous_batch": None, "results": []}
EMPTY_SEARCH = {"total": 0, "next_page": None, "relaxed": True, "results": []}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class FakeTransport:
    """Routes : (chemin, paramètres partiels) -> réponses consommées dans l'ordre."""

    def __init__(self, routes: list[tuple[str, dict, list]], clock: FakeClock | None = None):
        self.routes = [(path, params, list(responses)) for path, params, responses in routes]
        self.calls: list[tuple[str, dict, float | None]] = []
        self.clock = clock

    def __call__(self, url: str, headers):
        assert url.startswith(BASE_URL)
        parts = urlsplit(url)
        path = parts.path[len(urlsplit(BASE_URL).path) :]
        params = dict(parse_qsl(parts.query))
        self.calls.append((url, dict(headers), self.clock.now if self.clock else None))
        for route_path, route_params, responses in self.routes:
            if route_path == path and all(params.get(k) == str(v) for k, v in route_params.items()):
                if len(responses) > 1:
                    return responses.pop(0)
                return responses[0]
        raise AssertionError(f"route absente : {path} {params}")


def make_client(transport: FakeTransport, clock: FakeClock, cache_dir: Path | None = None):
    return JudilibreClient(
        KEY, fetch=transport, cache_dir=cache_dir, sleep=clock.sleep, clock=clock.monotonic
    )


def ce_archive(target: Path) -> Path:
    """Archive zip des trois XML écrits à la main au schéma de l'open data du CE."""
    with zipfile.ZipFile(target, "w") as archive:
        for xml in sorted((FIXTURES / "ce").glob("*.xml")):
            archive.write(xml, xml.name)
    return target
