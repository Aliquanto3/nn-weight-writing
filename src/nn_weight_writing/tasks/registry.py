"""Registre des tâches de séance : nom -> description, codec et vocabulaire fermé (AD-2, AD-4).

Les tâches jouet (1-7) y sont inscrites ; la tâche S s'y inscrira avec 1-9. `nnww session` lit
les exemples non annotés dans `data/<task>/<dataset>/examples.jsonl` (AD-12).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nn_weight_writing.tasks.base import Codec

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
EXAMPLES_NAME = "examples.jsonl"


@dataclass(frozen=True)
class TaskSpec:
    name: str
    description: str
    codec: Codec
    vocabulary: tuple[dict, ...]


TASKS: dict[str, TaskSpec] = {}


def register(spec: TaskSpec) -> TaskSpec:
    TASKS[spec.name] = spec
    return spec


def get_task(name: str) -> TaskSpec:
    if name not in TASKS:
        known = ", ".join(sorted(TASKS)) or "aucune (tâches inscrites à partir de 1-7)"
        raise KeyError(f"tâche inconnue : {name} ; connues : {known}")
    return TASKS[name]


def examples_path(task: str, dataset: str, data_dir: Path | None = None) -> Path:
    return Path(data_dir or DATA_DIR) / task / dataset / EXAMPLES_NAME


def _register_toy() -> None:
    """Tâches jouet de 1-7 : chacune est son propre codec (`encoder_id`, `encode`, `decode`)."""
    from nn_weight_writing.tasks.toy import TASKS as TOY

    for toy in TOY.values():
        register(TaskSpec(toy.name, toy.description, toy, tuple(toy.vocabulary)))


_register_toy()
