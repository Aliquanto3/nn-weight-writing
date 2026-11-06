"""Générateurs des jeux jouet (CAP-8, AD-16).

Un tirage unique par graine donne, par classe, des chaînes distinctes ; chaque classe fournit
d'abord sa part du jeu de séance, puis sa part du jeu réservé, entrelacées classe après classe.
Les deux jeux sont équilibrés séparément, et aucune chaîne ni aucun identifiant ne leur est commun.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from pathlib import Path

import numpy as np

from nn_weight_writing.datasets.io import Row, write_dataset
from nn_weight_writing.tasks.registry import validate_name
from nn_weight_writing.tasks.toy import TASKS, automaton, get_task, parity
from nn_weight_writing.tasks.toy import compare as compare_task

DATASET = "toy"
GENERATOR_VERSION = 2  # 2 : jeu réservé équilibré à part


def label_parity(raw: str) -> str:
    return "odd" if raw.count("1") % 2 else "even"


def label_compare(raw: str) -> str:
    a, b = compare_task.parse(raw)
    return "less" if a < b else "equal" if a == b else "greater"


def label_automaton(raw: str) -> str:
    return "accept" if "101" in raw else "reject"


LABELERS: dict[str, Callable[[str], str]] = {
    "parity": label_parity,
    "compare": label_compare,
    "automaton": label_automaton,
}


def _enumerated_pool(task_name: str, length: int, label: str, rng, count: int) -> list[str]:
    domain = ["".join(bits) for bits in itertools.product("01", repeat=length)]
    wanted = [raw for raw in domain if LABELERS[task_name](raw) == label]
    order = rng.permutation(len(wanted))[:count]
    return [wanted[int(i)] for i in order]


def _compare_pool(label: str, rng, count: int) -> list[str]:
    top = compare_task.MAX_VALUE + 1
    if label == "equal":
        count = min(count, top)  # une seule paire « a a » par valeur
    seen: dict[str, None] = {}
    while len(seen) < count:
        a, b = (int(v) for v in rng.integers(0, top, size=2))
        if label == "equal":
            b = a
        elif a == b:
            continue
        elif (label == "less") != (a < b):
            a, b = b, a
        seen[f"{a} {b}"] = None
    return list(seen)


def _pool(task_name: str, label: str, rng, count: int) -> list[str]:
    if task_name == "compare":
        return _compare_pool(label, rng, count)
    length = {"parity": parity.LENGTH, "automaton": automaton.LENGTH}[task_name]
    return _enumerated_pool(task_name, length, label, rng, count)


def _quotas(class_ids: tuple[str, ...], size: int) -> dict[str, int]:
    """Répartition équilibrée de `size` exemples : les premières classes reçoivent le reste."""
    base, extra = divmod(size, len(class_ids))
    return {cid: base + (i < extra) for i, cid in enumerate(class_ids)}


def _interleave(
    class_ids: tuple[str, ...], pools: dict[str, list[str]], start: dict[str, int], quotas: dict
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for rank in range(max(quotas.values())):
        for cid in class_ids:
            if rank < quotas[cid]:
                out.append((pools[cid][start[cid] + rank], cid))
    return out


def generate_rows(task_name: str, seed: int, n: int, n_heldout: int) -> tuple[list[Row], list[Row]]:
    """Jeu de séance (`n` lignes) et jeu réservé (`n_heldout`), déterministes pour `seed`.

    Chaque jeu est équilibré séparément (écart d'au plus un exemple entre classes) ; une taille
    que le domaine d'une classe ne permet pas d'équilibrer est refusée.
    """
    if n < 1 or n_heldout < 1:
        raise ValueError("n et n_heldout doivent être au moins 1")
    task = get_task(task_name)
    class_ids = tuple(task.class_ids)
    rng = np.random.default_rng(seed)
    q_data, q_held = _quotas(class_ids, n), _quotas(class_ids, n_heldout)
    pools = {cid: _pool(task_name, cid, rng, q_data[cid] + q_held[cid]) for cid in class_ids}
    for cid in class_ids:
        if len(pools[cid]) < q_data[cid] + q_held[cid]:
            raise ValueError(
                f"{task_name} : domaine trop petit pour {n} + {n_heldout} exemples distincts"
                f" équilibrés (classe {cid} : {len(pools[cid])} chaînes)"
            )
    data_items = _interleave(class_ids, pools, dict.fromkeys(class_ids, 0), q_data)
    held_items = _interleave(class_ids, pools, q_data, q_held)

    def rows(items: list[tuple[str, str]], prefix: str) -> list[Row]:
        return [
            Row(f"{task_name}-{prefix}{i:05d}", raw, label, label)
            for i, (raw, label) in enumerate(items, start=1)
        ]

    return rows(data_items, "d"), rows(held_items, "h")


def generate(
    task_name: str, *, seed: int, n: int, n_heldout: int, root: Path, dataset: str = DATASET
) -> tuple[Path, Path]:
    """Écrit `data/<task>/<dataset>/` et `heldout/<task>/<dataset>/` sous `root`."""
    if task_name not in TASKS:
        raise KeyError(f"tâche jouet inconnue : {task_name!r}")
    validate_name("jeu", dataset)
    data_rows, held_rows = generate_rows(task_name, seed, n, n_heldout)
    generator = f"toy.{task_name}"
    root = Path(root)
    data_dir = write_dataset(
        root / "data" / task_name / dataset,
        data_rows,
        generator=generator,
        version=GENERATOR_VERSION,
        seed=seed,
    )
    held_dir = write_dataset(
        root / "heldout" / task_name / dataset,
        held_rows,
        generator=generator,
        version=GENERATOR_VERSION,
        seed=seed,
    )
    return data_dir, held_dir
