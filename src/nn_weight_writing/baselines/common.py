"""Écriture d'un dossier de témoin au format commun (AD-12, AD-17)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from nn_weight_writing import network
from nn_weight_writing.evaluation.schema import RunRecord
from nn_weight_writing.network import io as netio


def run_id(task: str, baseline: str, n: int, seed: int) -> str:
    """`{task}-{baseline}-n{N}-s{seed}` (AD-12)."""
    return f"{task}-{baseline}-n{n}-s{seed}"


def freeze_run(
    run_dir: Path,
    manifest: dict,
    weights: dict[str, np.ndarray],
    *,
    baseline: str,
    n: int,
    seed: int,
) -> RunRecord:
    """Écrit `frozen/` (manifeste, poids) puis `run.json` ; refuse un dossier déjà gelé."""
    run_dir = Path(run_dir)
    if (run_dir / "run.json").exists():
        raise FileExistsError(f"témoin déjà gelé : {run_dir}")
    manifest = netio.validate_manifest(manifest)
    errors = netio.weights_errors(manifest, weights)
    if errors:
        raise netio.NetworkError("; ".join(errors))
    frozen = run_dir / "frozen"
    frozen.mkdir(parents=True, exist_ok=True)
    mbytes = netio.manifest_bytes(manifest)
    wbytes = netio.weights_bytes(manifest, weights)
    netio.atomic_write_bytes(frozen / netio.MANIFEST_NAME, mbytes)
    netio.atomic_write_bytes(frozen / netio.WEIGHTS_NAME, wbytes)
    files = {
        netio.MANIFEST_NAME: netio.sha256_bytes(mbytes),
        netio.WEIGHTS_NAME: netio.sha256_bytes(wbytes),
    }
    record = RunRecord(
        run_id=run_dir.name,
        baseline=baseline,
        n=n,
        seed=seed,
        files=files,
        tree_sha256=network.tree_sha256(files),
    )
    text = json.dumps(asdict(record), ensure_ascii=False, indent=2, sort_keys=True)
    netio.atomic_write_bytes(run_dir / "run.json", (text + "\n").encode("utf-8"))
    return record
