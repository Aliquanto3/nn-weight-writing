"""Générateurs de jeux jouet : graine, séparation séance et réservé, fichiers (AD-12, AD-16)."""

from __future__ import annotations

import json
from collections import Counter

import pytest

from nn_weight_writing.cli import main
from nn_weight_writing.datasets.toy import LABELERS, generate, generate_rows
from nn_weight_writing.evaluation.labels import LabelsError, read_labels
from nn_weight_writing.network.io import sha256_file
from nn_weight_writing.tasks.io import BundleError, read_examples
from nn_weight_writing.tasks.toy import TASKS, get_task

NAMES = sorted(TASKS)


@pytest.mark.parametrize("task", NAMES)
def test_same_seed_same_rows_other_seed_other_rows(task):
    first = generate_rows(task, 7, 40, 60)
    assert generate_rows(task, 7, 40, 60) == first
    assert generate_rows(task, 8, 40, 60) != first


@pytest.mark.parametrize("task", NAMES)
def test_session_and_heldout_share_no_id_and_no_raw(task):
    data, held = generate_rows(task, 3, 80, 120)
    assert (len(data), len(held)) == (80, 120)
    assert not {r.id for r in data} & {r.id for r in held}
    assert not {r.raw for r in data} & {r.raw for r in held}
    assert len({r.raw for r in data + held}) == 200
    assert data[0].id == f"{task}-d00001" and held[0].id == f"{task}-h00001"


@pytest.mark.parametrize("task", NAMES)
def test_labels_match_the_labeler_and_classes_are_balanced(task):
    data, held = generate_rows(task, 5, 100, 100)
    for row in data + held:
        assert row.label == LABELERS[task](row.raw) == row.type_id
        assert row.label in get_task(task).class_ids
    counts = Counter(r.label for r in data)
    if task == "compare":
        assert sorted(counts.values()) == [33, 33, 34]
    else:
        assert set(counts.values()) == {50}


def test_labelers_on_known_values():
    assert LABELERS["parity"]("0000000000") == "even"
    assert LABELERS["parity"]("1110000000") == "odd"
    assert LABELERS["compare"]("3 3") == "equal"
    assert LABELERS["compare"]("2 3") == "less"
    assert LABELERS["compare"]("4 3") == "greater"
    assert LABELERS["automaton"]("0001010000") == "accept"
    assert LABELERS["automaton"]("1100110011") == "reject"


def _spread(rows):
    counts = Counter(r.label for r in rows)
    return max(counts.values()) - min(counts.values()), len(counts)


@pytest.mark.parametrize(
    ("task", "n", "h"),
    [("parity", 512, 512), ("automaton", 352, 350), ("compare", 1500, 1501), ("compare", 1, 7)],
)
def test_both_sets_are_balanced_up_to_the_domain_limit(task, n, h):
    data, held = generate_rows(task, 4, n, h)
    k = len(get_task(task).class_ids)
    for rows, size in ((data, n), (held, h)):
        assert len(rows) == size
        spread, present = _spread(rows)
        assert spread <= 1 and present == min(k, size)
    assert len({r.raw for r in data + held}) == n + h


@pytest.mark.parametrize(
    ("task", "n", "h"),
    [("parity", 513, 512), ("automaton", 352, 352), ("compare", 1500, 1502), ("compare", 2000, 2000)],
)
def test_size_that_cannot_be_balanced_is_refused(task, n, h):
    with pytest.raises(ValueError, match="domaine trop petit"):
        generate_rows(task, 4, n, h)


def test_domain_too_small_is_refused():
    with pytest.raises(ValueError, match="domaine trop petit"):
        generate_rows("parity", 1, 1000, 100)


@pytest.mark.parametrize(("n", "h"), [(0, 5), (5, 0)])
def test_sizes_must_be_positive(n, h):
    with pytest.raises(ValueError, match="au moins 1"):
        generate_rows("parity", 1, n, h)


def test_generate_writes_layout_and_fingerprints(tmp_path):
    data_dir, held_dir = generate("parity", seed=2, n=30, n_heldout=50, root=tmp_path)
    assert data_dir == tmp_path / "data" / "parity" / "toy"
    assert held_dir == tmp_path / "heldout" / "parity" / "toy"
    for directory, count in ((data_dir, 30), (held_dir, 50)):
        assert sorted(p.name for p in directory.iterdir()) == [
            "dataset.json",
            "examples.jsonl",
            "labels.jsonl",
        ]
        meta = json.loads((directory / "dataset.json").read_text("utf-8"))
        assert meta == {
            "generator": "toy.parity",
            "version": 2,
            "seed": 2,
            "n": count,
            "files": {
                "examples.jsonl": sha256_file(directory / "examples.jsonl"),
                "labels.jsonl": sha256_file(directory / "labels.jsonl"),
            },
        }


def test_examples_file_carries_no_label_and_is_a_valid_bundle_source(tmp_path):
    data_dir, held_dir = generate("compare", seed=2, n=12, n_heldout=12, root=tmp_path)
    for line in (data_dir / "examples.jsonl").read_text("utf-8").splitlines():
        assert set(json.loads(line)) == {"id", "raw"}
    examples = read_examples(data_dir / "examples.jsonl")
    assert len(examples) == 12
    labels = read_labels(data_dir / "labels.jsonl")
    assert set(labels) == {e.id for e in examples}
    assert not set(labels) & set(read_labels(held_dir / "labels.jsonl"))


def test_session_reader_refuses_the_labelled_file(tmp_path):
    data_dir, _ = generate("parity", seed=2, n=5, n_heldout=5, root=tmp_path)
    with pytest.raises(BundleError, match="attendu exactement id et raw"):
        read_examples(data_dir / "labels.jsonl")


def test_generate_is_byte_reproducible_across_roots(tmp_path):
    a = generate("automaton", seed=4, n=20, n_heldout=20, root=tmp_path / "a")
    b = generate("automaton", seed=4, n=20, n_heldout=20, root=tmp_path / "b")
    for left, right in zip(a, b, strict=True):
        for name in ("examples.jsonl", "labels.jsonl", "dataset.json"):
            assert (left / name).read_bytes() == (right / name).read_bytes()


def test_generate_refuses_an_existing_dataset(tmp_path):
    generate("parity", seed=1, n=5, n_heldout=5, root=tmp_path)
    with pytest.raises(FileExistsError, match="jeu déjà présent"):
        generate("parity", seed=1, n=5, n_heldout=5, root=tmp_path)


def test_read_labels_rejects_extra_key_and_duplicate(tmp_path):
    path = tmp_path / "labels.jsonl"
    path.write_text('{"id": "a", "label": "x", "type_id": "x", "raw": "1"}\n', "utf-8")
    with pytest.raises(LabelsError, match="clés attendues"):
        read_labels(path)
    row = '{"id": "a", "label": "x", "type_id": "x"}\n'
    path.write_text(row + row, "utf-8")
    with pytest.raises(LabelsError, match="id en double"):
        read_labels(path)


def test_cli_datagen_all_and_refusal(tmp_path, capsys):
    root = str(tmp_path)
    argv = ["datagen", "all", "--seed", "1", "--n", "6", "--n-heldout", "6", "--root", root]
    assert main(argv) == 0
    for name in NAMES:
        assert (tmp_path / "data" / name / "toy" / "examples.jsonl").is_file()
        assert (tmp_path / "heldout" / name / "toy" / "labels.jsonl").is_file()
    assert main(argv) == 1
    assert "datagen refusé : jeu déjà présent" in capsys.readouterr().err


def test_cli_datagen_requires_explicit_seed(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main(["datagen", "parity", "--root", str(tmp_path)])
    assert exc.value.code == 2
