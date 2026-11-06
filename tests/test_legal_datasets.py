"""Jeux de S et S-réservé : tailles, proportions, recouvrement, octets (story 1-9, D4 et D6)."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date

import numpy as np
import pytest

from nn_weight_writing import cli
from nn_weight_writing.datasets import legal
from nn_weight_writing.datasets.legal import Sizes, generate, generate_rows
from nn_weight_writing.datasets.legal_rules import easter, number_year, violations
from nn_weight_writing.evaluation.labels import read_labels
from nn_weight_writing.tasks.io import BundleError, read_examples
from nn_weight_writing.tasks.legal.facts import facts_sha256, load_facts
from nn_weight_writing.tasks.legal.reference import parse_reference
from nn_weight_writing.tasks.legal.types import HELD_OUT, KNOWN, TYPES

ALL = [t.id for t in TYPES]
DIRS = [
    "heldout/legal_s/eval",
    "heldout/legal_s_reserved/eval",
    "data/legal_s/session",
    "data/legal_s/train",
    "data/legal_s_reserved/session",
    "data/legal_s_reserved/train",
]


@pytest.fixture(scope="module")
def rows():
    return generate_rows(0)


@pytest.fixture(scope="module")
def root(tmp_path_factory):
    path = tmp_path_factory.mktemp("legal")
    generate(seed=0, root=path)
    return path


def fakes(data):
    return [r for r in data if r.label == "fake"]


def jurisdiction_counts(data):
    return Counter(parse_reference(r.raw).jurisdiction for r in data)


def test_reals_violate_nothing_and_fakes_exactly_their_type(rows):
    assert {k: len(v) for k, v in rows.items()} == {
        "eval": 4000,
        "s_session": 40,
        "s_train": 8192,
        "r_session": 40,
        "r_train": 8192,
    }
    for data in rows.values():
        for row in data:
            found = violations(parse_reference(row.raw))
            assert found == (frozenset() if row.label == "real" else frozenset({row.type_id}))
            assert (row.type_id == "real") == (row.label == "real")


def test_same_seed_same_bytes_other_seed_differs(tmp_path, root):
    generate(seed=0, root=tmp_path / "again")
    generate(seed=1, root=tmp_path / "other")
    for directory in DIRS:
        for name in ("examples.jsonl", "labels.jsonl", "dataset.json"):
            assert (root / directory / name).read_bytes() == (
                tmp_path / "again" / directory / name
            ).read_bytes()
    assert (root / DIRS[0] / "examples.jsonl").read_bytes() != (
        tmp_path / "other" / DIRS[0] / "examples.jsonl"
    ).read_bytes()


def test_eval_independent_of_other_sizes(rows):
    small = generate_rows(0, Sizes(eval=4000, session=10, train=100))
    assert small["eval"] == rows["eval"]
    assert len(small["s_train"]) == 100 and len(small["r_session"]) == 10


def test_splits_pairwise_disjoint(rows):
    raws = {k: {r.raw for r in v} for k, v in rows.items()}
    ids = {k: {r.id for r in v} for k, v in rows.items()}
    keys = list(rows)
    for i, a in enumerate(keys):
        assert len(raws[a]) == len(rows[a])
        for b in keys[i + 1 :]:
            assert not raws[a] & raws[b], (a, b)
            assert not ids[a] & ids[b], (a, b)
    assert {next(iter(ids[k]))[:7] for k in keys} == {
        "legal-e",
        "legal-s",
        "legal-t",
        "legal-r",
        "legal-u",
    }


def test_reserved_eval_is_s_eval_with_all_15_types(root):
    s, r = root / DIRS[0], root / DIRS[1]
    for name in ("examples.jsonl", "labels.jsonl"):
        assert (s / name).read_bytes() == (r / name).read_bytes()
    counts = Counter(row["type_id"] for row in map(json.loads, (r / "labels.jsonl").open("rb")))
    assert all(counts[t] >= 133 for t in ALL), counts
    assert counts["real"] == 2000


def test_reserved_session_and_train_hold_only_known_types(rows):
    for key in ("r_session", "r_train"):
        types = {r.type_id for r in rows[key]}
        assert types == set(KNOWN) | {"real"}
        assert not types & set(HELD_OUT)


EXPECTED = {
    "eval": (667, 667, 666),
    "s_session": (7, 7, 6),
    "s_train": (1366, 1365, 1365),
    "r_session": (9, 6, 5),
    "r_train": (1844, 1103, 1149),
}


@pytest.mark.parametrize("key", list(EXPECTED))
def test_proportions(rows, key):
    data = rows[key]
    n = len(data)
    assert Counter(r.label for r in data) == {"real": n // 2, "fake": n // 2}
    ids = ALL if not key.startswith("r_") else list(KNOWN)
    counts = Counter(r.type_id for r in fakes(data))
    for tid in ids:
        assert abs(counts[tid] - (n // 2) / len(ids)) <= 1, (tid, counts[tid])
    fake_j, real_j = (
        jurisdiction_counts(fakes(data)),
        jurisdiction_counts([r for r in data if r.label == "real"]),
    )
    assert fake_j == real_j
    assert tuple(fake_j[j] for j in ("cc", "ce", "ca")) == EXPECTED[key]
    if not key.startswith("r_"):
        assert max(fake_j.values()) - min(fake_j.values()) <= 1
    if key == "eval":
        t05 = {parse_reference(r.raw).jurisdiction for r in data if r.type_id == "t05"}
        assert t05 == {"cc", "ce"}


@pytest.mark.parametrize("key", list(EXPECTED))
def test_order_and_ids_do_not_leak_label(rows, key):
    data = rows[key]
    prefix = data[0].id[:-5]
    assert [r.id for r in data] == [f"{prefix}{i:05d}" for i in range(1, len(data) + 1)]
    labels = [r.label for r in data]
    assert labels != sorted(labels) and labels != sorted(labels, reverse=True)
    assert any(a == b for a, b in zip(labels, labels[1:], strict=False))  # pas alterné
    assert labels != ["real", "fake"] * (len(labels) // 2)
    assert labels != ["fake", "real"] * (len(labels) // 2)


def test_dataset_json_composition(root):
    for directory in DIRS:
        meta = json.loads((root / directory / "dataset.json").read_text("utf-8"))
        comp = meta["composition"]
        assert (meta["generator"], meta["version"], meta["seed"]) == ("legal", 1, 0)
        assert comp["facts_sha256"] == facts_sha256()
        assert comp["encoder"] == "legal.chars@1"
        assert comp["corpus_date"] == "2026-11-01"
        assert comp["window"] == ["2001-01-02", "2026-10-31"]
        assert comp["n_real"] == comp["n_fake"] == meta["n"] // 2
        assert sum(comp["by_type"].values()) == comp["n_fake"] and set(comp["by_type"]) == set(ALL)
        assert sum(comp["by_jurisdiction"]["real"].values()) == comp["n_real"]
        assert [t["id"] for t in comp["types"]] == ALL
        reserved = "reserved" in directory
        assert comp["task"] == ("legal_s_reserved" if reserved else "legal_s")
        assert comp["split"] == directory.rsplit("/", 1)[1]
        assert comp["visible_types"] == (list(KNOWN) if reserved else ALL)
        assert comp["held_out_types"] == (list(HELD_OUT) if reserved else [])
    t02 = next(t for t in comp["types"] if t["id"] == "t02")
    assert (t02["status"], t02["nuss"], t02["jurisdictions"]) == (
        "attested",
        "attested_secondary",
        ["cc", "ce", "ca"],
    )


def test_session_file_is_a_bundle_source(root):
    session = root / "data" / "legal_s" / "session"
    examples = read_examples(session / "examples.jsonl")
    assert len(examples) == 40 and {e.id[:7] for e in examples} == {"legal-s"}
    with pytest.raises(BundleError):
        read_examples(session / "labels.jsonl")
    assert len(read_labels(session / "labels.jsonl")) == 40


def test_generate_refuses_existing_before_writing(tmp_path):
    (tmp_path / "heldout" / "legal_s" / "eval").mkdir(parents=True)
    (tmp_path / "heldout" / "legal_s" / "eval" / "x").write_text("x")
    with pytest.raises(FileExistsError):
        generate(seed=0, root=tmp_path, sizes=Sizes(eval=30, session=10, train=20))
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "heldout" / "legal_s_reserved").exists()


@pytest.mark.parametrize("sizes", [Sizes(session=41), Sizes(train=0), Sizes(eval=3)])
def test_odd_size_refused(sizes):
    with pytest.raises(ValueError, match="paire"):
        generate_rows(0, sizes)


def test_cli_datagen_legal(tmp_path, capsys):
    argv = ["datagen", "legal", "--seed", "0", "--root", str(tmp_path)]
    assert cli.main(argv) == 0
    out = capsys.readouterr().out.split()
    assert len(out) == 6 and out[0].endswith("eval")
    assert cli.main(argv) == 1
    assert "datagen refusé" in capsys.readouterr().err
    assert cli.main([*argv[:-2], "--n", "10", "--root", str(tmp_path / "x")]) == 2
    assert cli.main([*argv[:-2], "--n-heldout", "10", "--root", str(tmp_path / "x")]) == 2
    assert not (tmp_path / "x").exists()
    assert cli.main(["datagen", "parity", "--seed", "0", "--root", str(tmp_path / "toy")]) == 0
    assert [
        json.loads(line)["id"] for line in (tmp_path / "toy/data/parity/toy/examples.jsonl").open()
    ][-1] == "parity-d00256"
    toy = tmp_path / "toy/heldout/parity/toy/examples.jsonl"
    assert sum(1 for _ in toy.open()) == 400


# --- Décisions de relecture ---------------------------------------------------------------


def test_real_gaps_follow_the_observed_distribution_up_to_the_maximum():  # O2
    f = load_facts()
    cal = legal.build_calendar(f)
    rng = np.random.default_rng(123)
    for jurisdiction, maximum in (("cc", 6), ("ca", 8)):
        gaps = Counter()
        for _ in range(30000):
            ref = legal.draw_real(rng, f, cal, jurisdiction)
            gaps[ref.year - number_year(ref.number, ref.year)] += 1
        assert max(gaps) <= maximum and min(gaps) >= 0
        assert gaps[5] > 0 and gaps[6] > 0, gaps
        assert gaps[1] > gaps[0] > gaps[4] > 0 or jurisdiction == "ca"
    assert f.cc_old_gap == f.ca_old_gap == (10, 15)


def test_t12_holiday_half_draws_only_movable_holidays(rows):  # O3
    f = load_facts()
    refs = [parse_reference(x.raw) for x in rows["eval"] if x.type_id == "t12"]
    days = [date(r.year, r.month, r.day) for r in refs]
    sundays = [d for d in days if d.weekday() == 6]
    others = [d for d in days if d.weekday() != 6]
    assert len(sundays) > 50 and len(others) > 50
    movable = {"easter_monday", "ascension"}
    for d in others:
        offset = (d - easter(d.year)).days
        assert offset in {f.easter_offsets[n] for n in movable}, d
    assert {(d - easter(d.year)).days for d in others} == {1, 39}
    assert not any((d.month, d.day) in f.holiday_fixed for d in others)
    assert 50 not in {(d - easter(d.year)).days for d in days}  # jamais le lundi de Pentecôte


def test_court_of_appeal_serials_reach_the_sample_maximum(rows):  # O10
    f = load_facts()
    assert f.ca_serial == (1, 24999)
    serials = [
        int(parse_reference(r.raw).number[3:])
        for r in rows["s_train"]
        if r.label == "real" and parse_reference(r.raw).jurisdiction == "ca"
    ]
    assert max(serials) > 21304 and min(serials) >= 1 and max(serials) <= 24999
    assert sum(s >= 20000 for s in serials) > 100


def test_t15_does_not_bias_the_draw_toward_working_days(rows):  # O6
    days = [parse_reference(r.raw) for r in rows["s_train"] if r.type_id == "t15"]
    assert len(days) == 273
    assert all((d.day, d.month) == (29, 2) and d.year % 4 for d in days)
    per_year = Counter(d.year for d in days)
    assert len(per_year) == 20 and 4 <= min(per_year.values()) <= max(per_year.values()) <= 30
