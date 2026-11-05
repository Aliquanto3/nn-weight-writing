"""Audit a posteriori de l'interdit statistique (AD-19) : drapeaux journalisés, jamais de refus."""

from __future__ import annotations

import ast
from collections.abc import Sequence

FRAGMENT_LEN = 12
MAX_SAMPLES = 5


def _string_literals(tree: ast.AST) -> list[str]:
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _fragment_overlap(literals: list[str], examples: Sequence[tuple[str, str]]) -> dict | None:
    windows: dict[str, str] = {}
    for example_id, raw in examples:
        if not isinstance(raw, str):
            continue
        for i in range(len(raw) - FRAGMENT_LEN + 1):
            windows.setdefault(raw[i : i + FRAGMENT_LEN], example_id)
    if not windows:
        return None
    fragments: dict[str, str] = {}
    for literal in literals:
        for i in range(len(literal) - FRAGMENT_LEN + 1):
            fragment = literal[i : i + FRAGMENT_LEN]
            if fragment in windows:
                fragments.setdefault(fragment, windows[fragment])
    if not fragments:
        return None
    return {
        "kind": "fragment_overlap",
        "count": len(fragments),
        "example_ids": sorted(set(fragments.values()))[:MAX_SAMPLES],
        "samples": list(fragments)[:MAX_SAMPLES],
    }


def _iter_size(node: ast.expr) -> int | None:
    """Taille statique d'un itérable : `range(K)` ou littéral de liste, tuple ou ensemble."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and type(node.args[0].value) is int
    ):
        return node.args[0].value
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        return len(node.elts)
    return None


def _example_sized_loops(tree: ast.AST, n_examples: int) -> dict | None:
    lines = []
    for node in ast.walk(tree):
        iters = []
        if isinstance(node, ast.For | ast.AsyncFor):
            iters.append(node.iter)
        elif isinstance(node, ast.comprehension):
            iters.append(node.iter)
        for it in iters:
            if _iter_size(it) == n_examples:
                lines.append(getattr(it, "lineno", 0))
    if not lines:
        return None
    return {"kind": "example_sized_loop", "count": len(lines), "lines": sorted(lines)}


def audit(code: str, examples: Sequence[tuple[str, str]]) -> list[dict]:
    """Drapeaux d'audit du code soumis contre les exemples du paquet `(id, raw)`.

    Heuristiques statiques : recouvrement d'un fragment d'au moins 12 caractères entre un
    littéral de chaîne et un exemple ; boucle sur un itérable de taille égale au nombre
    d'exemples. Un code illisible ne porte aucun drapeau (le filtre le refuse).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError, ValueError:
        return []
    flags = []
    overlap = _fragment_overlap(_string_literals(tree), examples)
    if overlap:
        flags.append(overlap)
    if examples:
        loops = _example_sized_loops(tree, len(examples))
        if loops:
            flags.append(loops)
    return flags
