"""Jeu R (story 1-13) : fausses, vraies appariées, découpage, construction, plancher.

Aucune donnée réelle : fixtures écrites par `legal_r_jeu_support` et réponses Judilibre de 1-12
(`tests/fixtures/legal_r/judilibre/`). Seul le transport HTTP est un double.
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import pytest
from legal_r_jeu_support import World, classement_row, extraction_row, fake, real, write_world
from legal_r_jeu_support import synthetic_pairs as pairs_of
from legal_r_support import FakeClock, FakeTransport, make_client, ok

from nn_weight_writing.datasets.legal_r import pool as pool_module
from nn_weight_writing.datasets.legal_r.ce_index import CeIndex
from nn_weight_writing.datasets.legal_r.dataset import (
    EXCLUSIONS,
    RBuildError,
    Selection,
    day_kind,
    match_reals,
    raw_gap_class,
    recompute_canonical,
    select_fakes,
    split_pairs,
    split_sizes,
    type_of,
    write_r_dataset,
    year_gap_class,
)
from nn_weight_writing.datasets.legal_r.existence import CoverageWindow
from nn_weight_writing.datasets.legal_r.floor import floor_accuracies
from nn_weight_writing.datasets.legal_r.normalize import (
    fields_from_ce_opendata,
    fields_from_judilibre,
    normalize,
)
from nn_weight_writing.datasets.legal_r.pool import CeDays, cc_day_candidates, reference_of
from nn_weight_writing.publish.checks import check_content, check_sources, extraction_date
from nn_weight_writing.tasks.legal.reference import format_reference, parse_reference

SCRIPT = Path(__file__).parents[1] / "scripts" / "jeu_r.py"
WINDOWS = {
    "cc": CoverageWindow("cc", date(1989, 1, 1), date(2026, 8, 7), "test"),
    "ce": CoverageWindow("ce", date(2021, 9, 30), date(2026, 10, 7), "test"),
}
CORPUS = date(2026, 11, 7)
PERRUCHE = "Cass. ass. plén., 17 novembre 2000, n° 99-13.701"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("jeu_r_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- AC12 : types --------------------------------------------------------------------------


def test_type_of_fake():
    assert type_of({"R-O1", "R-C4"}, ("t03", "t12")) == "t03"
    assert type_of({"R-O5"}, ()) == "x01"
    assert type_of({"R-O5", "R-E3"}, ()) == "x01"
    assert type_of((), ()) == "c00"
    with pytest.raises(ValueError, match="ECLI seules"):
        type_of({"R-E3"}, ())


def test_year_gap_and_day_kind():
    assert year_gap_class("cc", 2015, "13-27.123") == "2"
    assert year_gap_class("cc", 2015, "15-27.123") == "0"
    assert year_gap_class("cc", 2015, "16-27.123") == "0"  # pourvoi après la décision (t01)
    assert year_gap_class("cc", 2015, "14-27.123") == "1"
    assert year_gap_class("cc", 2000, "97-13.701") == "3+"
    assert year_gap_class("cc", 2000, "99-13.701") == "1"
    assert year_gap_class("cc", 2015, "1327123") == "none"
    assert year_gap_class("ce", 2024, "481234") == "none"
    assert raw_gap_class(PERRUCHE) == "1"
    assert day_kind(date(2026, 11, 6)) == "ouvre"
    assert day_kind(date(2026, 11, 7)) == "samedi"
    assert day_kind(date(2026, 11, 8)) == "dimanche_ou_ferie"
    assert day_kind(date(2026, 11, 11)) == "dimanche_ou_ferie"  # fête légale, un mercredi


# --- AC2 : fausses du dénominateur ---------------------------------------------------------


def _rows():
    rows = [
        classement_row(
            "r-u00001", "cc", "civ. 4e", 2010, 5, 4, "09-10.001", "incoherent", ("R-O1",)
        ),
        classement_row(
            "r-u00002", "cc", "civ. 2e", 2027, 5, 6, "26-10.002", "incoherent", ("R-C3",)
        ),
        classement_row("r-u00003", "ce", "6e ch.", 2023, 5, 9, "471003", "coherent_absent"),
        classement_row("r-u00004", "cc", "civ. 1re", 2010, 5, 4, "09-10.004", "exists"),
        classement_row("r-u00005", "cc", "civ. 1re", 2010, 5, 4, "09-10.005", "partial"),
        classement_row("r-u00006", "cc", "civ. 1re", 2010, 5, 4, "09-10.006", "unverifiable"),
        classement_row("r-u00007", "ca", None, 2023, 5, 4, "22/00007", "out_of_scope"),
        classement_row("r-u00008", "ce", "6e ch.", 2023, 5, 9, "471008", "incoherent", ("R-E3",)),
        classement_row(
            "r-u00009", "cc", "civ. 2e", 1975, 5, 6, "74-10.009", "incoherent", ("R-O1",)
        ),
        classement_row("r-u00010", "cc", None, 2010, 5, 4, "09-10.010", "incoherent", ("R-O1",)),
        classement_row("r-u00011", "ce", "6e ch.", 2020, 5, 9, "441011", "incoherent", ("R-O4",)),
        classement_row(
            "r-u00012", "cc", "civ. 4e", 2026, 9, 15, "25-10.012", "incoherent", ("R-O1",)
        ),
        classement_row("r-u00013", "cc", "soc.", 2012, 2, 30, "11-10.013", "incoherent", ("R-C1",)),
        classement_row("r-u00014", "cc", "soc.", 2012, 2, 14, "11-10.014", "coherent_absent"),
    ]
    return rows


def test_select_fakes_gate_denominator_and_window():
    rows = _rows()
    in_s = {rows[13]["canonical"]}
    selection = select_fakes(
        rows, extraction=[extraction_row(r) for r in rows], windows=WINDOWS, s_raws=in_s
    )
    assert [f.unit_id for f in selection.fakes] == ["r-u00001", "r-u00002", "r-u00003", "r-u00013"]
    assert [f.type_id for f in selection.fakes] == ["t03", "t06", "c00", "t02"]
    assert selection.excluded == {
        **dict.fromkeys(EXCLUSIONS, 0),
        "not_in_gate": 4,
        "ecli_only": 1,
        "not_d1": 1,
        "before_window": 2,
        "after_window_not_future": 1,
        "raw_in_s": 1,
    }
    assert selection.before_window == {"cc": 1, "ce": 1}
    assert selection.fakes[0].raw == rows[0]["canonical"]  # jamais retouchée
    assert selection.fakes[0].model == "qwen3.5:2b"


def test_impossible_date_compared_on_year_and_month():
    row = classement_row("r-u00001", "ce", "6e ch.", 2021, 9, 31, "455001", "incoherent", ("R-C1",))
    kept = select_fakes([row], extraction=[extraction_row(row)], windows=WINDOWS)
    assert [f.unit_id for f in kept.fakes] == ["r-u00001"]  # septembre 2021 = mois de début
    row = classement_row("r-u00002", "ce", "6e ch.", 2021, 8, 31, "455002", "incoherent", ("R-O4",))
    gone = select_fakes([row], extraction=[extraction_row(row)], windows=WINDOWS)
    assert gone.fakes == [] and gone.excluded["before_window"] == 1


# --- AC3 : même normaliseur (CAP-11) -------------------------------------------------------


def test_same_normalizer_for_real_and_fake(tmp_path, monkeypatch):
    calls = []

    def spy(fields):
        calls.append(fields.source)
        return normalize(fields)

    monkeypatch.setattr(pool_module, "normalize", spy)
    row = classement_row(
        "r-u00001", "cc", "ass. plén.", 2000, 11, 17, "99-13.701", "coherent_absent"
    )
    slm_text = {"unit_id": "r-u00001", "raw": "Cass., Ass. plén., 17 nov. 2000, n° 99-13.701"}
    fake_raw = recompute_canonical(row, slm_text)
    assert calls == ["slm"]
    clock = FakeClock()
    transport = FakeTransport(
        [("/scan", {"date_start": "2000-11-17"}, [ok("scan_cc_2000-11-17.json")])], clock
    )
    reals = cc_day_candidates(make_client(transport, clock, tmp_path), date(2000, 11, 17))
    assert calls == ["slm", "judilibre", "judilibre"]
    (perruche,) = [c for c in reals if c.number == "99-13.701"]
    assert fake_raw == perruche.raw == PERRUCHE == row["canonical"]


def test_canonical_mismatch_refused():
    row = classement_row("r-u00001", "cc", "civ. 1re", 2015, 3, 12, "13-27.123", "coherent_absent")
    altered = {**row, "canonical": "Cass. civ. 2e, 12 mars 2015, n° 13-27.123"}
    with pytest.raises(RBuildError) as error:
        select_fakes([altered], extraction=[extraction_row(row)], windows=WINDOWS)
    assert error.value.code == "normalizer_mismatch" and error.value.exit_code == 2
    with pytest.raises(RBuildError, match="normalizer_mismatch"):
        select_fakes([row], extraction=[], windows=WINDOWS)  # citation canonique absente


# --- AC6 : appariement ---------------------------------------------------------------------


def _pool_world():
    """30 fausses (Cour de cassation et CE) et une base en mémoire autour de leurs jours."""
    fakes = []
    for i in range(24):
        y = 2005 + i % 12
        day = date(y, 3 + i % 6, 8 + i % 10)
        while day_kind(day) != "ouvre":
            day = day.replace(day=day.day + 1)
        rules = ("R-O1",) if i == 3 else ()
        formation = "civ. 4e" if i == 3 else ("civ. 1re", "soc.", "crim.")[i % 3]
        fakes.append(
            fake(
                f"r-u{i + 1:05d}",
                "cc",
                formation,
                y,
                day.month,
                day.day,
                f"{(y - 1) % 100:02d}-1{i % 10}.{i:03d}",
                rules=rules,
            )
        )
    fakes.append(fake("r-u00025", "cc", "soc.", 2027, 6, 3, "26-10.025", rules=("R-C3",)))
    partial = fake("r-u00026", "cc", "civ. 1re", 2010, 6, 1, "09-55.555")
    fakes.append(partial)
    for i in range(4):
        fakes.append(fake(f"r-u{27 + i:05d}", "ce", "6e ch.", 2023, 3, 6 + i, f"47100{i}"))

    def pool(jurisdiction, day):
        if day_kind(day) != "ouvre":
            return []
        out = []
        for k, formation in enumerate(("civ. 1re", "soc.", "crim.", "civ. 2e")):
            if jurisdiction == "ce":
                if k:
                    break
                formation = "6e ch."
            for j in range(3):
                if jurisdiction == "cc":
                    number = f"{(day.year - 1) % 100:02d}-{30 + k}.{day.toordinal() % 900 + j:03d}"
                else:
                    number = f"{480000 + day.toordinal() % 9000 + j}"
                out.append(real(jurisdiction, formation, day, number))
        if jurisdiction == "cc" and day == date(2010, 6, 1):
            out.append(real("cc", "civ. 2e", day, "09-55.555", "copie-de-la-fausse"))
        return out

    return fakes, pool, partial


def test_match_reals_follows_fakes():
    fakes, pool, _ = _pool_world()
    pairs, unmatched = match_reals(fakes, pool, seed=0, windows=WINDOWS, corpus_date=CORPUS)
    assert unmatched == [] and len(pairs) == 30
    for pair in pairs:
        f, r = pair.fake, pair.real
        assert r.jurisdiction == f.jurisdiction
        assert year_gap_class(r.jurisdiction, r.day.year, r.number) == year_gap_class(
            f.jurisdiction, f.year, f.number
        )
        if f.future:
            assert r.day.year == pair.notes["year_drawn"] != f.year
            assert r.day.year in {g.year for g in fakes if not g.future and g.jurisdiction == "cc"}
        else:
            assert r.day.year == f.year
            assert day_kind(r.day) == day_kind(f.valid_date)
        if f.formation_exists:
            assert r.formation == f.formation
        else:
            assert r.formation == pair.notes["formation_drawn"] in {"civ. 1re", "soc.", "crim."}
        assert r.day <= CORPUS
    assert len({p.real.raw for p in pairs}) == 30


def test_no_real_shares_a_fake_number():
    fakes, pool, partial = _pool_world()
    pairs, _ = match_reals(fakes, pool, seed=0, windows=WINDOWS, corpus_date=CORPUS)
    fake_numbers = {f.number for f in fakes}
    assert all(not (p.real.numbers & fake_numbers) for p in pairs)
    assert all(p.real.source_id != "copie-de-la-fausse" for p in pairs)
    assert any(c.source_id == "copie-de-la-fausse" for c in pool("cc", date(2010, 6, 1)))
    forbidden = {pool("cc", date(2010, 6, 1))[0].raw}
    again, _ = match_reals(
        fakes, pool, seed=0, windows=WINDOWS, corpus_date=CORPUS, forbidden_raws=forbidden
    )
    assert all(p.real.raw not in forbidden for p in again)


def test_match_reals_reproducible():
    fakes, pool, _ = _pool_world()
    first, _ = match_reals(fakes, pool, seed=0, windows=WINDOWS, corpus_date=CORPUS)
    second, _ = match_reals(
        list(reversed(fakes)), pool, seed=0, windows=WINDOWS, corpus_date=CORPUS
    )
    assert [(p.fake.unit_id, p.real.raw) for p in first] == [
        (p.fake.unit_id, p.real.raw) for p in second
    ]
    other, _ = match_reals(fakes, pool, seed=1, windows=WINDOWS, corpus_date=CORPUS)
    assert [p.real.raw for p in other] != [p.real.raw for p in first]


def test_neighbour_days_and_empty_stratum():
    sunday = fake("r-u00001", "cc", "civ. 1re", 2015, 3, 15, "14-10.001", rules=("R-C4",))
    impossible = fake("r-u00002", "cc", "soc.", 2015, 2, 30, "14-10.002", rules=("R-C1",))
    queried = []

    def pool(jurisdiction, day):
        queried.append(day)
        if day == date(2015, 2, 26):
            return [real("cc", "soc.", day, "14-40.001")]
        return []

    pairs, unmatched = match_reals(
        [sunday, impossible], pool, seed=0, windows=WINDOWS, corpus_date=CORPUS
    )
    assert unmatched == ["r-u00001"]
    sundays = [d for d in queried if d.year == 2015 and d.month <= 4 and d.weekday() == 6]
    assert len([d for d in queried if day_kind(d) == "dimanche_ou_ferie"]) == 15
    assert sundays and all(day_kind(d) != "ouvre" for d in queried[:15])
    (pair,) = pairs
    assert pair.fake.unit_id == "r-u00002" and pair.notes["day_offset"] == -2  # 28 -> 26 février


# --- AC7 : découpage -----------------------------------------------------------------------


def test_split_sizes():
    for n, expected in (
        (300, (20, 140, 140)),
        (100, (20, 0, 80)),
        (120, (20, 50, 50)),
        (301, (20, 140, 141)),
    ):
        out = split_pairs(pairs_of(n), seed=0)
        assert (len(out["session"]), len(out["train"]), len(out["eval"])) == expected
    assert split_sizes(80) == {"session": 20, "train": 0, "eval": 60}
    with pytest.raises(RBuildError) as error:
        split_pairs(pairs_of(79), seed=0)
    assert error.value.code == "too_few_fakes" and error.value.exit_code == 2


def test_split_no_overlap():
    pairs = pairs_of(300)
    out = split_pairs(pairs, seed=0)
    ids = [{p.fake.unit_id for p in members} for members in out.values()]
    assert sum(len(s) for s in ids) == 300 and len(set().union(*ids)) == 300
    raws = [{x for p in members for x in (p.fake.raw, p.real.raw)} for members in out.values()]
    assert not (raws[0] & raws[1]) and not (raws[0] & raws[2]) and not (raws[1] & raws[2])
    # Composition : réservé et entraînement à une paire près par strate.
    from collections import Counter

    from nn_weight_writing.datasets.legal_r.dataset import _stratum

    train = Counter(_stratum(p) for p in out["train"])
    held = Counter(_stratum(p) for p in out["eval"])
    assert all(abs(train[k] - held[k]) <= 1 for k in set(train) | set(held))
    session = Counter(_stratum(p) for p in out["session"])
    assert len(session) >= 4  # la séance couvre les strates, pas seulement la première
    assert split_pairs(pairs, seed=0) == out


def _write_all(tmp_path, n=300):
    out = split_pairs(pairs_of(n), seed=0)
    meta = {
        "extraction_date": "2026-11-07",
        "extraction_dates": {"judilibre": "2026-11-07", "ce-opendata": "2026-11-06"},
    }
    dirs = {}
    for split, members in out.items():
        if members:
            dirs[split] = write_r_dataset(tmp_path / split, members, split=split, meta=meta)
    return out, dirs


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_ids_prefix_and_shuffle(tmp_path):
    _, dirs = _write_all(tmp_path)
    reference_runs = []
    for k in range(20):  # permutations de graine fixée, même composition (S8)
        order = np.random.default_rng([12345, k]).permutation(["real"] * 140 + ["fake"] * 140)
        reference_runs.append(
            max(len(m[0]) for m in re.finditer(r"(r+|f+)", "".join(c[0] for c in order)))
        )
    for split, directory in dirs.items():
        letter = {"session": "s", "train": "t", "eval": "e"}[split]
        examples = _jsonl(directory / "examples.jsonl")
        labels = [r["label"] for r in _jsonl(directory / "labels.jsonl")]
        assert [e["id"] for e in examples] == [
            f"jr-{letter}{i:05d}" for i in range(1, len(labels) + 1)
        ]
        assert all(re.fullmatch(r"jr-[ste]\d{5}", e["id"]) for e in examples)
        assert not any(e["id"].startswith("legal-") for e in examples)
        assert {"real", "fake"} <= set(labels[:4])
        assert labels != sorted(labels) and labels != sorted(labels, reverse=True)
        longest = max(len(m[0]) for m in re.finditer(r"(r+|f+)", "".join(c[0] for c in labels)))
        assert longest <= max(reference_runs)
        assert labels.count("real") == labels.count("fake")


def test_r_dataset_publishable(tmp_path):
    out, dirs = _write_all(tmp_path)
    for split, directory in dirs.items():
        meta = json.loads((directory / "dataset.json").read_text(encoding="utf-8"))
        assert extraction_date(meta) == "2026-11-07"
        comp = meta["composition"]
        assert (comp["task"], comp["split"], comp["encoder"] if "encoder" in comp else None)[
            :2
        ] == ("legal_r", split)
        assert "held_out_types" not in comp
        assert set(meta["files"]) == {"examples.jsonl", "labels.jsonl", "sources.jsonl"}
        assert comp["by_class"] == {"real": len(out[split]), "fake": len(out[split])}
        assert comp["p_R"] == pytest.approx(
            sum(p.fake.type_id != "c00" for p in out[split]) / len(out[split])
        )
        for name in ("examples.jsonl", "labels.jsonl", "sources.jsonl"):
            docs = _jsonl(directory / name)
            assert check_content(name, docs, strict=True) == []
            assert all(len(d.get("raw", "")) <= 160 for d in docs)
        docs = [json.loads((directory / "dataset.json").read_text(encoding="utf-8"))]
        assert check_content("dataset.json", docs, strict=True) == []


def test_sources_follow_condition_3(tmp_path):
    out, dirs = _write_all(tmp_path)
    for split, directory in dirs.items():
        ids = [e["id"] for e in _jsonl(directory / "examples.jsonl")]
        data = (directory / "sources.jsonl").read_bytes()
        assert check_sources("sources.jsonl", data, ids) == []
        sources = {s["id"]: s for s in _jsonl(directory / "sources.jsonl")}
        labels = {r["id"]: r for r in _jsonl(directory / "labels.jsonl")}
        raws = {e["id"]: e["raw"] for e in _jsonl(directory / "examples.jsonl")}
        by_raw = {x.raw: x for p in out[split] for x in (p.fake, p.real)}
        for ident, source in sources.items():
            assert source["class"] == labels[ident]["label"]
            item = by_raw[raws[ident]]
            if source["class"] == "fake":
                assert source["source"] == f"slm:{item.model}" and source["unit_id"] == item.unit_id
                assert labels[ident]["type_id"] == item.type_id
            else:
                assert source["source"] in {"judilibre", "ce-opendata"}
                assert source["origin"] == {"number": item.number}  # S12 : champs d'origine
                assert labels[ident]["type_id"] == "real"
    sources = (dirs["eval"] / "sources.jsonl").read_bytes()
    bad = sources.replace(b'"source": "slm:', b'"source": "judilibre", "x": "', 1)
    assert check_sources("sources.jsonl", bad, None) != []


# --- AC1, AC4, AC9, AC13 : construction par le script --------------------------------------


@pytest.fixture
def built(tmp_path, script, monkeypatch):
    world = World()
    paths = write_world(world, tmp_path)
    monkeypatch.setenv("JUDILIBRE_KEY_ID", "KeyId-fictive-123")
    monkeypatch.setattr(script, "FETCH", world.transport)
    monkeypatch.setattr(script, "CLIENT_KW", {"sleep": lambda s: None})
    return world, paths


def _argv(paths, **over):
    args = {
        "--pre-etude-dir": paths["pre"],
        "--r-gate": paths["gate"],
        "--ce-index": paths["ce"],
        "--ce-index-sha256": paths["ce_sha"],
        "--s-root": paths["s_root"],
        "--repo": paths["repo"],
        "--root": paths["out"],
        "--cache": paths["cache"],
        "--env-file": paths["out"] / "absent.env",
    }
    args.update(over)
    return ["construire", *[str(x) for kv in args.items() for x in kv]]


def _no_dataset(paths) -> bool:
    return (
        not (paths["out"] / "data" / "legal_r").exists() and not (paths["out"] / "heldout").exists()
    )


def test_build_requires_gate_and_matching_classement(built, script, capsys):
    _, paths = built
    assert script.main(_argv(paths, **{"--r-gate": paths["gate"].with_name("absent.toml")})) == 2
    assert "gate_missing" in capsys.readouterr().err and _no_dataset(paths)
    text = paths["gate"].read_text(encoding="utf-8")
    paths["gate"].write_text(
        re.sub(r'classement_sha256 = "\w+"', 'classement_sha256 = "00"', text), encoding="utf-8"
    )
    assert script.main(_argv(paths)) == 2
    assert "gate_mismatch" in capsys.readouterr().err and _no_dataset(paths)
    paths["gate"].write_text(text, encoding="utf-8")
    resume = paths["pre"] / "resume.json"
    resume.rename(resume.with_suffix(".bak"))
    assert script.main(_argv(paths)) == 2
    assert "pre_etude_missing" in capsys.readouterr().err and _no_dataset(paths)
    resume.with_suffix(".bak").rename(resume)
    assert script.main(_argv(paths, **{"--ce-index-sha256": "0" * 64})) == 2
    assert "ce_index_mismatch" in capsys.readouterr().err
    (paths["repo"] / "f.txt").write_text("modifié", encoding="utf-8")
    assert script.main(_argv(paths)) == 2
    assert "dirty_tree" in capsys.readouterr().err and _no_dataset(paths)


def test_build_writes_three_sets_and_reals_match_their_source(built, script):
    world, paths = built
    assert script.main(_argv(paths)) == 0
    out = paths["out"]
    resume = json.loads((out / "data" / "r" / "jeu_r" / "resume.json").read_text("utf-8"))
    excluded = resume["funnel"]["excluded"]
    assert excluded["raw_in_s"] == 1 and excluded["not_in_gate"] == 2
    assert excluded["before_window"] == 1 and excluded["ecli_only"] == 1
    fakes = resume["funnel"]["fakes"]
    assert excluded["no_real_in_stratum"] == 0 and resume["unmatched"] == []
    assert fakes == 120 - 1 + 1 + 16
    sets = {
        "session": out / "data" / "legal_r" / "session",
        "train": out / "data" / "legal_r" / "train",
        "eval": out / "heldout" / "legal_r" / "eval",
    }
    assert {k: v["pairs"] for k, v in resume["splits"].items()} == {
        "session": 20,
        "train": (fakes - 20) // 2,
        "eval": fakes - 20 - (fakes - 20) // 2,
    }
    cache = {}
    for entry in paths["cache"].glob("*.json"):
        for meta in json.loads(entry.read_text(encoding="utf-8"))["results"]:
            cache[meta["id"]] = meta
    ce = {r["Numero_Dossier"]: r for r in CeIndex.load(paths["ce"] / "index.jsonl").records}
    all_raws, all_numbers = [], []
    for directory in sets.values():
        meta = json.loads((directory / "dataset.json").read_text(encoding="utf-8"))
        comp = meta["composition"]
        assert comp["corpus_date"] == comp["extraction_date"] == resume["corpus_date"]
        assert comp["r_gate"]["decision"] == "comparatif" and comp["encoder"] == "legal.chars@1"
        assert comp["visible_types"][-1] == "x01" and len(comp["visible_types"]) == 13
        examples = {e["id"]: e["raw"] for e in _jsonl(directory / "examples.jsonl")}
        for source in _jsonl(directory / "sources.jsonl"):
            raw = examples[source["id"]]
            all_raws.append(raw)
            all_numbers.append(parse_reference(raw).number)
            if source["class"] != "real":
                assert source["source"].startswith("slm:")
                continue
            if source["source"] == "judilibre":
                base = cache[source["source_id"]]
                fields = fields_from_judilibre(base)
                assert source["origin"]["number"] == base["number"]
                assert "text" not in source["origin"]
            else:
                base = ce[source["source_id"]]
                fields = fields_from_ce_opendata(base)
                assert source["origin"]["Numero_Dossier"] == base["Numero_Dossier"]
            ref, expected = reference_of(fields)
            assert raw == expected == format_reference(normalize(fields).to_reference())
            parsed = parse_reference(raw)
            assert (parsed.jurisdiction, parsed.formation, parsed.number) == (
                ref.jurisdiction,
                ref.formation,
                ref.number,
            )
            assert date(parsed.year, parsed.month, parsed.day).isoformat() <= comp["corpus_date"]
        assert (
            check_content("sources.jsonl", _jsonl(directory / "sources.jsonl"), strict=True) == []
        )
    assert len(all_raws) == len(set(all_raws)) == 2 * fakes
    assert len(all_numbers) == len(set(all_numbers))
    assert not set(all_raws) & paths["s_raws"]  # S7, vraies et fausses


def test_build_recheck_existence(built, script, capsys):
    world, paths = built
    world.found_day = world.cc_days[7]
    assert script.main(_argv(paths)) == 0
    resume = json.loads((paths["out"] / "data" / "r" / "jeu_r" / "resume.json").read_text("utf-8"))
    assert resume["funnel"]["excluded"]["found_at_build"] == 1
    assert resume["found_at_build"] == [world.rows[7]["unit_id"]]
    capsys.readouterr()
    world.found_day = None
    world.error_day = world.cc_days[9]
    paths["out"] = paths["out"].with_name("out2")
    paths["cache"] = paths["cache"].with_name("cache2")
    assert script.main(_argv(paths)) == 3
    assert "api_error" in capsys.readouterr().err and _no_dataset(paths)


def test_build_refuses_an_existing_set(built, script, capsys):
    _, paths = built
    target = paths["out"] / "heldout" / "legal_r" / "eval"
    target.mkdir(parents=True)
    (target / "x.txt").write_text("ancien", encoding="utf-8")
    assert script.main(_argv(paths)) == 2
    assert "already_built" in capsys.readouterr().err


# --- S1 : plancher d'indice ----------------------------------------------------------------


def test_floor_accuracies_exact():
    long_fake = [("Cass. civ. 1re, 12 mars 2015, n° 14-10.00" + str(i), "fake") for i in range(10)]
    short_real = [("CE, Sect., 1er mars 2023, n° 47000" + str(i), "real") for i in range(10)]
    result = floor_accuracies(long_fake + short_real, long_fake[:5] + short_real[:5])
    assert result == {"year_gap": 1.0, "raw_length": 1.0}
    same = [(r, "fake") for r, _ in short_real[:5]] + short_real[5:]
    # Indice nul : mêmes valeurs pour les deux classes, tout est prédit `real` (égalité).
    assert floor_accuracies(same, same) == {"year_gap": 0.5, "raw_length": 0.5}
    with pytest.raises(ValueError, match="non vides"):
        floor_accuracies([], short_real)


def test_plancher_command(tmp_path, script):
    out, dirs = _write_all(tmp_path / "w")
    root = tmp_path / "root"
    (root / "data" / "legal_r").mkdir(parents=True)
    (root / "heldout" / "legal_r").mkdir(parents=True)
    dirs["train"].rename(root / "data" / "legal_r" / "train")
    dirs["eval"].rename(root / "heldout" / "legal_r" / "eval")
    assert script.main(["plancher", "--root", str(root)]) == 0
    result = json.loads((root / "data" / "r" / "jeu_r" / "plancher.json").read_text("utf-8"))
    assert 0.0 <= result["year_gap"] <= 1.0 and 0.0 <= result["raw_length"] <= 1.0
    assert script.main(["plancher", "--root", str(tmp_path / "vide")]) == 2


# --- S10 : coût, projection ----------------------------------------------------------------


def test_project_cost(script):
    days = [
        {
            "requests": 1,
            "network": 1,
            "seconds": 0.2,
            "by_chamber": dict.fromkeys(script.COST_CHAMBERS, 1),
        },
        {"requests": 2, "network": 2, "seconds": 0.4, "by_chamber": {"civ. 1re": 3}},
    ]
    p = script.project_cost(days, [1, 1, 1], fakes=300)
    # 1,5 page par jour ; civ. 1re toujours présente (1 jour), les 5 autres une fois sur deux.
    assert p["pages_per_scan_day"] == 1.5
    assert p["expected_days_per_fake"] == pytest.approx((1 + 5 * 2) / 6)
    assert p["requests_per_fake"] == pytest.approx(1.5 * 11 / 6 + 1)
    assert p["requests"] == round(300 * (1.5 * 11 / 6 + 1))
    assert p["seconds_per_request"] == pytest.approx(0.2)
    assert p["minutes"] == round(300 * (1.5 * 11 / 6 + 1) * 0.2 / 60, 1)
    cached = [{**d, "network": 0} for d in days]
    assert script.project_cost(cached, [1, 1, 1])["minutes"] is None


def test_cost_sample_days_are_working_days_in_window(script):
    window = WINDOWS["cc"]
    days = script.sample_days(window, 12, 0)
    assert len(set(days)) == 12 and days == sorted(days)
    assert all(window.start <= d <= window.end and day_kind(d) == "ouvre" for d in days)
    assert days == script.sample_days(window, 12, 0)


def test_ce_days_candidates_from_index():
    index = CeIndex(
        [
            {
                "Numero_Dossier": "447363",
                "Date_Lecture": "2024-10-10",
                "Formation_Jugement": "3ème - 8ème chambres réunies",
                "Date_Mise_Jour": "2024-10-12",
            },
            {"Numero_Dossier": "447364", "Date_Lecture": "2024-10-11", "Formation_Jugement": "?"},
        ]
    )
    days = CeDays(index)
    (cand,) = days.candidates(date(2024, 10, 10))
    assert cand.raw == "CE, 3e et 8e ch. réunies, 10 octobre 2024, n° 447363"
    assert cand.origin["Date_Mise_Jour"] == cand.update_date == "2024-10-12"
    assert days.candidates(date(2024, 10, 11)) == []  # formation illisible : pas en D1


def test_selection_dataclass_defaults():
    assert Selection([], {}).before_window == {}


def test_no_raw_shared_with_s(built, script):
    _, paths = built
    assert script.main(_argv(paths)) == 0
    raws = set()
    for directory in (paths["out"] / "data" / "legal_r").iterdir():
        raws |= {e["raw"] for e in _jsonl(directory / "examples.jsonl")}
    raws |= {e["raw"] for e in _jsonl(paths["out"] / "heldout/legal_r/eval/examples.jsonl")}
    assert raws and not raws & paths["s_raws"]  # ni la fausse ni la vraie présentes dans S
    resume = json.loads((paths["out"] / "data/r/jeu_r/resume.json").read_text("utf-8"))
    assert resume["funnel"]["excluded"]["raw_in_s"] == 1


def test_write_dataset_extra_files(tmp_path):
    from nn_weight_writing.datasets.io import Row, write_dataset

    rows = [Row("a", "x", "real", "real")]
    path = write_dataset(
        tmp_path / "ok",
        rows,
        generator="g",
        version=1,
        seed=0,
        extra_files={"sources.jsonl": b"{}\n"},
    )
    meta = json.loads((path / "dataset.json").read_text("utf-8"))
    assert set(meta["files"]) == {"examples.jsonl", "labels.jsonl", "sources.jsonl"}
    plain = write_dataset(tmp_path / "plain", rows, generator="g", version=1, seed=0)
    assert set(json.loads((plain / "dataset.json").read_text("utf-8"))["files"]) == {
        "examples.jsonl",
        "labels.jsonl",
    }
    for bad in ("labels.jsonl", "dataset.json", "../x.jsonl"):
        target = tmp_path / bad.replace("/", "_").replace(".", "_")
        with pytest.raises(ValueError, match="compagnon refusé"):
            write_dataset(
                target,
                rows,
                generator="g",
                version=1,
                seed=0,
                extra_files={bad: b""},
            )
        assert not target.exists()  # refus avant toute écriture
