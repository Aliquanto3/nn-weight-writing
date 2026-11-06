"""Fixtures communes : une tâche de test minimale, un paquet de séance et un service d'outils."""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from nn_weight_writing.config import ModelConfig, Price, load_protocol
from nn_weight_writing.session.service import OpenInfo, ToolService
from nn_weight_writing.tasks.io import materialize_bundle
from nn_weight_writing.tasks.registry import TaskSpec

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

    def factory(method: str, config=None, size_target: int | None = None) -> ToolService:
        """Séance A sans `size_target` : ouverte à 10⁴ puis fenêtre levée (réseaux jouets)."""
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
            dataset="toy",
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
            size_target=size_target if size_target or method == "B" else 10_000,
        )
        service = ToolService(run_dir, LenCodec(), info, config or protocol)
        if size_target is None:
            service.size_target = None
        return service

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


# --- Pilotes et fournisseurs (1-6) ------------------------------------------------------------

FAKE_CLAUDE = Path(__file__).with_name("fake_claude.py")
TEST_PRICE = Price(input=1.0, output=2.0, cache_read=0.1, cache_write=1.25, date="t", source="t")
TASK = TaskSpec(
    name="toy",
    description="Dire si la référence est plausible.",
    codec=LenCodec(),
    vocabulary=tuple(VOCABULARY),
)


def fake_model(**overrides) -> ModelConfig:
    """Modèle du pilote API servi par le fournisseur `fake` (facturé, comme une API)."""
    values = {"name": "fake-model", "driver": "api", "provider": "fake", "id": "fake/model"}
    return ModelConfig(**{**values, **overrides})


def claude_model(**overrides) -> ModelConfig:
    values = {
        "name": "sonnet-5.5",
        "driver": "claude_code",
        "provider": "subscription",
        "id": "claude-sonnet-5-5",
        "effort": "medium",
    }
    return ModelConfig(**{**values, **overrides})


@pytest.fixture(scope="session")
def claude_cwd_root(tmp_path_factory):
    """Racine du répertoire courant de `claude` sans fichier de mémoire au-dessus (AD-14).

    Sous Windows, le dossier temporaire est sous le dossier utilisateur, qui peut porter un
    `.claude/CLAUDE.md` : repli sur un dossier à la racine du disque, supprimé à la fin.
    """
    from nn_weight_writing.session.claude_code import ancestor_memory_files

    base = tmp_path_factory.mktemp("claude-cwd")
    if not ancestor_memory_files(base):
        yield base
        return
    fallback = Path(base.anchor) / f"nnww-pytest-{uuid.uuid4().hex[:8]}"
    try:
        fallback.mkdir()
    except OSError as exc:
        pytest.skip(f"aucune racine sans CLAUDE.md au-dessus : {exc}")
    try:
        if ancestor_memory_files(fallback):
            pytest.skip(f"CLAUDE.md au-dessus de {fallback}")
        yield fallback
    finally:
        shutil.rmtree(fallback, ignore_errors=True)


@pytest.fixture
def session_env(tmp_path, protocol, claude_cwd_root):
    """Exemples, dossier des séances, registre et dossier de configuration Claude dédiés."""
    examples = write_examples(tmp_path / "examples.jsonl", EXAMPLES)
    config_dir = tmp_path / "claude-config"
    config_dir.mkdir()

    def run(model: ModelConfig, method: str = "B", **kwargs):
        from nn_weight_writing.session.run import run_session

        if method != "B":
            kwargs.setdefault("size_target", 10_000)
        params = {
            "task": TASK,
            "dataset": "toy",
            "examples": examples,
            "method": method,
            "model": model,
            "price": TEST_PRICE,
            "protocol": protocol,
            "attempt": 1,
            "seed": 7,
            "lot": 1,
            "runs_dir": tmp_path / "runs",
            "ledger_path": tmp_path / "ledger.csv",
            "claude_executable": (sys.executable, str(FAKE_CLAUDE)),
            "claude_config_dir": config_dir,
            "claude_cwd_root": claude_cwd_root,
            **kwargs,
        }
        return run_session(**params)

    return SimpleNamespace(
        run=run,
        examples=examples,
        ledger=tmp_path / "ledger.csv",
        config_dir=config_dir,
        cwd_root=claude_cwd_root,
        tmp=tmp_path,
    )


def scenario(monkeypatch, tmp_path, data: dict) -> Path:
    """Scénario du faux `claude` et fichier de capture de ce qu'il a reçu."""
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(data), "utf-8")
    capture = tmp_path / "capture.json"
    monkeypatch.setenv("NNWW_FAKE_CLAUDE_SCENARIO", str(path))
    monkeypatch.setenv("NNWW_FAKE_CLAUDE_CAPTURE", str(capture))
    return capture


def read_journal(run_dir: Path) -> list[dict]:
    return [
        json.loads(line) for line in (run_dir / "journal.jsonl").read_text("utf-8").splitlines()
    ]
