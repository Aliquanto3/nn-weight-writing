"""Tâches jouet à solution exacte connue (CAP-8) : parité, comparaison, petit automate."""

from nn_weight_writing.tasks.toy.automaton import TASK as AUTOMATON
from nn_weight_writing.tasks.toy.base import ToyTask
from nn_weight_writing.tasks.toy.compare import TASK as COMPARE
from nn_weight_writing.tasks.toy.parity import TASK as PARITY

TASKS: dict[str, ToyTask] = {t.name: t for t in (PARITY, COMPARE, AUTOMATON)}


def get_task(name: str) -> ToyTask:
    try:
        return TASKS[name]
    except KeyError:
        raise KeyError(f"tâche jouet inconnue : {name!r} (connues : {sorted(TASKS)})") from None


__all__ = ["AUTOMATON", "COMPARE", "PARITY", "TASKS", "ToyTask", "get_task"]
