"""Registre des tâches de séance : nom -> description, codec et vocabulaire fermé (AD-2, AD-4).

Les tâches jouet (1-7) et les tâches `legal_s` et `legal_s_reserved` (1-9) y sont inscrites.
`nnww session` lit les exemples non annotés dans `data/<task>/<dataset>/examples.jsonl` (AD-12) ;
les noms de tâche et de jeu qui composent un chemin sont validés (`validate_name`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from nn_weight_writing.tasks.base import Codec

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
EXAMPLES_NAME = "examples.jsonl"
NAME_PATTERN = re.compile(r"[a-z0-9_]+")


def validate_name(kind: str, value: str) -> str:
    """Refuse un nom de tâche ou de jeu qui ne tient pas dans `[a-z0-9_]+` (chemin, `..`)."""
    if not isinstance(value, str) or not NAME_PATTERN.fullmatch(value):
        raise ValueError(f"{kind} invalide : {value!r} (attendu : lettres minuscules, chiffres, _)")
    return value


@dataclass(frozen=True)
class TaskSpec:
    name: str
    description: str
    codec: Codec
    vocabulary: tuple[dict, ...]
    session_datasets: tuple[str, ...] = ("toy",)  # jeux autorisés pour `nnww session`


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
    validate_name("tâche", task)
    validate_name("jeu", dataset)
    return Path(data_dir or DATA_DIR) / task / dataset / EXAMPLES_NAME


def _register_toy() -> None:
    """Tâches jouet de 1-7 : chacune est son propre codec (`encoder_id`, `encode`, `decode`)."""
    from nn_weight_writing.tasks.toy import TASKS as TOY

    for toy in TOY.values():
        register(TaskSpec(toy.name, toy.description, toy, tuple(toy.vocabulary)))


_register_toy()


def _register_legal() -> None:
    """Tâches S et S-réservé de 1-9 : jeu de séance `session` seulement (`train` : témoins)."""
    from nn_weight_writing.tasks.legal import TASKS as LEGAL

    for task in LEGAL.values():
        register(
            TaskSpec(
                task.name,
                task.description,
                task,
                tuple(task.vocabulary),
                session_datasets=("session",),
            )
        )


_register_legal()
