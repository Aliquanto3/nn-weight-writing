"""Fixtures communes : une tâche de test minimale, un paquet de séance et un service d'outils."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from nn_weight_writing.config import load_protocol
from nn_weight_writing.session.service import OpenInfo, ToolService
from nn_weight_writing.tasks.io import materialize_bundle

ENCODER = "test.len@1"
VOCABULARY = [
    {"id": "T1", "description": "Référence trop courte"},
    {"id": "T2", "description": "Référence sans chiffre"},
]
EXAMPLES = [
    {"id": "e1", "raw": "Cass. civ. 1re, 12 mai 2021, n° 19-12.345"},
    {"id": "e2", "raw": "CE, 3 juin 2020"},
    {"id": "e3", "raw": "sans aucun chiffre ici"},
]


class LenCodec:
    """Encodeur de test : longueur et nombre de chiffres, divisés par 10."""

    encoder_id = ENCODER

    def encode(self, raw: object) -> np.ndarray:
        text = str(raw)
        return np.array([len(text) / 10, sum(c.isdigit() for c in text) / 10], dtype=np.float32)

    def decode(self, outputs: np.ndarray) -> object:
        return "ok" if float(outputs[0]) > 0 else "err"


def write_examples(path: Path, records: list[dict]) -> Path:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), "utf-8")
    return path


@pytest.fixture
def protocol():
    return load_protocol()


@pytest.fixture
def make_service(tmp_path, protocol):
    """Fabrique un service neuf pour une méthode, avec son paquet matérialisé."""
    counter = iter(range(1000))

    def factory(method: str, config=None) -> ToolService:
        run_dir = tmp_path / f"toy-{method}-test-t1-{next(counter)}"
        source = write_examples(tmp_path / "examples.jsonl", EXAMPLES)
        materialize_bundle(
            source,
            run_dir / "bundle",
            task="toy",
            description="Dire si la référence est plausible.",
            encoder=ENCODER,
            vocabulary=VOCABULARY,
        )
        info = OpenInfo(
            task="toy",
            dataset="toy-dev",
            dataset_sha256="0" * 64,
            method=method,
            model="test-model",
            driver="test-driver",
            provider="test-provider",
            attempt=1,
            seed=7,
            system_prompt_sha256="1" * 64,
            sampling={"temperature": 1.0},
            effort="medium",
        )
        return ToolService(run_dir, LenCodec(), info, config or protocol)

    return factory


def journal_records(service: ToolService) -> list[dict]:
    path = service.run_dir / "journal.jsonl"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


MANIFEST = {
    "encoder": ENCODER,
    "layers": [
        {"type": "dense", "in": 2, "out": 3, "activation": "relu"},
        {"type": "dense", "in": 3, "out": 1, "activation": "identity"},
    ],
}

BLOCKS = [
    {"rule": "longueur", "types": ["T1"], "units": [[0, 0], [0, 1]]},
    {"rule": "chiffres", "types": ["T2"], "units": [[0, 2]]},
]


def write_literal_network(service: ToolService) -> None:
    """Déclare MANIFEST et écrit tous ses poids par l'outil write_weights."""
    assert service.call("declare_network", {"manifest": MANIFEST})["declared"] is True
    calls = [
        ("0", "W", [[1, 0, 0.5], [0, 1, 0.5]]),
        ("0", "b", [0, 0, 0]),
        ("1", "W", [[1], [1], [-1]]),
        ("1", "b", [0.25]),
    ]
    for layer, param, rows in calls:
        result = service.call(
            "write_weights", {"layer": int(layer), "param": param, "row_start": 0, "rows": rows}
        )
        assert "written" in result, result
