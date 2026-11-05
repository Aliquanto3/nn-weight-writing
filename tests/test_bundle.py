"""Paquet de séance (AD-2, AD-16) : exemples sans étiquette ni type, vocabulaire fermé seul."""

from __future__ import annotations

import json

import pytest
from conftest import ENCODER, EXAMPLES, VOCABULARY, write_examples

from nn_weight_writing.tasks.io import BundleError, materialize_bundle, read_bundle, read_examples


def make(tmp_path, records=EXAMPLES, vocabulary=VOCABULARY):
    source = write_examples(tmp_path / "examples.jsonl", records)
    return materialize_bundle(
        source,
        tmp_path / "bundle",
        task="toy",
        description="Dire si la référence est plausible.",
        encoder=ENCODER,
        vocabulary=vocabulary,
    )


def test_bundle_contains_only_ids_raws_and_visible_vocabulary(tmp_path):
    bundle = make(tmp_path)
    names = sorted(p.name for p in (tmp_path / "bundle").iterdir())
    assert names == ["examples.jsonl", "task.json"]
    lines = (tmp_path / "bundle" / "examples.jsonl").read_text("utf-8").splitlines()
    assert [json.loads(line) for line in lines] == EXAMPLES
    meta = json.loads((tmp_path / "bundle" / "task.json").read_text("utf-8"))
    assert set(meta) == {"task", "description", "encoder", "vocabulary"}
    assert meta["vocabulary"] == VOCABULARY
    assert bundle.vocabulary_ids == {"T1", "T2"}
    assert read_bundle(tmp_path / "bundle") == bundle


@pytest.mark.parametrize("extra", [{"label": "ok"}, {"type_id": "T1"}, {"label": None}])
def test_examples_with_label_or_type_refused(tmp_path, extra):
    records = [EXAMPLES[0], {**EXAMPLES[1], **extra}]
    with pytest.raises(BundleError, match="ligne 2"):
        make(tmp_path, records)
    assert not (tmp_path / "bundle").exists()


def test_reader_rejects_duplicates_and_empty(tmp_path):
    with pytest.raises(BundleError, match="double"):
        read_examples(write_examples(tmp_path / "d.jsonl", [EXAMPLES[0], EXAMPLES[0]]))
    with pytest.raises(BundleError, match="aucun"):
        read_examples(write_examples(tmp_path / "e.jsonl", []))


@pytest.mark.parametrize(
    "vocabulary",
    [
        [],
        [{"id": "T1", "description": "a"}, {"id": "T1", "description": "b"}],
        [{"id": "T1", "description": "a", "examples": ["x"]}],
        [{"id": "T1", "description": " "}],
    ],
    ids=["vide", "doublon", "cle-en-trop", "description-vide"],
)
def test_vocabulary_is_closed_and_validated(tmp_path, vocabulary):
    with pytest.raises(BundleError):
        make(tmp_path, vocabulary=vocabulary)


def test_bundle_is_written_once(tmp_path):
    make(tmp_path)
    with pytest.raises(BundleError, match="déjà"):
        make(tmp_path)
