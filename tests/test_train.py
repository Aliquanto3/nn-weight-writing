"""Témoin C : couches PyTorch, parité avec NumPy, entraînement et format commun (AD-3, AD-17)."""

from __future__ import annotations

import json

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from nn_weight_writing import network  # noqa: E402
from nn_weight_writing.baselines import torch_layers  # noqa: E402
from nn_weight_writing.baselines.train import (  # noqa: E402
    load_train_config,
    reference_manifest,
    train,
)
from nn_weight_writing.cli import main  # noqa: E402
from nn_weight_writing.datasets.toy import generate  # noqa: E402
from nn_weight_writing.evaluation.score import score_frozen  # noqa: E402
from nn_weight_writing.evaluation.verify import verify_frozen  # noqa: E402
from nn_weight_writing.network.layers import ACTIVATIONS  # noqa: E402
from nn_weight_writing.tasks.toy import get_task  # noqa: E402


@pytest.mark.parametrize("activation", sorted(ACTIVATIONS))
def test_torch_forward_matches_numpy_forward(activation):
    rng = np.random.default_rng(0)
    manifest = {
        "encoder": "test.x@1",
        "layers": [
            {"type": "dense", "in": 5, "out": 7, "activation": activation},
            {"type": "dense", "in": 7, "out": 3, "activation": "identity"},
        ],
    }
    weights = {
        "L0.W": rng.normal(size=(5, 7)).astype(np.float32),
        "L0.b": rng.normal(size=7).astype(np.float32),
        "L1.W": rng.normal(size=(7, 3)).astype(np.float32),
        "L1.b": rng.normal(size=3).astype(np.float32),
    }
    x = rng.normal(size=(11, 5)).astype(np.float32) * 3
    module = torch_layers.build_module(manifest)
    torch_layers.load_weights(module, weights)
    with torch.no_grad():
        got = module(torch.from_numpy(x)).numpy()
    np.testing.assert_allclose(got, network.forward(manifest, weights, x), rtol=1e-5, atol=1e-5)
    exported = torch_layers.export_weights(module)
    assert set(exported) == set(weights)
    for key, value in weights.items():
        assert exported[key].dtype == np.float32
        np.testing.assert_array_equal(exported[key], value)


def test_torch_registry_covers_the_numpy_registry():
    assert set(torch_layers.TORCH_ACTIVATIONS) == set(ACTIVATIONS)


def test_train_config_reads_reference_architecture():
    config = load_train_config("compare")
    assert config.hidden == (16,)
    assert config.n_values == (64, 256) and config.seeds == (0, 1, 2)
    with pytest.raises(KeyError, match="pas d'architecture de référence"):
        load_train_config("nope")


def test_reference_manifest_shape():
    manifest = reference_manifest(get_task("automaton"), load_train_config("automaton"))
    assert manifest["encoder"] == "automaton.bits@1"
    assert [(layer["in"], layer["out"], layer["activation"]) for layer in manifest["layers"]] == [
        (10, 32, "relu"),
        (32, 2, "identity"),
    ]


@pytest.fixture(scope="module")
def compare_data(tmp_path_factory):
    root = tmp_path_factory.mktemp("c")
    return (*generate("compare", seed=2, n=256, n_heldout=300, root=root), root)


def test_train_writes_the_common_format_and_learns(compare_data):
    data, held, root = compare_data
    run_dir = train("compare", data, n=256, seed=0, runs_root=root / "runs", lot="toy")
    assert run_dir == root / "runs" / "toy" / "train" / "compare-C-n256-s0"
    assert sorted(p.name for p in run_dir.iterdir()) == ["eval.json", "frozen", "run.json"]
    run = json.loads((run_dir / "run.json").read_text("utf-8"))
    assert (run["baseline"], run["n"], run["seed"]) == ("C", 256, 0)
    assert run["run_id"] == "compare-C-n256-s0"
    assert run["dataset"]["path"] == "data/compare/toy"
    meta = json.loads((data / "dataset.json").read_text("utf-8"))
    assert run["dataset"]["files"] == meta["files"]
    kind, _, tree, _ = verify_frozen(run_dir)
    assert (kind, tree) == ("baseline", run["tree_sha256"])
    score = score_frozen(
        run_dir, get_task("compare"), held / "examples.jsonl", held / "labels.jsonl"
    )
    assert score.accuracy > 0.85


def test_train_is_deterministic_per_seed_and_differs_across_seeds(compare_data):
    data, _, root = compare_data
    a = train("compare", data, n=64, seed=1, runs_root=root / "a", lot="x")
    b = train("compare", data, n=64, seed=1, runs_root=root / "b", lot="x")
    c = train("compare", data, n=64, seed=2, runs_root=root / "c", lot="x")
    tree = [json.loads((d / "run.json").read_text("utf-8"))["tree_sha256"] for d in (a, b, c)]
    assert tree[0] == tree[1] != tree[2]
    wa, wb = network.load(a / "frozen")[1], network.load(b / "frozen")[1]
    assert all(np.array_equal(wa[k], wb[k]) for k in wa)


def test_train_refuses_n_out_of_range(compare_data):
    data, _, root = compare_data
    with pytest.raises(ValueError, match=r"n=257 hors de 1\.\.256"):
        train("compare", data, n=257, seed=0, runs_root=root / "r", lot="x")
    with pytest.raises(ValueError, match="n=0 hors"):
        train("compare", data, n=0, seed=0, runs_root=root / "r", lot="x")


def test_train_refuses_the_heldout_set(compare_data, capsys):
    _, held, root = compare_data
    with pytest.raises(ValueError, match="jeu réservé refusé"):
        train("compare", held, n=64, seed=0, runs_root=root / "h", lot="x")
    argv = ["train", "compare", "--data", str(held), "--n", "64", "--seed", "0"]
    assert main([*argv, "--runs-root", str(root / "h")]) == 1
    assert "jeu réservé refusé" in capsys.readouterr().err
    assert not (root / "h").exists()


def test_cli_train_then_refuses_second_run(compare_data, capsys):
    data, _, root = compare_data
    argv = ["train", "compare", "--data", str(data), "--n", "64", "--seed", "5"]
    argv += ["--runs-root", str(root / "cli")]
    assert main(argv) == 0
    assert capsys.readouterr().out.strip().endswith("compare-C-n64-s5")
    assert main(argv) == 1
    assert "train refusé : témoin déjà gelé" in capsys.readouterr().err
