"""Frontière de confiance par l'AST (AD-1)."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).parents[1] / "src" / "nn_weight_writing"
SESSION_SIDE = ("session", "providers", "sandbox", "network", "journal", "tasks", "budget")
FORBIDDEN_ROOTS = {"torch", "jax"}
FORBIDDEN_PACKAGES = {"evaluation", "baselines", "report", "datasets", "publish"}


def _resolve(module: str | None, level: int, rel: Path) -> str:
    """Nom absolu d'un import, relatif compris (`rel` : chemin dans le paquet)."""
    if not level:
        return module or ""
    parts = ["nn_weight_writing", *rel.parent.parts]
    base = parts[: len(parts) - (level - 1)]
    return ".".join([*base, module] if module else base)


def forbidden_imports(source: str, rel: Path) -> list[str]:
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = _resolve(node.module, node.level, rel)
            names = [base] + [f"{base}.{alias.name}" for alias in node.names]
        else:
            continue
        for name in names:
            parts = name.split(".")
            if parts[0] in FORBIDDEN_ROOTS:
                found.append(name)
            elif parts[0] == "nn_weight_writing" and len(parts) > 1:
                if parts[1] in FORBIDDEN_PACKAGES:
                    found.append(name)
    return found


def session_files() -> list[Path]:
    return [p for d in SESSION_SIDE if (PACKAGE / d).is_dir() for p in (PACKAGE / d).rglob("*.py")]


def test_session_side_exists():
    names = {p.relative_to(PACKAGE).as_posix() for p in session_files()}
    assert {"session/service.py", "sandbox/runner.py", "tasks/io.py"} <= names


@pytest.mark.parametrize("path", session_files(), ids=lambda p: p.relative_to(PACKAGE).as_posix())
def test_no_forbidden_import_on_session_side(path):
    assert forbidden_imports(path.read_text("utf-8"), path.relative_to(PACKAGE)) == []


@pytest.mark.parametrize("path", session_files(), ids=lambda p: p.relative_to(PACKAGE).as_posix())
def test_session_side_does_not_know_labels_or_heldout(path):
    text = path.read_text("utf-8")
    assert "labels.jsonl" not in text
    assert "heldout" not in text


def test_detector_catches_forbidden_imports():
    source = (
        "import torch.nn\nimport jax\nfrom ..evaluation import verify\n"
        "from nn_weight_writing.report import x\nfrom .. import baselines\nimport numpy\n"
    )
    found = forbidden_imports(source, Path("session/fake.py"))
    assert found == [
        "torch.nn",
        "jax",
        "nn_weight_writing.evaluation",
        "nn_weight_writing.evaluation.verify",
        "nn_weight_writing.report",
        "nn_weight_writing.report.x",
        "nn_weight_writing.baselines",
    ]


# AD-13 : PyTorch confiné aux témoins, importé par `baselines/` seul, jamais par `cli` en tête.
TORCH_MODULES = {"baselines/train.py", "baselines/torch_layers.py"}


def _imports_torch(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "torch" for a in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "torch":
            return True
    return False


def test_torch_is_imported_only_by_the_two_training_modules():
    importers = {
        p.relative_to(PACKAGE).as_posix()
        for p in PACKAGE.rglob("*.py")
        if _imports_torch(p.read_text("utf-8"))
    }
    assert importers == TORCH_MODULES


def test_torch_detector_catches_all_import_forms():
    assert _imports_torch("import torch")
    assert _imports_torch("import torch.nn as nn")
    assert _imports_torch("from torch import nn")
    assert _imports_torch("from torch.nn import Linear")
    assert not _imports_torch("import numpy\nfrom nn_weight_writing import network")


def test_cli_imports_baselines_train_only_inside_a_function():
    tree = ast.parse((PACKAGE / "cli.py").read_text("utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import | ast.ImportFrom):
            names = [a.name for a in node.names] + [getattr(node, "module", None) or ""]
            assert not any("baselines" in n or "torch" in n for n in names)


def test_importing_cli_and_the_session_side_does_not_load_torch():
    code = (
        "import sys\n"
        "import nn_weight_writing.cli\n"
        "import nn_weight_writing.session.service, nn_weight_writing.sandbox.runner\n"
        "import nn_weight_writing.network, nn_weight_writing.tasks.toy\n"
        "sys.exit(1 if 'torch' in sys.modules else 0)\n"
    )
    result = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_session_side_never_imports_legal_r():
    """Story 1-12 : `datasets.legal_r` (pré-étude R) reste côté évaluateur."""
    source = (
        "from nn_weight_writing.datasets.legal_r import grid\n"
        "import nn_weight_writing.datasets.legal_r.judilibre\n"
    )
    found = forbidden_imports(source, Path("session/fake.py"))
    assert found == [
        "nn_weight_writing.datasets.legal_r",
        "nn_weight_writing.datasets.legal_r.grid",
        "nn_weight_writing.datasets.legal_r.judilibre",
    ]
    for path in session_files():
        assert "legal_r" not in path.read_text("utf-8"), path
