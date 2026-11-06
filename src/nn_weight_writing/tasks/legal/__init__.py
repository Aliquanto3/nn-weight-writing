"""Tâches de référence de décision de justice : S (15 types) et S-réservé (10 connus)."""

from nn_weight_writing.tasks.legal.task import TASK_S, TASK_S_RESERVED, LegalTask

TASKS: dict[str, LegalTask] = {t.name: t for t in (TASK_S, TASK_S_RESERVED)}

__all__ = ["TASKS", "TASK_S", "TASK_S_RESERVED", "LegalTask"]
