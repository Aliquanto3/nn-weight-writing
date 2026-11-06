"""Témoins C et F : entraînement PyTorch sur l'architecture de référence (CAP-7, AD-13, AD-17).

Importé seulement par import paresseux depuis `cli`. Le réseau entraîné est gelé au format de
AD-3 (`frozen/`) avec `run.json`, puis `evaluate` écrit `eval.json` : aucun évaluateur parallèle.
F est C avec les entrées préparées de la tâche (`prepared_encoder_id`). `retrain` réentraîne
l'architecture gelée d'une séance depuis des poids aléatoires (C « même réseau »).
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from nn_weight_writing import network
from nn_weight_writing.baselines import torch_layers
from nn_weight_writing.baselines.common import freeze_run, run_id
from nn_weight_writing.config import CONFIG_DIR
from nn_weight_writing.evaluation.labels import read_labels
from nn_weight_writing.evaluation.score import check_alignment, run_task
from nn_weight_writing.evaluation.verify import FROZEN_DIR, evaluate, verify_frozen
from nn_weight_writing.network.io import sha256_file
from nn_weight_writing.tasks.io import read_examples
from nn_weight_writing.tasks.legal import TASKS as LEGAL_TASKS
from nn_weight_writing.tasks.legal.task import LegalTask
from nn_weight_writing.tasks.toy import TASKS as TOY_TASKS
from nn_weight_writing.tasks.toy import ToyTask

TRAIN_PATH = CONFIG_DIR / "train.toml"
BASELINE = "C"
BASELINE_PREPARED = "F"  # C avec entrées préparées (CAP-7)
HELDOUT_DIR = "heldout"  # AD-12 : jamais lu pour entraîner (protocole-ecriture.md)

AnyTask = ToyTask | LegalTask


@dataclass(frozen=True)
class TrainConfig:
    hidden: tuple[int, ...]
    learning_rate: float
    epochs: int
    batch_size: int
    n_values: tuple[int, ...]
    seeds: tuple[int, ...]


def get_task(name: str) -> AnyTask:
    """Tâche jouet ou juridique (`legal_s`, `legal_s_reserved`) qui porte ses encodeurs."""
    if name in TOY_TASKS:
        return TOY_TASKS[name]
    if name in LEGAL_TASKS:
        return LEGAL_TASKS[name]
    raise KeyError(f"tâche inconnue : {name!r} (connues : {sorted([*TOY_TASKS, *LEGAL_TASKS])})")


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
        epochs=int(spec.get("epochs", defaults["epochs"])),
        batch_size=int(defaults["batch_size"]),
        n_values=tuple(spec.get("n_values", defaults["n_values"])),
        seeds=tuple(defaults["seeds"]),
    )


def _prepared(task: AnyTask) -> tuple[int, str]:
    if not hasattr(task, "encode_prepared"):
        raise ValueError(f"{task.name} : pas d'entrées préparées (témoin F)")
    return task.n_prepared_inputs, task.prepared_encoder_id


def _encode_for(task: AnyTask, encoder_id: str) -> Callable[[object], np.ndarray]:
    """Fonction d'encodage de la tâche qui porte cet identifiant d'encodeur."""
    if encoder_id == task.encoder_id:
        return task.encode
    if getattr(task, "prepared_encoder_id", None) == encoder_id:
        return task.encode_prepared
    raise ValueError(f"{task.name} : encodeur {encoder_id!r} inconnu")


def reference_manifest(task: AnyTask, config: TrainConfig, *, prepared: bool = False) -> dict:
    """Couches cachées `relu`, sortie `identity` : une unité par classe.

    `prepared` : entrées du témoin F, mêmes couches cachées que C.
    """
    n_inputs, encoder = _prepared(task) if prepared else (task.n_inputs, task.encoder_id)
    sizes = [n_inputs, *config.hidden, len(task.classes)]
    layers = [
        {
            "type": "dense",
            "in": sizes[i],
            "out": sizes[i + 1],
            "activation": "relu" if i < len(sizes) - 2 else "identity",
        }
        for i in range(len(sizes) - 1)
    ]
    return {"encoder": encoder, "layers": layers}


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


def _fit_and_freeze(
    task_name: str,
    manifest: dict,
    data_dir: Path,
    *,
    n: int,
    seed: int,
    run_dir: Path,
    baseline: str,
    config: TrainConfig,
    extra: dict | None = None,
) -> Path:
    task = get_task(task_name)
    data_dir = Path(data_dir)
    if HELDOUT_DIR in data_dir.resolve().parts:
        raise ValueError(f"jeu réservé refusé pour l'entraînement : {data_dir}")
    examples = read_examples(data_dir / "examples.jsonl")
    labels = read_labels(data_dir / "labels.jsonl")
    check_alignment(examples, labels)
    if not 1 <= n <= len(examples):
        raise ValueError(f"n={n} hors de 1..{len(examples)} (taille du jeu {data_dir})")
    encode = _encode_for(task, manifest["encoder"])
    chosen = examples[:n]
    inputs = np.stack([encode(e.raw) for e in chosen])
    index = {cid: i for i, cid in enumerate(task.class_ids)}
    targets = np.array([index[labels[e.id].label] for e in chosen], dtype=np.int64)
    weights = train_network(manifest, inputs, targets, config, seed)
    dataset = {
        "path": "/".join(data_dir.resolve().parts[-3:]),
        "files": {
            name: sha256_file(data_dir / name) for name in ("examples.jsonl", "labels.jsonl")
        },
        **(extra or {}),
    }
    freeze_run(
        run_dir,
        manifest,
        weights,
        baseline=baseline,
        n=n,
        seed=seed,
        dataset=dataset,
        task=task_name,
    )
    evaluate(run_dir)
    return run_dir


def train(
    task_name: str,
    data_dir: Path,
    *,
    n: int,
    seed: int,
    runs_root: Path,
    lot: str,
    config_path: Path | None = None,
    prepared: bool = False,
) -> Path:
    """Entraîne sur les `n` premiers exemples étiquetés de `data_dir`, gèle et évalue.

    `prepared` : témoin F (entrées préparées), sinon témoin C.
    """
    task = get_task(task_name)
    config = load_train_config(task_name, config_path)
    baseline = BASELINE_PREPARED if prepared else BASELINE
    manifest = reference_manifest(task, config, prepared=prepared)
    run_dir = Path(runs_root) / lot / "train" / run_id(task_name, baseline, n, seed)
    return _fit_and_freeze(
        task_name,
        manifest,
        data_dir,
        n=n,
        seed=seed,
        run_dir=run_dir,
        baseline=baseline,
        config=config,
    )


def retrain(
    session_dir: Path,
    data_dir: Path,
    *,
    n: int,
    seed: int,
    runs_root: Path,
    lot: str,
    config_path: Path | None = None,
) -> Path:
    """C « même réseau » : réentraîne l'architecture gelée d'une séance, poids aléatoires.

    Les empreintes de la séance sont vérifiées d'abord ; seul le manifeste est gardé, jamais ses
    poids. Dossier : `<runs_root>/<lot>/train/<séance>-retrain-n{N}-s{seed}`.
    """
    session_dir = Path(session_dir)
    _, _, tree, _ = verify_frozen(session_dir)
    task_name = run_task(session_dir)
    if not task_name:
        raise ValueError(f"{session_dir} : tâche de la séance introuvable")
    manifest, _ = network.load(session_dir / FROZEN_DIR)
    config = load_train_config(task_name, config_path)
    run_dir = Path(runs_root) / lot / "train" / f"{session_dir.name}-retrain-n{n}-s{seed}"
    extra = {"retrained_from": {"session": session_dir.name, "tree_sha256": tree}}
    return _fit_and_freeze(
        task_name,
        manifest,
        data_dir,
        n=n,
        seed=seed,
        run_dir=run_dir,
        baseline=BASELINE,
        config=config,
        extra=extra,
    )
