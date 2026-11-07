"""Mesures d'un dossier gelé sur un jeu réservé (story 1-14) : natives ou croisées.

Ordre tenu partout : `verify_frozen` (empreintes du gel), puis contrôle de la tâche et de
l'encodeur, puis empreintes du jeu réservé contre son `dataset.json`, et seulement ensuite
lecture des exemples et des étiquettes. B passe par `sandbox.run` profil B avec les seules
chaînes brutes, comme en séance ; des règles en échec donnent `error`, jamais une exactitude.
Les groupes « tenus à l'écart » viennent du `dataset.json` du jeu évalué (`baselines/curve.py`
n'est pas importable ici : PyTorch, AD-13).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

import numpy as np

from nn_weight_writing import network, sandbox
from nn_weight_writing.evaluation.ablation import ablate
from nn_weight_writing.evaluation.labels import Label, read_labels
from nn_weight_writing.evaluation.schema import FROZEN_DIR, JOURNAL_FILE
from nn_weight_writing.evaluation.score import check_alignment, run_task
from nn_weight_writing.evaluation.verify import EvalRefusalCode, EvaluationRefused, verify_frozen
from nn_weight_writing.journal.reader import find_last
from nn_weight_writing.network import io as netio
from nn_weight_writing.tasks.io import Example, read_examples
from nn_weight_writing.tasks.registry import TASKS, TaskSpec, validate_name

EXAMPLES_FILE = "examples.jsonl"
LABELS_FILE = "labels.jsonl"
DATASET_FILE = "dataset.json"
RULES_FILE = "rules.py"


class RulesFailed(RuntimeError):
    """Règles B refusées ou en échec dans le bac à sable."""


def _refuse(code: EvalRefusalCode, detail: str) -> EvaluationRefused:
    return EvaluationRefused(code, detail)


def resolve_heldout(heldout_root: Path, task: str, dataset: str | None) -> Path:
    """`heldout/<tâche>/<jeu>/` ; sans `dataset`, le seul sous-dossier de la tâche."""
    validate_name("tâche", task)
    base = Path(heldout_root) / task
    if not base.is_dir():
        raise _refuse(EvalRefusalCode.NO_HELDOUT, f"aucun jeu réservé pour {task}")
    if dataset is not None:
        validate_name("jeu", dataset)
        path = base / dataset
        if not path.is_dir():
            raise _refuse(EvalRefusalCode.NO_HELDOUT, f"jeu réservé absent : {task}/{dataset}")
        return path
    subdirs = sorted(p.name for p in base.iterdir() if p.is_dir())
    if not subdirs:
        raise _refuse(EvalRefusalCode.NO_HELDOUT, f"aucun jeu réservé pour {task}")
    if len(subdirs) > 1:
        raise _refuse(EvalRefusalCode.AMBIGUOUS_DATASET, f"{task} : {subdirs}, --dataset requis")
    return base / subdirs[0]


def dataset_identity(heldout_dir: Path) -> dict:
    """Empreintes du jeu réservé, vérifiées contre `dataset.json`, et types tenus à l'écart."""
    heldout_dir = Path(heldout_dir)
    paths = {name: heldout_dir / name for name in (EXAMPLES_FILE, LABELS_FILE, DATASET_FILE)}
    absent = sorted(name for name, path in paths.items() if not path.is_file())
    if absent:
        raise _refuse(EvalRefusalCode.NO_HELDOUT, f"{heldout_dir.name} : absents {absent}")
    data = json.loads(paths[DATASET_FILE].read_text("utf-8"))
    expected = data.get("files") if isinstance(data, dict) else None
    if not isinstance(expected, dict):
        raise _refuse(EvalRefusalCode.HELDOUT_FINGERPRINT, "dataset.json sans empreintes (files)")
    actual = {name: netio.sha256_file(paths[name]) for name in (EXAMPLES_FILE, LABELS_FILE)}
    for name, digest in actual.items():
        if expected.get(name) != digest:
            raise _refuse(EvalRefusalCode.HELDOUT_FINGERPRINT, f"{name} ≠ dataset.json")
    composition = data.get("composition") if isinstance(data.get("composition"), dict) else {}
    held = composition.get("held_out_types", data.get("held_out_types", [])) or []
    return {
        "examples_sha256": actual[EXAMPLES_FILE],
        "labels_sha256": actual[LABELS_FILE],
        "held_out_types": sorted(str(t) for t in held),
        "task": composition.get("task", data.get("task")),
    }


def encoder_for(spec: TaskSpec, encoder_id: str) -> Callable[[object], np.ndarray]:
    """Fonction d'encodage de la tâche qui porte cet encodeur (natif, préparé ou ancien)."""
    codec = spec.codec
    if encoder_id == codec.encoder_id:
        return codec.encode
    if getattr(codec, "prepared_encoder_id", None) == encoder_id:
        return codec.encode_prepared
    legacy = getattr(codec, "legacy_encoders", {}) or {}
    if encoder_id in legacy:
        return legacy[encoder_id]
    raise _refuse(
        EvalRefusalCode.ENCODER_MISMATCH, f"encodeur {encoder_id!r} étranger à {spec.name}"
    )


def predict_b(run_dir: Path, examples: list[Example]) -> dict[str, object]:
    """Règles gelées exécutées par `sandbox.run` profil B, sur les seules chaînes brutes."""
    code = (Path(run_dir) / FROZEN_DIR / RULES_FILE).read_text(encoding="utf-8")
    result = sandbox.run(code, sandbox.Profile.B, {"examples": [e.raw for e in examples]})
    if not result.ok:
        raise RulesFailed(f"règles B en échec : {result.error} {result.violations or ''}".strip())
    if not isinstance(result.value, list) or len(result.value) != len(examples):
        raise RulesFailed("règles B : une sortie par exemple attendue")
    return {
        e.id: (item.get("label") if isinstance(item, dict) else None)
        for e, item in zip(examples, result.value, strict=True)
    }


def _count(predictions: Mapping[str, object], labels: Mapping[str, Label], key) -> dict:
    table: dict[str, dict[str, int]] = {}
    for lid, lab in labels.items():
        entry = table.setdefault(key(lab), {"correct": 0, "n": 0})
        entry["n"] += 1
        entry["correct"] += int(predictions.get(lid) == lab.label)
    return dict(sorted(table.items()))


def metrics_of(
    predictions: Mapping[str, object], labels: Mapping[str, Label], held_out_types: list[str]
) -> dict:
    """Exactitude, par étiquette, par type et hors distribution (types tenus à l'écart)."""
    by_type = _count(predictions, labels, lambda lab: lab.type_id)
    held = set(held_out_types)
    ood = None
    if held:
        ood = {"correct": 0, "n": 0}
        for type_id, entry in by_type.items():
            if type_id in held:
                ood["correct"] += entry["correct"]
                ood["n"] += entry["n"]
    return {
        "accuracy": {
            "correct": sum(e["correct"] for e in by_type.values()),
            "n": sum(e["n"] for e in by_type.values()),
        },
        "by_label": _count(predictions, labels, lambda lab: lab.label),
        "by_type": by_type,
        "held_out_types": sorted(held),
        "ood": ood,
        "ablation": None,
        "error": None,
    }


def _error_metrics(error: str, held_out_types: list[str]) -> dict:
    return {
        "accuracy": None,
        "by_label": {},
        "by_type": {},
        "held_out_types": sorted(held_out_types),
        "ood": None,
        "ablation": None,
        "error": error,
    }


def _measure(run_dir: Path, task: str, heldout_dir: Path, *, cross: bool) -> tuple[dict, dict]:
    run_dir = Path(run_dir)
    kind, _, _, _ = verify_frozen(run_dir)  # avant toute lecture du réservé
    written = run_task(run_dir)
    if written not in TASKS:
        raise _refuse(EvalRefusalCode.TASK_MISMATCH, f"tâche du réseau inconnue : {written!r}")
    if cross and task == written:
        raise _refuse(EvalRefusalCode.CROSS_SAME_TASK, f"{task} est la tâche du réseau")
    if not cross and task != written:
        raise _refuse(EvalRefusalCode.TASK_MISMATCH, f"réseau de {written}, jeu de {task}")
    if task not in TASKS:
        raise _refuse(EvalRefusalCode.TASK_MISMATCH, f"tâche inconnue : {task!r}")
    spec = TASKS[task]
    frozen = run_dir / FROZEN_DIR
    rules = (frozen / RULES_FILE).is_file()
    if not rules:
        manifest, weights = network.load(frozen)
        encode = encoder_for(spec, manifest["encoder"])
    identity = dataset_identity(heldout_dir)  # empreintes du réservé avant ses étiquettes
    if identity["task"] not in (None, task):
        raise _refuse(EvalRefusalCode.TASK_MISMATCH, f"dataset.json de {identity['task']}")
    target = {
        "task": task,
        "dataset": Path(heldout_dir).name,
        "examples_sha256": identity["examples_sha256"],
        "labels_sha256": identity["labels_sha256"],
        "written_task": written,
        "cross": cross,
    }
    held = identity["held_out_types"]
    examples = read_examples(Path(heldout_dir) / EXAMPLES_FILE)
    labels = read_labels(Path(heldout_dir) / LABELS_FILE)
    check_alignment(examples, labels)
    if rules:
        try:
            predictions = predict_b(run_dir, examples)
        except RulesFailed as exc:
            return target, _error_metrics(str(exc), held)
        return target, metrics_of(predictions, labels, held)
    try:
        inputs = np.stack([encode(e.raw) for e in examples])
        outputs = network.forward(manifest, weights, inputs)
        decoded = [spec.codec.decode(row) for row in outputs]
    except (ValueError, TypeError, FloatingPointError) as exc:
        return target, _error_metrics(f"réseau en échec : {exc}", held)
    predictions = {e.id: p for e, p in zip(examples, decoded, strict=True)}
    metrics = metrics_of(predictions, labels, held)
    if not cross and kind == "session":
        freeze = find_last(run_dir / JOURNAL_FILE, "freeze") or {}
        blocks = freeze.get("blocks") or []
        if blocks:
            pairs = [(labels[e.id].label, labels[e.id].type_id) for e in examples]
            metrics["ablation"] = ablate(
                manifest, weights, blocks, inputs, pairs, spec.codec.decode
            )
    return target, metrics


def measure(run_dir: Path, heldout_dir: Path) -> tuple[dict, dict]:
    """Mesures natives : `heldout_dir` = `heldout/<tâche du réseau>/<jeu>/`."""
    return _measure(run_dir, Path(heldout_dir).parent.name, heldout_dir, cross=False)


def measure_cross(run_dir: Path, task: str, heldout_dir: Path) -> tuple[dict, dict]:
    """Évaluation croisée sur le jeu réservé d'une autre tâche (B sur les chaînes brutes)."""
    return _measure(run_dir, task, heldout_dir, cross=True)
