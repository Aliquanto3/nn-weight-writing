"""Tâches jouet : encodeurs, décodeurs, vocabulaire (AD-4)."""

from __future__ import annotations

import numpy as np
import pytest

from nn_weight_writing.tasks.toy import TASKS, get_task


def test_three_tasks_with_expected_encoder_ids():
    assert sorted(TASKS) == ["automaton", "compare", "parity"]
    assert get_task("parity").encoder_id == "parity.bits@1"
    assert get_task("compare").encoder_id == "compare.pair@1"
    assert get_task("automaton").encoder_id == "automaton.bits@1"


def test_unknown_task_message():
    with pytest.raises(KeyError, match="tâche jouet inconnue"):
        get_task("nope")


def test_vocabulary_is_the_closed_class_list():
    assert [v["id"] for v in get_task("compare").vocabulary] == ["less", "equal", "greater"]
    assert get_task("parity").class_ids == ("even", "odd")
    assert get_task("automaton").class_ids == ("accept", "reject")
    for task in TASKS.values():
        assert all(v["description"] for v in task.vocabulary)
        assert task.description.strip()


def test_parity_encode_is_bit_vector():
    out = get_task("parity").encode("1010000001")
    assert out.dtype == np.float32
    assert out.tolist() == [1, 0, 1, 0, 0, 0, 0, 0, 0, 1]


def test_compare_encode_scales_by_1000():
    out = get_task("compare").encode("47 999")
    assert out.dtype == np.float32
    assert out.tolist() == [float(np.float32(0.047)), float(np.float32(0.999))]


@pytest.mark.parametrize(
    ("task", "raw"),
    [
        ("parity", "101"),
        ("parity", "10100000012"),
        ("automaton", "abcdefghij"),
        ("compare", "47"),
        ("compare", "47  63"),
        ("compare", "-1 4"),
        ("compare", "1000 4"),
        ("compare", "4 x"),
    ],
)
def test_encode_refuses_malformed_raw(task, raw):
    with pytest.raises(ValueError, match="attendu|reçu|entiers"):
        get_task(task).encode(raw)


def test_encode_refuses_non_string():
    with pytest.raises(TypeError, match="chaîne"):
        get_task("parity").encode(["1"])


def test_decode_takes_argmax_in_class_order():
    compare = get_task("compare")
    assert compare.decode(np.array([0.1, 0.2, 0.9], dtype=np.float32)) == "greater"
    assert compare.decode(np.array([[0.9, 0.2, 0.1]], dtype=np.float32)) == "less"
    assert get_task("parity").decode(np.array([0.5, 0.5], dtype=np.float32)) == "even"


def test_decode_refuses_wrong_output_size():
    with pytest.raises(ValueError, match="3 sorties, 2 attendues"):
        get_task("parity").decode(np.zeros(3, dtype=np.float32))
