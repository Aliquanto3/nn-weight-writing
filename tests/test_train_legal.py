"""Témoins C et F sur S et S-réservé, mesure par groupe de types, réentraînement (1-11)."""

from __future__ import annotations

import json
import subprocess
import sys

import numpy as np
import pytest

pytest.importorskip("torch")

from nn_weight_writing import network  # noqa: E402
from nn_weight_writing.baselines.curve import measure, summarize  # noqa: E402
from nn_weight_writing.baselines.train import (  # noqa: E402
    get_task,
    load_train_config,
    reference_manifest,
    retrain,
    train,
)
from nn_weight_writing.cli import main  # noqa: E402
from nn_weight_writing.datasets.legal import Sizes, generate  # noqa: E402
from nn_weight_writing.evaluation.labels import read_labels  # noqa: E402
from nn_weight_writing.evaluation.verify import EvaluationRefused  # noqa: E402
from nn_weight_writing.network import sha256_file, tree_sha256  # noqa: E402
from nn_weight_writing.tasks.legal.types import HELD_OUT  # noqa: E402


def n_params(manifest: dict) -> int:
    return sum(layer["in"] * layer["out"] + layer["out"] for layer in manifest["layers"])


@pytest.fixture(scope="module")
def legal_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("legal")
    generate(seed=0, root=root, sizes=Sizes(eval=300, session=30, train=300))
    return root


@pytest.mark.parametrize("name", ["legal_s", "legal_s_reserved"])
def test_reference_architectures_have_the_documented_sizes(name):
    config = load_train_config(name)
    assert config.n_values == (64, 256, 1024, 8192, 32768) and config.seeds == (0, 1, 2)
    task = get_task(name)
    c = reference_manifest(task, config)
    f = reference_manifest(task, config, prepared=True)
    assert (c["encoder"], n_params(c)) == ("legal.chars@1", 98018)
    assert (f["encoder"], n_params(f)) == ("legal.fields@2", 77154)
    assert [layer["out"] for layer in c["layers"]] == [32, 2]


def test_prepared_inputs_are_refused_for_a_toy_task():
    with pytest.raises(ValueError, match="pas d'entrées préparées"):
        reference_manifest(get_task("parity"), load_train_config("parity"), prepared=True)


@pytest.mark.parametrize("prepared", [False, True])
def test_train_c_and_f_freeze_and_measure(legal_root, prepared):
    data = legal_root / "data" / "legal_s_reserved" / "train"
    held = legal_root / "heldout" / "legal_s_reserved" / "eval"
    run_dir = train(
        "legal_s_reserved",
        data,
        n=300,
        seed=0,
        runs_root=legal_root / "runs",
        lot="t",
        prepared=prepared,
    )
    method = "F" if prepared else "C"
    assert run_dir.name == f"legal_s_reserved-{method}-n300-s0"
    run = json.loads((run_dir / "run.json").read_text("utf-8"))
    assert (run["baseline"], run["task"]) == (method, "legal_s_reserved")
    manifest, _ = network.load(run_dir / "frozen")
    assert manifest["encoder"] == ("legal.fields@2" if prepared else "legal.chars@1")
    counts = measure(run_dir, "legal_s_reserved", held)
    labels = read_labels(held / "labels.jsonl").values()
    n_held = sum(1 for lab in labels if lab.type_id in HELD_OUT)
    n_real = sum(1 for lab in labels if lab.label == "real")
    assert counts["all"]["n"] == 300 == sum(counts[g]["n"] for g in counts if g != "all")
    assert counts["fake_held_out"]["n"] == n_held > 0
    assert counts["real"]["n"] == n_real
    assert counts["fake_known"]["n"] == 300 - n_real - n_held
    assert counts["all"]["correct"] == sum(counts[g]["correct"] for g in counts if g != "all")
    assert counts["all"]["correct"] / 300 > 0.5  # apprend quelque chose avec 300 exemples


def test_train_refuses_a_dataset_of_the_other_legal_task(legal_root, tmp_path):
    data = legal_root / "data" / "legal_s_reserved" / "train"
    with pytest.raises(ValueError, match="tâche 'legal_s_reserved', séance de 'legal_s'"):
        train("legal_s", data, n=64, seed=0, runs_root=tmp_path, lot="x")


def test_legacy_fields_v1_runs_stay_measurable(legal_root, tmp_path):
    from nn_weight_writing.baselines.train import _encode_for
    from nn_weight_writing.tasks.legal.encoders import encode_fields

    task = get_task("legal_s")
    assert _encode_for(task, "legal.fields@1") is encode_fields
    with pytest.raises(ValueError, match="inconnu"):
        _encode_for(task, "legal.fields@9")


def test_measure_refuses_a_run_of_another_task(legal_root):
    data = legal_root / "data" / "legal_s" / "train"
    run_dir = train("legal_s", data, n=64, seed=1, runs_root=legal_root / "runs", lot="o")
    held = legal_root / "heldout" / "legal_s_reserved" / "eval"
    with pytest.raises(ValueError, match="réseau écrit pour 'legal_s'"):
        measure(run_dir, "legal_s_reserved", held)


def test_measure_checks_fingerprints_before_reading_the_heldout_set(legal_root, tmp_path):
    data = legal_root / "data" / "legal_s" / "train"
    run_dir = train("legal_s", data, n=64, seed=2, runs_root=tmp_path, lot="v")
    with (run_dir / "frozen" / "weights.bin").open("ab") as f:
        f.write(b"x")
    with pytest.raises(EvaluationRefused):
        measure(run_dir, "legal_s", tmp_path / "absent")  # le réservé n'est pas ouvert


def test_retrain_keeps_the_architecture_with_fresh_random_weights(legal_root):
    data = legal_root / "data" / "legal_s" / "train"
    runs = legal_root / "runs"
    source = train("legal_s", data, n=64, seed=3, runs_root=runs, lot="src", prepared=True)
    out = retrain(source, data, n=128, seed=9, runs_root=runs, lot="re")
    with pytest.raises(ValueError, match="séance de 'legal_s'"):
        other = legal_root / "data" / "legal_s_reserved" / "train"
        retrain(source, other, n=128, seed=8, runs_root=runs, lot="re")
    assert out.name == "legal_s-F-n64-s3-retrain-n128-s9"
    m_src, w_src = network.load(source / "frozen")
    m_new, w_new = network.load(out / "frozen")
    assert m_new == m_src
    assert not np.array_equal(w_new["L0.W"], w_src["L0.W"])
    run = json.loads((out / "run.json").read_text("utf-8"))
    src_run = json.loads((source / "run.json").read_text("utf-8"))
    assert run["dataset"]["retrained_from"] == {
        "session": source.name,
        "tree_sha256": src_run["tree_sha256"],
    }
    assert (run["n"], run["seed"], run["task"]) == (128, 9, "legal_s")


def test_retrain_refuses_a_tampered_source(legal_root, tmp_path):
    data = legal_root / "data" / "legal_s" / "train"
    source = train("legal_s", data, n=64, seed=4, runs_root=tmp_path, lot="s")
    (source / "frozen" / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(EvaluationRefused):
        retrain(source, data, n=64, seed=0, runs_root=tmp_path, lot="r")


def test_retrain_drops_the_blocks_declared_by_a_session(legal_root, tmp_path):
    data = legal_root / "data" / "legal_s" / "train"
    source = train("legal_s", data, n=64, seed=6, runs_root=tmp_path, lot="b")
    path = source / "frozen" / "manifest.json"
    manifest = json.loads(path.read_text("utf-8"))
    manifest["blocks"] = [{"rule": "r", "types": ["t10"], "units": [[0, 0]]}]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    run_path = source / "run.json"
    run = json.loads(run_path.read_text("utf-8"))
    run["files"]["manifest.json"] = sha256_file(path)
    run["tree_sha256"] = tree_sha256(run["files"])
    run_path.write_text(json.dumps(run), encoding="utf-8")
    out = retrain(source, data, n=64, seed=0, runs_root=tmp_path, lot="b2")
    new_manifest, _ = network.load(out / "frozen")
    assert "blocks" not in new_manifest and new_manifest["layers"] == manifest["layers"]


def test_cli_train_prepared_and_retrain(legal_root, capsys):
    data = str(legal_root / "data" / "legal_s" / "train")
    runs = str(legal_root / "runs")
    base = ["--data", data, "--seed", "5", "--runs-root", runs]
    assert main(["train", "legal_s", "--prepared", "--n", "64", "--lot", "cli", *base]) == 0
    source = capsys.readouterr().out.strip()
    assert source.endswith("legal_s-F-n64-s5")
    assert main(["retrain", source, "--n", "64", "--lot", "cli2", *base]) == 0
    assert capsys.readouterr().out.strip().endswith("legal_s-F-n64-s5-retrain-n64-s5")


def test_summarize_mean_and_population_std():
    def rec(seed, correct):
        acc = {g: {"correct": correct, "n": 10} for g in ("all", "real", "fake_known")}
        acc["fake_held_out"] = {"correct": 0, "n": 0}
        return {"task": "t", "method": "C", "n": 64, "seed": seed, "seconds": 2.0, "accuracy": acc}

    (row,) = summarize([rec(0, 6), rec(1, 8)])
    assert row["all"] == (0.7, pytest.approx(0.1))
    assert "fake_held_out" not in row and row["seeds"] == [0, 1]


def test_session_side_never_loads_torch():
    code = (
        "import sys, nn_weight_writing.cli, nn_weight_writing.session.run, "
        "nn_weight_writing.session.service, nn_weight_writing.tasks.registry; "
        "sys.exit(1 if 'torch' in sys.modules else 0)"
    )
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
