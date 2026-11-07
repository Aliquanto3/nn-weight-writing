"""Artefacts de lot écrits à la main pour les tests de 1-14 : séances, témoins, jeux réservés.

Une tâche de test `typed` (encodeur `typed.ab@1`) : l'entrée vaut [« A » présent, « B »
présent] ; classes `real` puis `fake`. Le réseau `typed_network` a une unité cachée par
lettre (et une unité neutre en option) : il dit `fake` dès qu'une lettre est présente.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from nn_weight_writing.network import io as netio
from nn_weight_writing.tasks.registry import TaskSpec

TYPED_ENCODER = "typed.ab@1"


@dataclass(frozen=True)
class TypedCodec:
    name: str = "typed"
    encoder_id: str = TYPED_ENCODER

    def encode(self, raw: object) -> np.ndarray:
        text = str(raw)
        return np.array([float("A" in text), float("B" in text)], dtype=np.float32)

    def decode(self, outputs: np.ndarray) -> str:
        scores = np.asarray(outputs, dtype=np.float32).reshape(-1)
        return ("real", "fake")[int(np.argmax(scores))]


def typed_spec(name: str = "typed") -> TaskSpec:
    return TaskSpec(name, "tâche de test", TypedCodec(name=name), ({"id": "t01"}, {"id": "t02"}))


def typed_network(neutral: bool = False) -> tuple[dict, dict[str, np.ndarray]]:
    hidden = 3 if neutral else 2
    manifest = {
        "encoder": TYPED_ENCODER,
        "layers": [
            {"type": "dense", "in": 2, "out": hidden, "activation": "relu"},
            {"type": "dense", "in": hidden, "out": 2, "activation": "identity"},
        ],
    }
    w0 = np.zeros((2, hidden), dtype=np.float32)
    w0[0, 0] = w0[1, 1] = 1.0
    w1 = np.zeros((hidden, 2), dtype=np.float32)
    w1[0, 1] = w1[1, 1] = 1.0
    weights = {
        "L0.W": w0,
        "L0.b": np.zeros(hidden, dtype=np.float32),
        "L1.W": w1,
        "L1.b": np.array([0.5, 0.0], dtype=np.float32),
    }
    return manifest, weights


TYPED_ROWS = [  # (raw, label, type_id)
    ("xAx", "fake", "t01"),
    ("yAy", "fake", "t01"),
    ("xBx", "fake", "t02"),
    ("yBy", "fake", "t02"),
    ("zzz", "real", "real"),
    ("www", "real", "real"),
]


def write_heldout(
    root: Path,
    task: str,
    dataset: str,
    rows: list[tuple[str, str, str]],
    held_out_types: list[str] | None = None,
) -> Path:
    """`heldout/<task>/<dataset>/` au format d'AD-16, empreintes dans `dataset.json`."""
    directory = Path(root) / task / dataset
    directory.mkdir(parents=True, exist_ok=True)
    examples = "".join(
        json.dumps({"id": f"{task}-h{i:03d}", "raw": raw}) + "\n"
        for i, (raw, _, _) in enumerate(rows)
    )
    labels = "".join(
        json.dumps({"id": f"{task}-h{i:03d}", "label": lab, "type_id": t}) + "\n"
        for i, (_, lab, t) in enumerate(rows)
    )
    (directory / "examples.jsonl").write_bytes(examples.encode())
    (directory / "labels.jsonl").write_bytes(labels.encode())
    meta: dict = {
        "files": {
            "examples.jsonl": netio.sha256_bytes(examples.encode()),
            "labels.jsonl": netio.sha256_bytes(labels.encode()),
        },
        "composition": {"task": task},
    }
    if held_out_types is not None:
        meta["composition"]["held_out_types"] = held_out_types
    (directory / "dataset.json").write_text(json.dumps(meta), "utf-8")
    return directory


def _event(seq: int, ts: str, kind: str, **fields) -> dict:
    return {"schema_version": 1, "seq": seq, "ts": ts, "type": kind, **fields}


def write_session(
    lot_dir: Path,
    *,
    task: str = "typed",
    method: str = "A-literal",
    model: str = "test-model",
    attempt: int = 1,
    stamp: str = "20261107T000000Z",
    frozen: bool = True,
    network: tuple[dict, dict] | None = None,
    blocks: list | None = None,
    rules: str | None = None,
    flags: list | None = None,
    billed: float = 0.0,
    equiv: float = 0.25,
    effort: str | None = "medium",
    driver: str = "claude_code",
) -> Path:
    """Séance au format d'AD-7 et AD-12 : journal complet, `frozen/` aux empreintes exactes."""
    session_id = f"{task}-{method}-{model}-t{attempt}-{stamp}"
    run_dir = Path(lot_dir) / session_id
    (run_dir / "frozen").mkdir(parents=True)
    ts = f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z"
    events = [
        _event(
            0,
            ts,
            "open",
            session_id=session_id,
            task=task,
            dataset="session",
            dataset_sha256="0" * 64,
            method=method,
            model=model,
            driver=driver,
            provider="subscription" if driver == "claude_code" else "fake",
            attempt=attempt,
            seed=attempt - 1,
            pass_budget=20,
            protocol_sha256="1" * 64,
            system_prompt_sha256="2" * 64,
            sampling={},
            effort=effort,
            size_target=None if method == "B" else 10000,
        ),
        _event(
            1,
            ts,
            "model_call",
            input_tokens=10,
            output_tokens=20,
            cache_read_tokens=30,
            cache_write_tokens=40,
            cost_equiv_usd=equiv,
            billed_usd=billed,
            provider_cost=None,
            duration_s=1.0,
            exchange={},
        ),
        _event(
            2,
            ts,
            "script_run",
            tool="run_script",
            code_sha256="3" * 64,
            ok=True,
            log="",
            flags=flags or [],
            duration_s=0.1,
            error=None,
        ),
    ]
    if frozen:
        files: dict[str, bytes] = {}
        if rules is not None:
            files["rules.py"] = rules.encode("utf-8")
        else:
            manifest, weights = network or typed_network()
            files["manifest.json"] = netio.manifest_bytes(manifest)
            files["weights.npz"] = netio.weights_bytes(manifest, weights)
        digests = {}
        for name, data in files.items():
            (run_dir / "frozen" / name).write_bytes(data)
            digests[name] = netio.sha256_bytes(data)
        events.append(
            _event(
                3,
                ts,
                "freeze",
                files=digests,
                tree_sha256=netio.tree_sha256(digests),
                valid=True,
                blocks=blocks,
                size_nominal=0 if rules else 14,
                size_script_bytes=0,
                size_weights_zlib=10,
            )
        )
    reason = "frozen" if frozen else "pass_budget"
    events.append(
        _event(
            len(events),
            ts,
            "end",
            reason=reason,
            passes_used=1,
            totals={"duration_s": 120.0},
            detail=None,
        )
    )
    (run_dir / "journal.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), "utf-8")
    return run_dir


def write_baseline(
    lot_dir: Path,
    *,
    task: str = "typed",
    baseline: str = "C",
    n: int = 64,
    seed: int = 0,
    chemin: str = "",
    retrained_from: str | None = None,
    network: tuple[dict, dict] | None = None,
) -> Path:
    """Témoin `**/train/<run_id>/` avec `run.json` (AD-17)."""
    suffix = f"-retrain-n{n}-s{seed}" if retrained_from else f"-{baseline}-n{n}-s{seed}"
    run_id = (retrained_from or task) + suffix
    base = Path(lot_dir) / chemin if chemin else Path(lot_dir)
    run_dir = base / "train" / run_id
    (run_dir / "frozen").mkdir(parents=True)
    manifest, weights = network or typed_network()
    files = {
        "manifest.json": netio.manifest_bytes(manifest),
        "weights.npz": netio.weights_bytes(manifest, weights),
    }
    digests = {}
    for name, data in files.items():
        (run_dir / "frozen" / name).write_bytes(data)
        digests[name] = netio.sha256_bytes(data)
    dataset: dict = {"path": f"data/{task}/train", "files": {}}
    if retrained_from:
        dataset["retrained_from"] = {"session": retrained_from, "tree_sha256": "0" * 64}
    record = {
        "run_id": run_id,
        "baseline": baseline,
        "n": n,
        "seed": seed,
        "files": digests,
        "tree_sha256": netio.tree_sha256(digests),
        "schema_version": 1,
        "dataset": dataset,
        "task": task,
    }
    (run_dir / "run.json").write_text(json.dumps(record), "utf-8")
    return run_dir
