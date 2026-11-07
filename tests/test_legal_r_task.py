"""Tâche `legal_r` (story 1-13, D6) : registre, description, frontière, S inchangé, témoins."""

from __future__ import annotations

import hashlib
import json
from datetime import date

import pytest
from legal_r_jeu_support import synthetic_pairs

from nn_weight_writing import cli
from nn_weight_writing.datasets.legal_r.dataset import split_pairs, write_r_dataset
from nn_weight_writing.session.prompt import sha256_text, system_prompt
from nn_weight_writing.tasks.legal import TASKS
from nn_weight_writing.tasks.legal import task as task_module
from nn_weight_writing.tasks.legal.types import TYPES
from nn_weight_writing.tasks.registry import get_task

# Relevés dans `bundle/task.json` et le journal des séances B Sonnet de 1-10 (lot 1, 2026-11-06).
S_DESCRIPTION_SHA = {
    "legal_s": "726d4b7969aa7d6e9a12b58666974e0794f95873728e4bc09273068d161308b8",
    "legal_s_reserved": "3d6bd0a87d98c7afadb267daf1b4fa8ac5c77b08bfd6d9eec2423b9c17279a93",
}
S_VOCABULARY_SHA = {
    "legal_s": "67e8baf5b1f2ce9889b0338974f424ee868dd3f67adb2bf0322727962d938522",
    "legal_s_reserved": "a5f22219a9c345b9ca0689d4f09e4ae468ba0eca5f41de7cb2f36c4b9dea2a5c",
}
SYSTEM_PROMPT_B_SHA = "fa5f8335a67ecdb29ffb938615b598d505e4ee35b6ee4f696dfed4725c4ecd99"
R_VOCABULARY = ("t01", "t02", "t03", "t05", "t06", "t07", "t08", "t10", "t11", "t12", "t14")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_s_task_prompts_unchanged():
    for name in ("legal_s", "legal_s_reserved"):
        spec = get_task(name)
        assert _sha(spec.description) == S_DESCRIPTION_SHA[name]
        vocabulary = json.dumps(list(spec.vocabulary), ensure_ascii=False, sort_keys=True)
        assert _sha(vocabulary) == S_VOCABULARY_SHA[name]
        assert "x01" not in {v["id"] for v in spec.vocabulary}
    assert sha256_text(system_prompt("B", 20)) == SYSTEM_PROMPT_B_SHA
    assert len(TYPES) == 15  # x01 n'entre pas dans la composition de S


def test_legal_r_task_registered():
    spec = get_task("legal_r")
    assert spec.codec.encoder_id == "legal.chars@1" and spec.session_datasets == ("session",)
    ids = [v["id"] for v in spec.vocabulary]
    assert ids == [*R_VOCABULARY, "t15", "x01"] and len(ids) == 13
    assert not {"c00", "t04", "t09", "t13"} & set(ids)
    text = spec.description
    assert "exactement une incohérence" not in text and "cour d'appel" not in text.lower()
    assert "CA " not in text and "AA/NNNNN" not in text
    assert "Le corpus est arrêté au 7 novembre 2026." in text
    assert "aucune incohérence visible" in text and "petits modèles de langage" in text
    assert "juge des référés" in text and "ch. réunies" in text
    assert text.endswith(task_module.TAIL)
    t06 = next(v for v in spec.vocabulary if v["id"] == "t06")
    assert "7 novembre 2026" in t06["description"]
    s_types = {v["id"]: v["description"] for v in get_task("legal_s").vocabulary}
    for entry in spec.vocabulary:
        if entry["id"] not in {"t06", "x01"}:
            assert entry["description"] == s_types[entry["id"]]
    assert hash(TASKS["legal_r"])  # la tâche reste hachable (paires de remplacement)


def test_r_corpus_text_formats_the_date():
    assert task_module.r_corpus_text(date(2026, 11, 1)) == "1er novembre 2026"
    assert task_module.r_corpus_text(date(2026, 12, 3)) == "3 décembre 2026"
    assert task_module.r_corpus_text(None) == task_module.R_CORPUS_PENDING


def _session_argv(tmp_path, dataset):
    return [
        "session",
        "--task",
        "legal_r",
        "--dataset",
        dataset,
        "--method",
        "B",
        "--model",
        "sonnet-5.5",
        "--attempt",
        "1",
        "--seed",
        "0",
        "--lot",
        "1",
        "--data-dir",
        str(tmp_path / "data"),
        "--runs-dir",
        str(tmp_path / "runs"),
        "--ledger",
        str(tmp_path / "ledger.csv"),
    ]


def test_legal_r_session_dataset_whitelist(tmp_path, capsys, monkeypatch):
    examples = tmp_path / "data" / "legal_r" / "session" / "examples.jsonl"
    examples.parent.mkdir(parents=True)
    examples.write_text('{"id": "jr-s00001", "raw": "CE, Sect., 1er mars 2023, n° 470001"}\n')
    assert cli.main(_session_argv(tmp_path, "eval")) == 2
    assert "jeu de séance inconnu : eval ; autorisés : session" in capsys.readouterr().err
    assert cli.main(_session_argv(tmp_path, "train")) == 2
    assert "pas un jeu de séance" in capsys.readouterr().err
    monkeypatch.setattr(task_module, "R_CORPUS_DATE", None)  # garde d'avant le jeu figé
    assert cli.main(_session_argv(tmp_path, "session")) == 2
    assert "R_CORPUS_DATE non fixée" in capsys.readouterr().err
    assert not (tmp_path / "runs").exists() and not (tmp_path / "ledger.csv").exists()


def _r_sets(root):
    out = split_pairs(synthetic_pairs(200), seed=0)
    meta = {
        "extraction_date": "2026-11-07",
        "extraction_dates": {"judilibre": "2026-11-07", "ce-opendata": "2026-11-06"},
    }
    write_r_dataset(root / "data" / "legal_r" / "train", out["train"], split="train", meta=meta)
    write_r_dataset(root / "heldout" / "legal_r" / "eval", out["eval"], split="eval", meta=meta)
    return out


def test_cross_eval_s_to_r(tmp_path):
    pytest.importorskip("torch")
    from nn_weight_writing.baselines.train import train
    from nn_weight_writing.datasets.legal import Sizes, generate
    from nn_weight_writing.evaluation.verify import evaluate

    generate(seed=0, root=tmp_path, sizes=Sizes(eval=100, session=20, train=100))
    out = _r_sets(tmp_path)
    run_dir = train(
        "legal_s",
        tmp_path / "data" / "legal_s" / "train",
        n=64,
        seed=0,
        runs_root=tmp_path / "runs",
        lot="t",
    )
    path = evaluate(run_dir, tmp_path / "heldout", on=("legal_r", "eval"))
    assert path.name == "eval-cross-legal_r-eval.json"
    record = json.loads(path.read_text("utf-8"))
    assert record["target"]["cross"] is True and record["target"]["task"] == "legal_r"
    assert record["target"]["written_task"] == "legal_s"
    by_type = record["metrics"]["by_type"]
    n_c00 = sum(p.fake.type_id == "c00" for p in out["eval"])
    assert n_c00 > 0 and by_type["c00"]["n"] == n_c00
    assert by_type["real"]["n"] == len(out["eval"])
    assert not (run_dir / "eval.json").exists() or "legal_r" not in (
        run_dir / "eval.json"
    ).read_text("utf-8")


def test_train_legal_r(tmp_path, capsys):
    pytest.importorskip("torch")
    _r_sets(tmp_path)
    data = tmp_path / "data" / "legal_r" / "train"
    argv = ["train", "legal_r", "--data", str(data), "--n", "64", "--seed", "0", "--lot", "t"]
    assert cli.main([*argv, "--runs-root", str(tmp_path / "runs")]) == 0
    (run_json,) = (tmp_path / "runs").rglob("run.json")
    run = json.loads(run_json.read_text("utf-8"))
    assert run["task"] == "legal_r" and run["baseline"] == "C"
