"""Mesures de `nnww evaluate` (1-14) : eval.json v2, B, hors distribution, lisibilité, croisée."""

from __future__ import annotations

import builtins
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from artefacts import TYPED_ROWS, typed_network, typed_spec, write_heldout, write_session

from nn_weight_writing import network
from nn_weight_writing.baselines.rules import RULES
from nn_weight_writing.cli import main
from nn_weight_writing.datasets.toy import generate
from nn_weight_writing.evaluation.ablation import ablate, forward_masked
from nn_weight_writing.evaluation.verify import (
    EvalRefusalCode,
    EvaluationRefused,
    evaluate,
    lot_dirs,
)
from nn_weight_writing.tasks.registry import TASKS

BLOCKS = [
    {"rule": "lettre A", "types": ["t01"], "units": [[0, 0]]},
    {"rule": "lettre B", "types": ["t02"], "units": [[0, 1]]},
]


@pytest.fixture
def typed(monkeypatch):
    """Tâche de test inscrite au registre réel le temps du test."""
    monkeypatch.setitem(TASKS, "typed", typed_spec())


@pytest.fixture
def heldout(tmp_path):
    root = tmp_path / "heldout"
    write_heldout(root, "typed", "eval", TYPED_ROWS)
    return root


def load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def test_evaluate_writes_metrics_v2(typed, heldout, tmp_path):
    run_dir = write_session(tmp_path / "runs" / "1", blocks=BLOCKS)
    record = load(evaluate(run_dir, heldout))
    assert record["schema_version"] == 2
    target = record["target"]
    assert target["task"] == "typed" and target["dataset"] == "eval"
    assert target["written_task"] == "typed" and target["cross"] is False
    meta = load(heldout / "typed" / "eval" / "dataset.json")["files"]
    assert target["examples_sha256"] == meta["examples.jsonl"]
    assert target["labels_sha256"] == meta["labels.jsonl"]
    metrics = record["metrics"]
    assert metrics["accuracy"] == {"correct": 6, "n": 6}
    assert metrics["by_label"] == {"fake": {"correct": 4, "n": 4}, "real": {"correct": 2, "n": 2}}
    assert metrics["by_type"] == {
        "real": {"correct": 2, "n": 2},
        "t01": {"correct": 2, "n": 2},
        "t02": {"correct": 2, "n": 2},
    }
    assert metrics["error"] is None and metrics["ood"] is None and metrics["held_out_types"] == []
    assert metrics["ablation"]["legibility"]["score"] == "2/2"


def test_evaluate_metrics_are_deterministic(typed, heldout, tmp_path):
    run_dir = write_session(tmp_path / "runs" / "1", blocks=BLOCKS)
    first = load(evaluate(run_dir, heldout))
    second = load(evaluate(run_dir, heldout))
    assert first.pop("ts") and second.pop("ts")
    assert first == second


def test_evaluate_without_heldout_root_is_verification_only(typed, tmp_path, monkeypatch):
    """Décision Q9 : aucune lecture implicite de heldout/ du répertoire courant."""
    write_heldout(tmp_path / "heldout", "typed", "eval", TYPED_ROWS)
    monkeypatch.chdir(tmp_path)
    run_dir = write_session(tmp_path / "runs" / "1", blocks=BLOCKS)
    record = load(evaluate(run_dir))
    assert record["metrics"] == {} and record["target"] == {}


def test_evaluate_verifies_freeze_before_heldout(typed, heldout, tmp_path, monkeypatch):
    run_dir = write_session(tmp_path / "runs" / "1")
    weights = run_dir / "frozen" / "weights.npz"
    data = bytearray(weights.read_bytes())
    data[-1] ^= 0xFF
    weights.write_bytes(bytes(data))
    opened: list[str] = []
    real_open = builtins.open

    def spy(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(run_dir, heldout)
    assert exc.value.code == EvalRefusalCode.FINGERPRINT_MISMATCH
    assert not any(name.endswith("labels.jsonl") for name in opened)
    assert not (run_dir / "eval.json").exists()


def test_evaluate_refuses_heldout_not_matching_dataset_json(typed, heldout, tmp_path):
    run_dir = write_session(tmp_path / "runs" / "1")
    labels = heldout / "typed" / "eval" / "labels.jsonl"
    labels.write_text(labels.read_text("utf-8").replace('"real"', '"fake"', 1), "utf-8")
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(run_dir, heldout)
    assert exc.value.code == EvalRefusalCode.HELDOUT_FINGERPRINT
    assert "labels.jsonl" in exc.value.detail


def test_evaluate_refuses_missing_or_ambiguous_heldout(typed, heldout, tmp_path):
    run_dir = write_session(tmp_path / "runs" / "1")
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(run_dir, tmp_path / "vide")
    assert exc.value.code == EvalRefusalCode.NO_HELDOUT
    write_heldout(heldout, "typed", "autre", TYPED_ROWS)
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(run_dir, heldout)
    assert exc.value.code == EvalRefusalCode.AMBIGUOUS_DATASET
    assert load(evaluate(run_dir, heldout, dataset="autre"))["target"]["dataset"] == "autre"


@pytest.fixture(scope="module")
def parity(tmp_path_factory):
    root = tmp_path_factory.mktemp("jouet")
    generate("parity", seed=3, n=16, n_heldout=40, root=root)
    return root / "heldout"


def test_evaluate_b_through_sandbox(parity, tmp_path):
    run_dir = write_session(
        tmp_path / "runs" / "1", task="parity", method="B", rules=RULES["parity"]
    )
    metrics = load(evaluate(run_dir, parity))["metrics"]
    assert metrics["accuracy"] == {"correct": 40, "n": 40}
    assert metrics["error"] is None and metrics["ablation"] is None
    assert sum(e["n"] for e in metrics["by_label"].values()) == 40


def test_evaluate_b_failure_is_error_not_score(parity, tmp_path):
    rules = "def predict(raw):\n    raise ValueError('règle cassée')\n"
    run_dir = write_session(tmp_path / "runs" / "1", task="parity", method="B", rules=rules)
    metrics = load(evaluate(run_dir, parity))["metrics"]
    assert metrics["accuracy"] is None and metrics["by_type"] == {}
    assert metrics["error"].startswith("règles B en échec")


def test_ood_group_follows_dataset_json(typed, tmp_path):
    root = tmp_path / "heldout"
    write_heldout(root, "typed", "eval", TYPED_ROWS, held_out_types=["t02"])
    manifest, weights = typed_network()
    weights["L0.W"][1, 1] = 0.0  # le réseau ne voit plus B : les t02 sont manqués
    run_dir = write_session(tmp_path / "runs" / "1", network=(manifest, weights))
    metrics = load(evaluate(run_dir, root))["metrics"]
    assert metrics["held_out_types"] == ["t02"]
    assert metrics["ood"] == {"correct": 0, "n": 2}
    assert metrics["accuracy"] == {"correct": 4, "n": 6}
    other = tmp_path / "s"
    write_heldout(other, "typed", "eval", TYPED_ROWS)
    assert load(evaluate(run_dir, other))["metrics"]["ood"] is None


# --- lisibilité -------------------------------------------------------------------------------


def test_forward_masked_without_mask_equals_forward():
    rng = np.random.default_rng(0)
    manifest = {
        "encoder": "x@1",
        "layers": [
            {"type": "dense", "in": 4, "out": 5, "activation": "tanh"},
            {"type": "dense", "in": 5, "out": 3, "activation": "sigmoid"},
            {"type": "dense", "in": 3, "out": 2, "activation": "identity"},
        ],
    }
    weights = {}
    for i, layer in enumerate(manifest["layers"]):
        weights[f"L{i}.W"] = rng.normal(size=(layer["in"], layer["out"])).astype(np.float32)
        weights[f"L{i}.b"] = rng.normal(size=layer["out"]).astype(np.float32)
    x = rng.normal(size=(7, 4)).astype(np.float32)
    assert np.array_equal(
        forward_masked(manifest, weights, x, set()), network.forward(manifest, weights, x)
    )
    masked = forward_masked(manifest, weights, x, {(0, 2)})
    assert not np.array_equal(masked, network.forward(manifest, weights, x))


def _typed_inputs(rows):
    codec = typed_spec().codec
    inputs = np.stack([codec.encode(raw) for raw, _, _ in rows])
    return inputs, [(lab, t) for _, lab, t in rows], codec.decode


def test_legibility_matches_declared_blocks(typed, heldout, tmp_path):
    run_dir = write_session(tmp_path / "runs" / "1", blocks=BLOCKS)
    ablation = load(evaluate(run_dir, heldout))["metrics"]["ablation"]
    assert ablation["legibility"] == {
        "units": 2,
        "legible": 2,
        "neutral": 0,
        "score": "2/2",
        "rate": 1.0,
    }
    unit0 = ablation["units"][0]
    assert unit0["unit"] == [0, 0] and unit0["block"] == 0
    assert unit0["max_drop"] == "1" and unit0["max_drop_types"] == ["t01"]
    assert ablation["blocks"][0]["accuracy"] == {"correct": 4, "n": 6}
    assert ablation["blocks"][0]["by_type"]["t01"] == {"correct": 0, "n": 2}


def test_legibility_swapped_blocks_scores_zero():
    manifest, weights = typed_network()
    inputs, labels, decode = _typed_inputs(TYPED_ROWS)
    swapped = [dict(BLOCKS[0], types=["t02"]), dict(BLOCKS[1], types=["t01"])]
    result = ablate(manifest, weights, swapped, inputs, labels, decode)
    assert result["legibility"]["legible"] == 0 and result["legibility"]["score"] == "0/2"


def test_neutral_unit_counts_in_denominator():
    manifest, weights = typed_network(neutral=True)
    inputs, labels, decode = _typed_inputs(TYPED_ROWS)
    blocks = [BLOCKS[0], {"rule": "B et rien", "types": ["t02"], "units": [[0, 1], [0, 2]]}]
    result = ablate(manifest, weights, blocks, inputs, labels, decode)
    assert result["legibility"] == {
        "units": 3,
        "legible": 2,
        "neutral": 1,
        "score": "2/3",
        "rate": round(2 / 3, 6),
    }
    assert result["units"][2]["max_drop"] == "0" and result["units"][2]["max_drop_types"] == []


def _rows(n_t01_a: int, n_t01: int, n_t02_a: int, n_t02: int):
    """t01 : `n_t01` exemples dont `n_t01_a` portent A ; t02 : idem, B pour les autres."""
    rows = [("A", "fake", "t01")] * n_t01_a + [("B", "fake", "t01")] * (n_t01 - n_t01_a)
    rows += [("A", "fake", "t02")] * n_t02_a + [("B", "fake", "t02")] * (n_t02 - n_t02_a)
    return rows + [("z", "real", "real")]


@pytest.mark.parametrize(
    ("rows", "legible", "declared", "other"),
    [
        (_rows(2, 2, 1, 4), True, "1", "1/4"),  # 100 points contre 25 : plus du double
        (_rows(2, 2, 2, 4), False, "1", "1/2"),  # exactement le double : non lisible
        (_rows(1, 20, 0, 4), True, "1/20", "0"),  # 5 points pile : lisible
        (_rows(1, 21, 0, 4), False, "1/21", "0"),  # moins de 5 points
    ],
)
def test_legibility_thresholds_are_exact(rows, legible, declared, other):
    manifest, weights = typed_network()
    inputs, labels, decode = _typed_inputs(rows)
    result = ablate(manifest, weights, [BLOCKS[0]], inputs, labels, decode)
    unit = result["units"][0]
    assert (unit["legible"], unit["declared_drop"], unit["other_drop"]) == (
        legible,
        declared,
        other,
    )
    assert Fraction(unit["declared_drop"]) >= 0


# --- évaluation croisée ----------------------------------------------------------------------


def test_cross_evaluation_writes_separate_file(typed, heldout, tmp_path, monkeypatch):
    monkeypatch.setitem(TASKS, "typed_reserved", typed_spec("typed_reserved"))
    write_heldout(heldout, "typed_reserved", "eval", TYPED_ROWS, held_out_types=["t01"])
    run_dir = write_session(tmp_path / "runs" / "1", blocks=BLOCKS)
    native = evaluate(run_dir, heldout)
    before = native.read_bytes()
    out = evaluate(run_dir, heldout, on=("typed_reserved", "eval"))
    assert out.name == "eval-cross-typed_reserved-eval.json"
    record = load(out)
    assert record["target"]["cross"] is True and record["target"]["written_task"] == "typed"
    assert record["metrics"]["ood"] == {"correct": 2, "n": 2}
    assert record["metrics"]["ablation"] is None
    assert native.read_bytes() == before


def test_cross_refuses_same_task(typed, heldout, tmp_path):
    run_dir = write_session(tmp_path / "runs" / "1")
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(run_dir, heldout, on=("typed", "eval"))
    assert exc.value.code == EvalRefusalCode.CROSS_SAME_TASK


def test_cross_refuses_foreign_encoder(typed, tmp_path):
    root = tmp_path / "heldout"
    write_heldout(root, "parity", "toy", [("0101010101", "even", "even")])
    run_dir = write_session(tmp_path / "runs" / "1")
    with pytest.raises(EvaluationRefused) as exc:
        evaluate(run_dir, root, on=("parity", "toy"))
    assert exc.value.code == EvalRefusalCode.ENCODER_MISMATCH
    assert "typed.ab@1" in exc.value.detail


def test_cross_accepts_a_task_registered_later(typed, heldout, tmp_path, monkeypatch):
    monkeypatch.setitem(TASKS, "legal_r", typed_spec("legal_r"))
    write_heldout(heldout, "legal_r", "eval", TYPED_ROWS)
    run_dir = write_session(tmp_path / "runs" / "1")
    record = load(evaluate(run_dir, heldout, on=("legal_r", "eval")))
    assert record["target"]["task"] == "legal_r"
    assert record["metrics"]["accuracy"] == {"correct": 6, "n": 6}


# --- commande -------------------------------------------------------------------------------


def test_cli_lot_dir_lists_unfrozen_and_filters_task(typed, heldout, tmp_path, capsys):
    lot = tmp_path / "runs" / "1"
    frozen = write_session(lot, attempt=1)
    unfrozen = write_session(lot, attempt=2, frozen=False)
    assert lot_dirs(lot) == ([frozen], [unfrozen], [])
    code = main(["evaluate", "--lot-dir", str(lot), "--heldout-root", str(heldout)])
    out = capsys.readouterr()
    assert code == 0 and f"non gelée : {unfrozen.name}" in out.err
    assert (frozen / "eval.json").is_file() and not (unfrozen / "eval.json").exists()
    (frozen / "eval.json").unlink()
    assert main(["evaluate", "--lot-dir", str(lot), "--from-task", "parity"]) == 0
    assert not (frozen / "eval.json").exists()


def test_cli_reports_every_refusal_and_continues(typed, heldout, tmp_path, capsys):
    lot = tmp_path / "runs" / "1"
    bad = write_session(lot, attempt=1)
    (bad / "frozen" / "manifest.json").write_text("{}", "utf-8")
    good = write_session(lot, attempt=2)
    code = main(["evaluate", str(bad), str(good), "--heldout-root", str(heldout)])
    err = capsys.readouterr().err
    assert code == 1 and "fingerprint_mismatch" in err
    assert (good / "eval.json").is_file()


@pytest.mark.parametrize(
    "argv",
    [
        ["evaluate"],
        ["evaluate", "x", "--lot-dir", "y"],
        ["evaluate", "x", "--on", "typed"],
        ["evaluate", "x", "--on", "typed:eval"],
    ],
)
def test_cli_usage_errors(argv):
    assert main(argv) == 2


def test_verification_only_keeps_existing_measures(typed, heldout, tmp_path):
    """Revue 1-14 : un contrôle de gel relancé sans --heldout-root n'efface pas les mesures."""
    run_dir = write_session(tmp_path / "runs" / "1")
    measured = load(evaluate(run_dir, heldout))
    assert measured["metrics"]
    assert load(evaluate(run_dir)) == measured


def test_cli_dataset_requires_heldout_root(typed, tmp_path, capsys):
    run_dir = write_session(tmp_path / "runs" / "1")
    assert main(["evaluate", str(run_dir), "--dataset", "eval"]) == 2
    assert not (run_dir / "eval.json").exists()
