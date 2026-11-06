"""Choix du nombre d'époques des témoins C et F sur une validation tirée du jeu d'entraînement.

Usage : uv run --group train python scripts/choix_epoques.py [--root .] [--n 8192] [--val 4096]
    [--seeds 0 1] [--epochs 25 50 100 200 400]

Revue de 1-11 (AD-12) : le choix ne lit jamais `heldout/`. Le réseau apprend sur les `n`
premiers exemples de `data/<tâche>/train/`, la validation est faite des `val` derniers, disjoints
(le jeu doit compter au moins n + val exemples). Une seule passe d'entraînement jusqu'au plus
grand nombre d'époques, exactitude de validation relevée à chaque palier (même suite de lots
qu'un run court).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from nn_weight_writing.baselines.train import (
    HELDOUT_DIR,
    _encode_for,
    get_task,
    load_train_config,
    reference_manifest,
    train_network,
)
from nn_weight_writing.evaluation.labels import read_labels
from nn_weight_writing.evaluation.score import check_alignment
from nn_weight_writing.tasks.io import read_examples


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tasks", nargs="+", default=["legal_s", "legal_s_reserved"])
    parser.add_argument("--n", type=int, default=8192)
    parser.add_argument("--val", type=int, default=4096)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--epochs", type=int, nargs="+", default=[25, 50, 100, 200, 400])
    args = parser.parse_args(argv)
    print("| Tâche | Méthode | Graine | " + " | ".join(f"{e} ép." for e in args.epochs) + " |")
    print("|---|---|---|" + "---|" * len(args.epochs))
    for task_name in args.tasks:
        data_dir = args.root / "data" / task_name / "train"
        if HELDOUT_DIR in data_dir.resolve().parts:
            raise ValueError(f"jeu réservé refusé : {data_dir}")
        examples = read_examples(data_dir / "examples.jsonl")
        labels = read_labels(data_dir / "labels.jsonl")
        check_alignment(examples, labels)
        if len(examples) < args.n + args.val:
            raise ValueError(f"{data_dir} : {len(examples)} exemples < n + val")
        task = get_task(task_name)
        config = replace(load_train_config(task_name), epochs=max(args.epochs))
        index = {cid: i for i, cid in enumerate(task.class_ids)}
        fit, val = examples[: args.n], examples[-args.val :]
        for method in ("C", "F"):
            manifest = reference_manifest(task, config, prepared=method == "F")
            encode = _encode_for(task, manifest["encoder"])
            x_fit = np.stack([encode(e.raw) for e in fit])
            y_fit = np.array([index[labels[e.id].label] for e in fit], dtype=np.int64)
            x_val = torch.from_numpy(np.stack([encode(e.raw) for e in val]))
            y_val = np.array([index[labels[e.id].label] for e in val], dtype=np.int64)
            for seed in args.seeds:
                scores: dict[int, float] = {}

                def check(epoch: int, module, scores=scores, x_val=x_val, y_val=y_val) -> None:
                    if epoch in args.epochs:
                        with torch.no_grad():
                            pred = module(x_val).argmax(dim=1).numpy()
                        scores[epoch] = float((pred == y_val).mean())

                train_network(manifest, x_fit, y_fit, config, seed, on_epoch=check)
                cells = " | ".join(f"{100 * scores[e]:.1f}" for e in args.epochs)
                print(f"| {task_name} | {method} ({manifest['encoder']}) | {seed} | {cells} |")
                sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
