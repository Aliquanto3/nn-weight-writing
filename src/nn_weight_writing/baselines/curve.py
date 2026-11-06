"""Courbe des témoins C et F : entraînement par (tâche, N, graine) et exactitude après gel.

Importe PyTorch (via `train`) : hors de la frontière de séance (AD-1, AD-13). L'exactitude est
mesurée hors séance, `verify_frozen` d'abord, `heldout/` lu ensuite seulement.
"""

from __future__ import annotations

import json
import statistics
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

import numpy as np

from nn_weight_writing import network
from nn_weight_writing.baselines.train import _encode_for, get_task, load_train_config, train
from nn_weight_writing.evaluation.labels import read_labels
from nn_weight_writing.evaluation.score import check_alignment, run_task
from nn_weight_writing.evaluation.verify import FROZEN_DIR, verify_frozen
from nn_weight_writing.tasks.io import read_examples
from nn_weight_writing.tasks.legal.types import HELD_OUT

GROUPS = ("all", "real", "fake_known", "fake_held_out")


def _group(label: str, type_id: str) -> str:
    if label == "real":
        return "real"
    return "fake_held_out" if type_id in HELD_OUT else "fake_known"


def measure(run_dir: Path, task_name: str, heldout: Path) -> dict[str, dict[str, int]]:
    """Exactitude sur le réservé : `{groupe: {correct, n}}`, empreintes vérifiées d'abord."""
    run_dir = Path(run_dir)
    verify_frozen(run_dir)
    written = run_task(run_dir)
    if written != task_name:
        raise ValueError(f"réseau écrit pour {written!r}, jeu évalué de {task_name!r}")
    manifest, weights = network.load(run_dir / FROZEN_DIR)
    task = get_task(task_name)
    encode: Callable[[object], np.ndarray] = _encode_for(task, manifest["encoder"])
    examples = read_examples(heldout / "examples.jsonl")
    labels = read_labels(heldout / "labels.jsonl")
    check_alignment(examples, labels)
    inputs = np.stack([encode(e.raw) for e in examples])
    outputs = network.forward(manifest, weights, inputs)
    counts = {g: {"correct": 0, "n": 0} for g in GROUPS}
    for example, row in zip(examples, outputs, strict=True):
        label = labels[example.id]
        ok = task.decode(row) == label.label
        for group in ("all", _group(label.label, label.type_id)):
            counts[group]["n"] += 1
            counts[group]["correct"] += int(ok)
    return counts


def run_curve(
    task_name: str,
    data_dir: Path,
    heldout: Path,
    *,
    prepared: bool,
    runs_root: Path,
    lot: str,
    n_values: tuple[int, ...] | None = None,
    seeds: tuple[int, ...] | None = None,
    skip: Callable[[int, int], bool] | None = None,
    log: Callable[[dict], None] | None = None,
) -> list[dict]:
    """Un enregistrement par run : tâche, méthode, N, graine, durée, exactitude par groupe."""
    config = load_train_config(task_name)
    records = []
    for n in n_values or config.n_values:
        for seed in seeds or config.seeds:
            if skip and skip(n, seed):
                continue
            start = time.perf_counter()
            run_dir = train(
                task_name, data_dir, n=n, seed=seed, runs_root=runs_root, lot=lot, prepared=prepared
            )
            seconds = time.perf_counter() - start
            record = {
                "task": task_name,
                "method": "F" if prepared else "C",
                "n": n,
                "seed": seed,
                "seconds": round(seconds, 2),
                "run": run_dir.name,
                "accuracy": measure(run_dir, task_name, heldout),
            }
            records.append(record)
            if log:
                log(record)
    return records


def summarize(records: list[dict]) -> list[dict]:
    """Moyenne et écart-type (population des graines, `pstdev`) par (tâche, méthode, N, groupe)."""
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        cells[(r["task"], r["method"], r["n"])].append(r)
    rows = []
    for (task, method, n), runs in sorted(cells.items()):
        row = {
            "task": task,
            "method": method,
            "n": n,
            "seeds": [r["seed"] for r in runs],
            "seconds_mean": statistics.fmean(r["seconds"] for r in runs),
        }
        for group in GROUPS:
            values = [
                r["accuracy"][group]["correct"] / r["accuracy"][group]["n"]
                for r in runs
                if r["accuracy"][group]["n"]
            ]
            if values:
                row[group] = (statistics.fmean(values), statistics.pstdev(values))
        rows.append(row)
    return rows


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
