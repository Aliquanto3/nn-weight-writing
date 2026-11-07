"""`scripts/rassembler_runs.py` (story 1-14) : copie des artefacts sans écrire dans les sources."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "rassembler_runs.py"
spec = importlib.util.spec_from_file_location("rassembler_runs", SCRIPT)
gather = importlib.util.module_from_spec(spec)
sys.modules["rassembler_runs"] = gather
spec.loader.exec_module(gather)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")
    return path


@pytest.fixture
def sources(tmp_path):
    """Deux worktrees : séances distinctes, même `heldout/`, eval et collecte brute à exclure."""
    a, b = tmp_path / "wt-a", tmp_path / "wt-b"
    write(a / "runs/1/s-a/journal.jsonl", "{}\n")
    write(a / "runs/1/s-a/eval.json", "{}")
    write(a / "runs/1/s-a/eval-cross-x-eval.json", "{}")
    write(a / "runs/1/s-a/bundle/task.json", "{}")
    write(a / "data/r/collecte/collecte.jsonl", "{}\n")
    write(a / "data/legal_s/session/examples.jsonl", "{}\n")
    write(b / "runs/1/train/c-n64-s0/run.json", "{}")
    for root in (a, b):
        write(root / "heldout/legal_s/eval/examples.jsonl", '{"id": "e1"}\n')
    write(a / "notes.md", "hors runs, heldout, data")
    return [a, b]


def snapshot(roots: list[Path]) -> dict[str, tuple[str, int]]:
    return {
        str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
        for root in roots
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def run(sources: list[Path], dest: Path, *extra: str) -> int:
    return gather.main(["--to", str(dest), "--from", *map(str, sources), *extra])


def files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def test_gather_copies_without_touching_sources(sources, tmp_path):
    before = snapshot(sources)
    dest = tmp_path / "dest"
    assert run(sources, dest) == 0
    assert snapshot(sources) == before
    assert files(dest) == [
        "data/legal_s/session/examples.jsonl",
        "heldout/legal_s/eval/examples.jsonl",
        "provenance.jsonl",
        "runs/1/s-a/bundle/task.json",
        "runs/1/s-a/journal.jsonl",
        "runs/1/train/c-n64-s0/run.json",
    ]
    lines = [json.loads(x) for x in (dest / "provenance.jsonl").read_text("utf-8").splitlines()]
    assert [x["path"] for x in lines] == [
        "runs/1/s-a/bundle/task.json",
        "runs/1/s-a/journal.jsonl",
        "heldout/legal_s/eval/examples.jsonl",
        "data/legal_s/session/examples.jsonl",
        "runs/1/train/c-n64-s0/run.json",
    ]
    assert lines[1]["src"] == str(sources[0])
    source = sources[0] / "runs/1/s-a/journal.jsonl"
    assert lines[1]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert set(lines[0]) == {"src", "path", "sha256", "ts"}


def test_gather_is_idempotent(sources, tmp_path, capsys):
    dest = tmp_path / "dest"
    assert run(sources, dest) == 0
    provenance = (dest / "provenance.jsonl").read_bytes()
    capsys.readouterr()
    assert run(sources, dest) == 0
    assert "à copier : 0 ; déjà présents : 6" in capsys.readouterr().out
    assert (dest / "provenance.jsonl").read_bytes() == provenance
    # Relance avec une nouvelle source (1-13) : seuls ses fichiers sont ajoutés.
    new = tmp_path / "wt-c"
    write(new / "runs/1/s-c/journal.jsonl", "{}\n")
    assert run([*sources, new], dest) == 0
    added = (
        (dest / "provenance.jsonl").read_text("utf-8").splitlines()[len(provenance.splitlines()) :]
    )
    assert [json.loads(x)["path"] for x in added] == ["runs/1/s-c/journal.jsonl"]


def test_gather_refuses_conflicting_file(sources, tmp_path, capsys):
    write(sources[1] / "heldout/legal_s/eval/examples.jsonl", '{"id": "autre"}\n')
    dest = tmp_path / "dest"
    assert run(sources, dest) == 1
    err = capsys.readouterr().err
    assert "conflit : heldout/legal_s/eval/examples.jsonl" in err and "rien n'est copié" in err
    assert not dest.exists()
    # Conflit avec la destination : rien de copié non plus.
    write(dest / "runs/1/s-a/journal.jsonl", "différent\n")
    assert run(sources[:1], dest) == 1
    assert files(dest) == ["runs/1/s-a/journal.jsonl"]


def test_gather_skips_eval_files_and_raw_collection(sources, tmp_path, capsys):
    dest = tmp_path / "dest"
    assert run(sources, dest, "--dry-run") == 0
    assert "à copier : 5 ; déjà présents : 1 ; exclus : 3 ; conflits : 0" in capsys.readouterr().out
    assert not dest.exists()
    assert run(sources, dest) == 0
    copied = files(dest)
    assert "runs/1/s-a/eval.json" not in copied
    assert "runs/1/s-a/eval-cross-x-eval.json" not in copied
    assert not any(p.startswith("data/r/") for p in copied)


def test_gather_only_option_skips_data(sources, tmp_path):
    dest = tmp_path / "dest"
    assert run(sources, dest, "--only", "runs", "heldout") == 0
    assert not (dest / "data").exists()
    assert (dest / "heldout/legal_s/eval/examples.jsonl").is_file()


def test_gather_missing_source_is_usage_error(tmp_path):
    assert run([tmp_path / "absent"], tmp_path / "dest") == 2
