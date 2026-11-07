"""Tâches de référence de décision de justice : S (15 types), S-réservé (10 connus) et R."""

from nn_weight_writing.tasks.legal.task import TASK_R, TASK_S, TASK_S_RESERVED, LegalTask

TASKS: dict[str, LegalTask] = {t.name: t for t in (TASK_S, TASK_S_RESERVED, TASK_R)}

__all__ = ["TASKS", "TASK_R", "TASK_S", "TASK_S_RESERVED", "LegalTask"]
