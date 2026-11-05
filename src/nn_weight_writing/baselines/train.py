"""Témoin C : entraînement PyTorch sur l'architecture de référence (CAP-7, AD-13, AD-17).

Importé seulement par import paresseux depuis `cli`. Le réseau entraîné est gelé au format de
AD-3 (`frozen/`) avec `run.json`, puis `evaluate` écrit `eval.json` : aucun évaluateur parallèle.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from nn_weight_writing.baselines import torch_layers
from nn_weight_writing.baselines.common import freeze_run, run_id
from nn_weight_writing.config import CONFIG_DIR
from nn_weight_writing.evaluation.labels import read_labels
from nn_weight_writing.evaluation.score import check_alignment
from nn_weight_writing.evaluation.verify import evaluate
from nn_weight_writing.network.io import sha256_file
from nn_weight_writing.tasks.io import read_examples
from nn_weight_writing.tasks.toy import ToyTask, get_task

TRAIN_PATH = CONFIG_DIR / "train.toml"
BASELINE = "C"
HELDOUT_DIR = "heldout"  # AD-12 : jamais lu pour entraîner (protocole-ecriture.md)


@dataclass(frozen=True)
class TrainConfig:
    hidden: tuple[int, ...]
    learning_rate: float
    epochs: int
    batch_size: int
    n_values: tuple[int, ...]
    seeds: tuple[int, ...]


def load_train_config(task: str, path: Path | None = None) -> TrainConfig:
    data = tomllib.loads((path or TRAIN_PATH).read_text("utf-8"))
    defaults = data["defaults"]
    if defaults["optimizer"] != "adam":
        raise ValueError("train.toml : seul l'optimiseur adam est implémenté")
    try:
        spec = data["tasks"][task]
    except KeyError:
        raise KeyError(f"train.toml : pas d'architecture de référence pour {task!r}") from None
    return TrainConfig(
        hidden=tuple(spec["hidden"]),
        learning_rate=float(defaults["learning_rate"]),
        epochs=int(defaults["epochs"]),
        batch_size=int(defaults["batch_size"]),
        n_values=tuple(defaults["n_values"]),
        seeds=tuple(defaults["seeds"]),
    )


def reference_manifest(task: ToyTask, config: TrainConfig) -> dict:
    """Couches cachées `relu`, sortie `identity` : une unité par classe."""
    sizes = [task.n_inputs, *config.hidden, len(task.classes)]
    layers = [
        {
            "type": "dense",
            "in": sizes[i],
            "out": sizes[i + 1],
            "activation": "relu" if i < len(sizes) - 2 else "identity",
        }
        for i in range(len(sizes) - 1)
    ]
    return {"encoder": task.encoder_id, "layers": layers}


def train_network(
    manifest: dict, inputs: np.ndarray, targets: np.ndarray, config: TrainConfig, seed: int
) -> dict[str, np.ndarray]:
    """Entraîne depuis des poids aléatoires (graine `seed`), entropie croisée, Adam, CPU."""
    torch.manual_seed(seed)
    generator = torch.Generator().manual_seed(seed)
    module = torch_layers.build_module(manifest)
    optimizer = torch.optim.Adam(module.parameters(), lr=config.learning_rate)
    loss_fn = nn.CrossEntropyLoss()
    x = torch.from_numpy(np.ascontiguousarray(inputs, dtype=np.float32))
    y = torch.from_numpy(np.ascontiguousarray(targets, dtype=np.int64))
    for _ in range(config.epochs):
        order = torch.randperm(len(x), generator=generator)
        for start in range(0, len(x), config.batch_size):
            batch = order[start : start + config.batch_size]
            optimizer.zero_grad()
            loss_fn(module(x[batch]), y[batch]).backward()
            optimizer.step()
    return torch_layers.export_weights(module)


def train(
    task_name: str,
    data_dir: Path,
    *,
    n: int,
    seed: int,
    runs_root: Path,
    lot: str,
    config_path: Path | None = None,
) -> Path:
    """Entraîne sur les `n` premiers exemples étiquetés de `data_dir`, gèle et évalue."""
    task = get_task(task_name)
    config = load_train_config(task_name, config_path)
    data_dir = Path(data_dir)
    if HELDOUT_DIR in data_dir.resolve().parts:
        raise ValueError(f"jeu réservé refusé pour l'entraînement : {data_dir}")
    examples = read_examples(data_dir / "examples.jsonl")
    labels = read_labels(data_dir / "labels.jsonl")
    check_alignment(examples, labels)
    if not 1 <= n <= len(examples):
        raise ValueError(f"n={n} hors de 1..{len(examples)} (taille du jeu {data_dir})")
    chosen = examples[:n]
    inputs = np.stack([task.encode(e.raw) for e in chosen])
    index = {cid: i for i, cid in enumerate(task.class_ids)}
    targets = np.array([index[labels[e.id].label] for e in chosen], dtype=np.int64)
    manifest = reference_manifest(task, config)
    weights = train_network(manifest, inputs, targets, config, seed)
    run_dir = Path(runs_root) / lot / "train" / run_id(task_name, BASELINE, n, seed)
    dataset = {
        "path": "/".join(data_dir.resolve().parts[-3:]),
        "files": {
            name: sha256_file(data_dir / name) for name in ("examples.jsonl", "labels.jsonl")
        },
    }
    freeze_run(run_dir, manifest, weights, baseline=BASELINE, n=n, seed=seed, dataset=dataset)
    evaluate(run_dir)
    return run_dir
