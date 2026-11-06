"""Solutions écrites à la main et témoin B sur le jouet : 100 % par le harnais (CAP-6, CAP-8)."""

from __future__ import annotations

import itertools
import json

import numpy as np
import pytest

from nn_weight_writing import network
from nn_weight_writing.baselines import handmade, rules
from nn_weight_writing.baselines.common import freeze_run, run_id
from nn_weight_writing.cli import main
from nn_weight_writing.datasets.toy import LABELERS, generate
from nn_weight_writing.evaluation.score import accuracy, score_frozen
from nn_weight_writing.evaluation.verify import EvalRefusalCode, EvaluationRefused, evaluate
from nn_weight_writing.tasks.toy import TASKS, get_task

NAMES = sorted(TASKS)


@pytest.fixture(scope="module")
def datasets(tmp_path_factory):
    root = tmp_path_factory.mktemp("jouet")
    return {name: generate(name, seed=11, n=64, n_heldout=300, root=root / name) for name in NAMES}


def frozen_handmade(tmp_path, task):
    manifest, weights = handmade.build(task)
    run_dir = tmp_path / "runs" / "toy" / "train" / run_id(task, "handmade", 0, 0)
    freeze_run(run_dir, manifest, weights, baseline="handmade", n=0, seed=0, task=task)
    return run_dir


def predict_all(task_name, raws):
    task = get_task(task_name)
    manifest, weights = handmade.build(task_name)
    outputs = network.forward(manifest, weights, np.stack([task.encode(r) for r in raws]))
    return [task.decode(row) for row in outputs]


@pytest.mark.parametrize("task", ["parity", "automaton"])
def test_handmade_is_exact_on_the_whole_bit_domain(task):
    raws = ["".join(bits) for bits in itertools.product("01", repeat=10)]
    assert predict_all(task, raws) == [LABELERS[task](r) for r in raws]


def test_handmade_compare_is_exact_on_edges_and_a_dense_grid():
    values = [0, 1, 2, 3, 499, 500, 501, 997, 998, 999]
    raws = [f"{a} {b}" for a in values for b in values]
    raws += [f"{a} {a + 1}" for a in range(999)] + [f"{a + 1} {a}" for a in range(999)]
    raws += [f"{a} {a}" for a in range(1000)]
    assert predict_all("compare", raws) == [LABELERS["compare"](r) for r in raws]


@pytest.mark.parametrize("task", NAMES)
def test_handmade_reaches_100_percent_on_heldout_through_the_evaluation_path(
    tmp_path, datasets, task
):
    _, held = datasets[task]
    run_dir = frozen_handmade(tmp_path, task)
    score = score_frozen(run_dir, get_task(task), held / "examples.jsonl", held / "labels.jsonl")
    assert (score.n, score.correct, score.accuracy) == (300, 300, 1.0)
    assert evaluate(run_dir) == run_dir / "eval.json"


def test_handmade_manifest_is_valid_and_uses_the_task_encoder():
    for task in NAMES:
        manifest, weights = handmade.build(task)
        network.validate_manifest(manifest)
        assert manifest["encoder"] == get_task(task).encoder_id
        assert all(w.dtype == np.float32 for w in weights.values())


def test_nnww_evaluate_accepts_the_frozen_handmade_run_and_records_fingerprints(tmp_path, capsys):
    run_dir = frozen_handmade(tmp_path, "parity")
    assert main(["evaluate", str(run_dir)]) == 0
    record = json.loads((run_dir / "eval.json").read_text("utf-8"))
    run = json.loads((run_dir / "run.json").read_text("utf-8"))
    assert record["kind"] == "baseline" and record["tree_sha256"] == run["tree_sha256"]
    assert run["baseline"] == "handmade" and run["run_id"] == "parity-handmade-n0-s0"
    assert sorted(run["files"]) == ["manifest.json", "weights.npz"]


def test_score_refuses_a_tampered_frozen_network(tmp_path, datasets):
    _, held = datasets["parity"]
    run_dir = frozen_handmade(tmp_path, "parity")
    manifest, weights = handmade.build("parity")
    weights["L1.b"] = weights["L1.b"] + np.float32(1.0)
    (run_dir / "frozen" / "weights.npz").write_bytes(network.io.weights_bytes(manifest, weights))
    with pytest.raises(EvaluationRefused) as exc:
        score_frozen(run_dir, get_task("parity"), held / "examples.jsonl", held / "labels.jsonl")
    assert exc.value.code == EvalRefusalCode.FINGERPRINT_MISMATCH


def test_score_refuses_a_foreign_encoder(tmp_path, datasets):
    _, held = datasets["parity"]
    run_dir = frozen_handmade(tmp_path, "parity")
    with pytest.raises(ValueError, match="encodeur 'parity.bits@1' différent de 'automaton"):
        score_frozen(run_dir, get_task("automaton"), held / "examples.jsonl", held / "labels.jsonl")


def test_freeze_run_refuses_to_overwrite(tmp_path):
    run_dir = frozen_handmade(tmp_path, "parity")
    manifest, weights = handmade.build("parity")
    with pytest.raises(FileExistsError, match="témoin déjà gelé"):
        freeze_run(run_dir, manifest, weights, baseline="handmade", n=0, seed=0)


def test_accuracy_counts_missing_prediction_as_wrong():
    from nn_weight_writing.evaluation.labels import Label

    labels = {"a": Label("a", "x", "x"), "b": Label("b", "y", "y")}
    score = accuracy({"a": "x"}, labels)
    assert (score.n, score.correct, score.accuracy) == (2, 1, 0.5)


@pytest.mark.parametrize("task", NAMES)
def test_witness_b_rules_run_in_the_profile_b_sandbox_at_100_percent(datasets, task):
    _, held = datasets[task]
    score = rules.score_rules(task, held / "examples.jsonl", held / "labels.jsonl")
    assert (score.n, score.correct) == (300, 300)


@pytest.mark.parametrize("task", NAMES)
def test_witness_b_rules_pass_the_profile_b_filter(task):
    from nn_weight_writing.sandbox.filter import check

    assert check(rules.RULES[task], "B") == []


def test_run_rules_returns_labels_in_order_and_refuses_unknown_task():
    assert rules.run_rules("parity", ["1000000000", "1100000000"]) == ["odd", "even"]
    with pytest.raises(KeyError, match="pas de règles B"):
        rules.run_rules("nope", ["x"])


def test_run_rules_reports_a_sandbox_failure(monkeypatch):
    monkeypatch.setitem(rules.RULES, "parity", "import os\n")
    with pytest.raises(rules.RulesError, match="parity : refused"):
        rules.run_rules("parity", ["1000000000"])


def test_score_refuses_a_network_written_for_another_task(tmp_path, datasets):  # O4
    _, held = datasets["parity"]
    manifest, weights = handmade.build("parity")
    for name, task in (("other", "legal_s"), ("legacy", "")):
        run_dir = tmp_path / "runs" / name
        freeze_run(run_dir, manifest, weights, baseline="handmade", n=0, seed=0, task=task)
        with pytest.raises(ValueError, match="évaluation croisée non prise en charge") as exc:
            score_frozen(
                run_dir, get_task("parity"), held / "examples.jsonl", held / "labels.jsonl"
            )
        assert f"tâche {task!r}" in str(exc.value) and "'parity'" in str(exc.value)
