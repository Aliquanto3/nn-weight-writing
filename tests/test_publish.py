"""`nnww publish` et `nnww publish --check` (AD-18, R2, R6, décisions Q1-Q5, Q10, Q11, 1-14).

Tous les tests passent un `publish.toml`, un `NOTICE` et un `.env` temporaires, et retirent de
l'environnement les variables de secret : ni la configuration réelle ni le `.env` du dépôt ne
sont lus.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path

import pytest
from artefacts import write_baseline, write_heldout, write_session

from nn_weight_writing.cli import main
from nn_weight_writing.config import load_publish
from nn_weight_writing.publish.checks import (
    LICENCE_URL,
    NOTICE_PHRASE,
    PublishRefusalCode,
    collect_secrets,
    is_secret_name,
    normalize,
    text_pieces,
    unescape,
)

RAW = "Cass. civ. 1re, 12 mai 2021, n° 19-12.345"
ROWS = [
    (RAW, "real", "real"),
    ("CE, 3e ch., 29 février 2022, n° 223387", "fake", "t01"),
    ("court", "fake", "t02"),  # moins de 12 caractères : sauté
]
SECRET = "s3cr3t-valeur-de-test-0123456789"
NOTICE = (
    f"Vraies références : {NOTICE_PHRASE}, Licence Ouverte 2.0 ({LICENCE_URL}), "
    "extraction du 2026-11-08.\n"
)
R_ROWS = [  # id, raw, label, source
    ("r-e001", "Cass. 1re civ., 12 janvier 2022, n° 20-12.345", "real", "judilibre"),
    ("r-e002", "CE, 4 mars 2023, n° 461234", "real", "ce-opendata"),
    ("r-e003", "Cass. soc., 31 février 2021, n° 19-99.999", "fake", "slm:qwen3.5-2b"),
]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Aucune variable de secret héritée ; `.env`, `publish.toml` et `NOTICE` temporaires."""
    for name in list(os.environ):
        if is_secret_name(name):
            monkeypatch.delenv(name, raising=False)
    files = tmp_path / "conf"
    files.mkdir()
    (files / ".env").write_text("", "utf-8")
    (files / "NOTICE").write_text(NOTICE, "utf-8")
    write_config(files, r_republish=True)
    return files


def write_config(files: Path, *, r_republish: object, tasks: str = '["legal_r"]') -> Path:
    value = json.dumps(r_republish) if isinstance(r_republish, bool) else repr(r_republish)
    path = files / "publish.toml"
    path.write_text(f"r_republish = {value}\nr_tasks = {tasks}\n", "utf-8")
    return path


@pytest.fixture
def root(tmp_path):
    """Racine rassemblée : une séance gelée, une séance en erreur, un témoin, un jeu réservé."""
    root = tmp_path / "artefacts"
    write_heldout(root / "heldout", "typed", "eval", ROWS)
    lot = root / "runs" / "1"
    write_session(lot, attempt=1, stamp="20261107T010000Z")
    write_session(lot, attempt=2, stamp="20261107T020000Z", frozen=False)
    write_baseline(lot, n=64, seed=0)
    return root


def publish(root: Path, env: Path, *extra: str) -> int:
    argv = ["publish", "1", "--root", str(root), "--config", str(env / "publish.toml")]
    argv += ["--env-file", str(env / ".env"), "--notice", str(env / "NOTICE"), *extra]
    return main(argv)


def out_dir(root: Path) -> Path:
    return root / "dist" / "lot1"


def session(root: Path, attempt: int = 1) -> Path:
    return next((root / "runs" / "1").glob(f"*-t{attempt}-*"))


def set_detail(run_dir: Path, detail: str) -> None:
    """Écrit `detail` dans l'événement `end` du journal (champ libre, schéma inchangé)."""
    path = run_dir / "journal.jsonl"
    lines = path.read_text("utf-8").splitlines()
    record = json.loads(lines[-1])
    record["detail"] = detail
    lines[-1] = json.dumps(record)
    path.write_text("\n".join(lines) + "\n", "utf-8")


def members(archive: Path) -> dict[str, bytes]:
    with tarfile.open(archive) as tar:
        return {m.name: tar.extractfile(m).read() for m in tar.getmembers()}


def codes(capsys) -> list[str]:
    err = capsys.readouterr().err
    return [
        line.split(" : ")[0].removeprefix("refus ")
        for line in err.splitlines()
        if line.startswith("refus ")
    ]


def write_r(root: Path, rows=R_ROWS, *, sources: bool = True, extraction="2026-11-08", **extra):
    """Jeux `data/legal_r/session` et `heldout/legal_r/eval` au format d'AD-16, plus sources."""
    for base, dataset in (("data", "session"), ("heldout", "eval")):
        directory = root / base / "legal_r" / dataset
        directory.mkdir(parents=True, exist_ok=True)
        examples = [{"id": i, "raw": raw, **extra} for i, raw, _, _ in rows]
        labels = [
            {"id": i, "label": lab, "type_id": "real" if lab == "real" else "t01"}
            for i, _, lab, _ in rows
        ]
        lines = {
            "examples.jsonl": examples,
            "labels.jsonl": labels,
            "sources.jsonl": [{"id": i, "class": lab, "source": s} for i, _, lab, s in rows],
        }
        if not sources:
            del lines["sources.jsonl"]
        for name, items in lines.items():
            text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items)
            (directory / name).write_text(text, "utf-8")
        meta = {"composition": {"task": "legal_r"}}
        if extraction:
            meta["extraction_date"] = extraction
        (directory / "dataset.json").write_text(json.dumps(meta), "utf-8")


# --- les trois refus de `invoke_dev_with` ------------------------------------------------------


def test_publish_refuses_key_pattern(root, env, capsys):
    set_detail(session(root), "clé : sk-or-v1-0123456789abcdef")
    assert publish(root, env) == 1
    assert codes(capsys) == ["key_pattern"]
    assert not out_dir(root).exists()


@pytest.mark.parametrize("pattern", ["sk-ant-api03-x", "Bearer abcdefgh"])
def test_publish_refuses_other_key_patterns(root, env, capsys, pattern):
    (session(root) / "system_prompt.md").write_text(f"exemple : {pattern}\n", "utf-8")
    assert publish(root, env) == 1
    assert codes(capsys) == ["key_pattern"]


def test_publish_refuses_reserved_example(root, env, capsys):
    set_detail(session(root), json.dumps(RAW, ensure_ascii=False))
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "refus reserved_example" in err and "typed/eval/typed-h000" in err
    assert RAW not in err and "12 mai 2021" not in err
    assert not out_dir(root).exists()


def test_publish_refuses_r_artifact_without_r_republish(root, env, capsys):
    write_config(env, r_republish=False)
    write_session(root / "runs" / "1", task="legal_r", stamp="20261107T030000Z")
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    refused = {line.split(" : ")[1] for line in err.splitlines() if "r_without_republish" in line}
    assert refused and all("legal_r-" in name for name in refused)
    assert any(name.endswith("journal.jsonl") for name in refused)
    assert not out_dir(root).exists()


def test_publish_r_witness_and_cross_eval_are_r_artifacts(root, env, capsys):
    write_config(env, r_republish=False)
    write_baseline(root / "runs" / "1", task="legal_r", n=32, seed=1)
    cross = next((root / "runs" / "1" / "train").glob("typed-*")) / "eval-cross-legal_r-eval.json"
    cross.write_text(json.dumps({"target": {"task": "legal_r", "written_task": "typed"}}), "utf-8")
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    refused = sorted(line.split(" : ")[1] for line in err.splitlines() if "r_without_r" in line)
    assert any("legal_r-C-n32-s1/run.json" in name for name in refused)
    assert any(name.endswith("eval-cross-legal_r-eval.json") for name in refused)


def test_r_republish_not_true_boolean_is_false(env):
    for value in ('"true"', "1"):
        (env / "publish.toml").write_text(f'r_republish = {value}\nr_tasks = ["legal_r"]\n')
        assert load_publish(env / "publish.toml").r_republish is False
    (env / "publish.toml").write_text('r_tasks = ["legal_r"]\n')
    assert load_publish(env / "publish.toml").r_republish is False


@pytest.mark.parametrize("tasks", [None, '"legal_r"', '["Legal-R"]', '["../x"]'])
def test_r_tasks_missing_or_invalid_is_config_error(root, env, tasks, capsys):
    text = "r_republish = true\n" + (f"r_tasks = {tasks}\n" if tasks else "")
    (env / "publish.toml").write_text(text, "utf-8")
    with pytest.raises(ValueError, match="r_tasks"):
        load_publish(env / "publish.toml")
    assert publish(root, env) == 2
    assert "r_tasks" in capsys.readouterr().err


def test_real_publish_toml_has_r_tasks():
    config = load_publish()
    assert config.r_republish is True and config.r_tasks == ("legal_r",)


# --- secrets (R6, Q5) ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "JUDILIBRE_KEY_ID",
        "PISTE_CLIENT_ID",
        "PISTE_CLIENT_SECRET",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "HF_TOKEN",
        "SOME_SERVICE_SECRET",
        "OTHER_KEY",
    ],
)
def test_publish_refuses_known_secret_value(root, env, monkeypatch, capsys, name):
    monkeypatch.setenv(name, SECRET)
    set_detail(session(root), f"journalisé : {SECRET}")
    assert publish(root, env) == 1
    captured = capsys.readouterr()
    assert "valeurs de secret contrôlées : 1" in captured.out
    assert f"refus secret_value : runs/1/{session(root).name}/journal.jsonl" in captured.err
    assert f"valeur de la variable {name}" in captured.err


def test_publish_reads_secrets_from_env_file(root, env, capsys):
    (env / ".env").write_text(f'# commentaire\nexport PISTE_CLIENT_SECRET="{SECRET}"\n', "utf-8")
    (session(root) / "system_prompt.md").write_text(SECRET, "utf-8")
    assert publish(root, env) == 1
    captured = capsys.readouterr()
    assert "valeurs de secret contrôlées : 1" in captured.out
    assert "valeur de la variable PISTE_CLIENT_SECRET" in captured.err


def test_publish_finds_json_escaped_secret(root, env, monkeypatch, capsys):
    value = 'abc"déf\\ghi-0123'
    monkeypatch.setenv("ANTHROPIC_API_KEY", value)
    set_detail(session(root), value)  # écrit sous sa forme échappée JSON
    assert value.encode() not in (session(root) / "journal.jsonl").read_bytes()
    assert publish(root, env) == 1
    assert codes(capsys) == ["secret_value"]


def test_publish_refusal_never_prints_secret(root, env, monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", SECRET)
    set_detail(session(root), SECRET)
    assert publish(root, env, "--dry-run") == 1
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    assert SECRET[:8] not in captured.out + captured.err


def test_publish_ignores_short_or_unset_secret(root, env, monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1234567")  # 7 caractères
    monkeypatch.setenv("NOT_A_SECRET_NAME", SECRET)  # nom hors liste
    set_detail(session(root), f"1234567 {SECRET}")
    assert publish(root, env) == 0
    captured = capsys.readouterr()
    assert "valeurs de secret contrôlées : 0" in captured.out
    assert "avertissement : aucune valeur de secret à contrôler" in captured.err


def test_collect_secrets_counts_each_value_once(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(f"PISTE_CLIENT_ID={SECRET}\nOTHER=x\n", "utf-8")
    secrets = collect_secrets({"JUDILIBRE_KEY_ID": SECRET, "A_TOKEN": "y" * 8}, [env_file])
    assert secrets.count == 2
    assert [name for name, _ in secrets.values] == ["JUDILIBRE_KEY_ID", "A_TOKEN"]
    assert collect_secrets({}, []).count == 0


# --- réservé (AD-19, Q4) ------------------------------------------------------------------------


def test_publish_skips_raws_under_12_chars(root, env, capsys):
    set_detail(session(root), json.dumps("court"))
    assert publish(root, env) == 0
    assert "raw réservés contrôlés : 2 ; sautés (moins de 12 caractères) : 1" in (
        capsys.readouterr().out
    )


@pytest.mark.parametrize(
    "detail",
    [
        json.dumps(json.dumps({"raw": RAW})),  # double échappement JSON
        ascii(RAW),  # littéral Python : n°
        ascii(f"print('{RAW}')"),  # littéral Python dans du code
        RAW.replace(", n°", ",\n  n°"),  # retour à la ligne et espaces
        RAW.upper(),  # casse
        json.dumps(RAW),  # ensure_ascii : n°
    ],
)
def test_reserved_search_is_normalized(root, env, capsys, detail):
    set_detail(session(root), detail)
    assert publish(root, env) == 1
    assert codes(capsys) == ["reserved_example"]


def test_reserved_search_needs_the_whole_raw(root, env, capsys):
    set_detail(session(root), RAW[:-1] + "6")
    assert publish(root, env) == 0


def test_normalize_and_unescape():
    assert normalize("  A\n\tB  ") == " a b "
    assert unescape(r"n° \"x\" \'y\' \\n") == "n° \"x\" 'y' \\n"
    pieces = text_pieces("", [{"k": json.dumps({"raw": "a\\nb"})}])
    assert "a\nb" in pieces


def test_publish_refuses_no_heldout(root, env, capsys):
    for path in sorted((root / "heldout").rglob("*"), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    assert publish(root, env) == 1
    assert codes(capsys) == ["no_heldout"]


# --- contenu, chemins, reproductibilité ---------------------------------------------------------


def test_publish_excludes_bundle_and_lot_files(root, env, capsys):
    lot = root / "runs" / "1"
    (session(root) / "bundle").mkdir()
    (session(root) / "bundle" / "examples.jsonl").write_text("{}\n", "utf-8")
    (lot / "courbe-c-f.jsonl").write_text("{}\n", "utf-8")
    (lot / "reentrainement.jsonl").write_text("{}\n", "utf-8")
    (session(root) / "notes.txt").write_text("x", "utf-8")
    assert publish(root, env, "--dry-run") == 0
    out = capsys.readouterr().out
    for name in ("bundle/examples.jsonl", "courbe-c-f.jsonl", "reentrainement.jsonl", "notes.txt"):
        assert any(
            line.startswith("ignoré : ") and line.endswith(name) for line in out.splitlines()
        )
    assert "séances : 2 ; témoins : 1 ; membres : 7" in out
    assert publish(root, env) == 0
    names = set(members(out_dir(root) / "runs-lot1.tar.gz"))
    s1, s2 = session(root, 1).name, session(root, 2).name
    witness = next((lot / "train").iterdir()).name
    assert names == {
        "runs/1/SHA256SUMS",
        f"runs/1/{s1}/journal.jsonl",
        f"runs/1/{s1}/frozen/manifest.json",
        f"runs/1/{s1}/frozen/weights.npz",
        f"runs/1/{s2}/journal.jsonl",
        f"runs/1/train/{witness}/run.json",
        f"runs/1/train/{witness}/frozen/manifest.json",
        f"runs/1/train/{witness}/frozen/weights.npz",
    }


def test_publish_includes_prompt_and_evals(root, env):
    run_dir = session(root)
    (run_dir / "system_prompt.md").write_text("consigne\n", "utf-8")
    (run_dir / "eval.json").write_text("{}", "utf-8")
    (run_dir / "eval-cross-other-eval.json").write_text("{}", "utf-8")
    assert publish(root, env) == 0
    names = set(members(out_dir(root) / "runs-lot1.tar.gz"))
    for name in ("system_prompt.md", "eval.json", "eval-cross-other-eval.json"):
        assert f"runs/1/{run_dir.name}/{name}" in names


def test_publish_archive_is_byte_reproducible(root, env, tmp_path):
    assert publish(root, env, "--out", str(tmp_path / "a")) == 0
    for path in root.rglob("*"):
        os.utime(path, (1_000_000, 1_000_000))
    assert publish(root, env, "--out", str(tmp_path / "b")) == 0
    first = (tmp_path / "a" / "runs-lot1.tar.gz").read_bytes()
    assert first == (tmp_path / "b" / "runs-lot1.tar.gz").read_bytes()
    with tarfile.open(fileobj=io.BytesIO(first)) as tar:
        infos = tar.getmembers()
    assert [m.name for m in infos] == sorted(m.name for m in infos)
    assert {(m.mtime, m.uid, m.gid, m.uname, m.gname, m.mode) for m in infos} == {
        (0, 0, 0, "", "", 0o644)
    }
    assert first[4:8] == b"\x00\x00\x00\x00"  # mtime gzip nul


def test_publish_sha256sums_match_members(root, env):
    assert publish(root, env) == 0
    content = members(out_dir(root) / "runs-lot1.tar.gz")
    sums = content.pop("runs/1/SHA256SUMS").decode().splitlines()
    assert sums == [f"{hashlib.sha256(d).hexdigest()}  {n}" for n, d in sorted(content.items())]
    outer = (out_dir(root) / "SHA256SUMS").read_text("utf-8").splitlines()
    digest = hashlib.sha256((out_dir(root) / "runs-lot1.tar.gz").read_bytes()).hexdigest()
    assert outer == [f"{digest}  runs-lot1.tar.gz"]


def test_publish_refuses_existing_output(root, env, capsys):
    out_dir(root).mkdir(parents=True)
    (out_dir(root) / "runs-lot1.tar.gz").write_bytes(b"ancien")
    assert publish(root, env) == 1
    assert codes(capsys) == ["output_exists"]
    assert (out_dir(root) / "runs-lot1.tar.gz").read_bytes() == b"ancien"
    assert not (out_dir(root) / "SHA256SUMS").exists()


def test_publish_dry_run_writes_nothing(root, env, capsys):
    before = sorted(p.relative_to(root) for p in root.rglob("*"))
    assert publish(root, env, "--dry-run") == 0
    assert sorted(p.relative_to(root) for p in root.rglob("*")) == before
    out = capsys.readouterr().out
    assert "à blanc : aucun refus, rien n'est écrit" in out
    assert "archive de R : non construite : aucun jeu de r_tasks sous data/ ni heldout/" in out


def test_publish_checks_everything_before_writing(root, env, capsys):
    set_detail(session(root), "sk-ant-x " + json.dumps(RAW))
    (out_dir(root)).mkdir(parents=True)
    (out_dir(root) / "SHA256SUMS").write_text("", "utf-8")
    assert publish(root, env) == 1
    assert sorted(codes(capsys)) == ["key_pattern", "output_exists", "reserved_example"]
    assert sorted(p.name for p in out_dir(root).iterdir()) == ["SHA256SUMS"]


@pytest.mark.parametrize("directory", ["interne", "collecte", "cache"])
def test_publish_refuses_forbidden_paths(root, env, capsys, directory):
    path = session(root) / "frozen" / directory / "x.json"
    path.parent.mkdir()
    path.write_text("{}", "utf-8")
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert f"refus forbidden_path : runs/1/{session(root).name}/frozen/{directory}/x.json" in err


def test_publish_check_refuses_raw_collection(env, root, capsys):
    collected = root / "data" / "r" / "collecte.jsonl"
    inner = root / "data" / "r" / "collecte" / "x.jsonl"
    classement = root / "data" / "r" / "pre_etude" / "classement.jsonl"
    for path in (collected, inner, classement):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", "utf-8")
    argv = ["publish", "--check", str(collected), str(inner), str(classement)]
    argv += ["--root", str(root), "--config", str(env / "publish.toml")]
    assert main([*argv, "--env-file", str(env / ".env")]) == 1
    err = capsys.readouterr().err
    assert (
        "refus forbidden_path : data/r/collecte.jsonl : chemin non publié (collecte.jsonl)" in err
    )
    assert "refus forbidden_path : data/r/collecte/x.jsonl : chemin non publié (collecte)" in err
    assert "classement.jsonl" not in err  # classement de 1-12 : publiable (D8)


def test_text_content_blocks_allowed_but_bare_text_refused(root, env, capsys):
    block = json.dumps({"content": [{"type": "text", "text": "réponse de l'agent"}]})
    set_detail(session(root), block)  # chaîne : pas un objet du journal
    notes = session(root) / "frozen" / "notes.json"
    notes.write_text(json.dumps({"content": [{"type": "text", "text": "ok"}]}), "utf-8")
    assert publish(root, env) == 0
    notes.write_text(json.dumps({"decision": {"text": "texte intégral", "zones": {}}}), "utf-8")
    for path in out_dir(root).iterdir():
        path.unlink()
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "refus r_forbidden_field : " in err and "clé text" in err and "clé zones" in err


@pytest.mark.parametrize(
    "raw,label",
    [
        ("Cass. civ., Dupont c/ Martin, 2021", "c/"),
        ("Affaire X contre Y, CE 2020", "contre"),
        ("Cass., M. Durand, 12 mai 2021", "M."),
        ("CA Paris, Mme Durand, 2021", "Mme"),
        ("Cass. com., Société Générale, 2021", "société"),
    ],
)
def test_publish_refuses_party_names_in_any_archive(root, env, capsys, raw, label):
    notes = session(root) / "frozen" / "notes.json"
    notes.write_text(json.dumps([{"id": "x1", "raw": raw}]), "utf-8")
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert f"refus r_party_name : runs/1/{session(root).name}/frozen/notes.json" in err
    assert f"« {label} »" in err and raw not in err


def test_publish_refuses_long_raw(root, env, capsys):
    notes = session(root) / "frozen" / "notes.jsonl"
    notes.write_text(json.dumps({"id": "x1", "raw": "a" * 161}) + "\n", "utf-8")
    assert publish(root, env) == 1
    assert "raw de 161 caractères (> 160), id x1" in capsys.readouterr().err
    notes.write_text(json.dumps({"id": "x1", "raw": "a" * 160}) + "\n", "utf-8")
    assert publish(root, env) == 0


# --- archive de R (R2, conditions 1 à 3, Q1, Q10) ---------------------------------------------


def test_publish_r_accepted_with_r_republish(root, env, capsys):
    write_r(root)
    write_session(root / "runs" / "1", task="legal_r", stamp="20261107T030000Z")
    assert publish(root, env) == 0
    out = capsys.readouterr().out
    assert "archive de R : construite (2 jeux)" in out
    content = members(out_dir(root) / "r-lot1.tar.gz")
    expected = {
        f"{base}/legal_r/{dataset}/{name}"
        for base, dataset in (("data", "session"), ("heldout", "eval"))
        for name in ("examples.jsonl", "labels.jsonl", "dataset.json", "sources.jsonl")
    }
    assert set(content) == expected | {"SHA256SUMS"}
    sums = content.pop("SHA256SUMS").decode().splitlines()
    assert sums == [f"{hashlib.sha256(d).hexdigest()}  {n}" for n, d in sorted(content.items())]
    outer = (out_dir(root) / "SHA256SUMS").read_text("utf-8").splitlines()
    assert [line.split("  ")[1] for line in outer] == ["r-lot1.tar.gz", "runs-lot1.tar.gz"]
    assert any("legal_r-" in n for n in members(out_dir(root) / "runs-lot1.tar.gz"))


def test_publish_r_archive_not_built_without_r_republish(root, env, capsys):
    write_config(env, r_republish=False)
    write_r(root)
    assert publish(root, env) == 0
    assert "archive de R : non construite : r_republish n'est pas true" in capsys.readouterr().out
    assert not (out_dir(root) / "r-lot1.tar.gz").exists()


@pytest.mark.parametrize("key", ["text", "zones", "text_highlight"])
def test_publish_r_dataset_refuses_forbidden_fields(root, env, capsys, key):
    write_r(root, **{key: {"type": "text"} if key == "zones" else "texte"})
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert f"refus r_forbidden_field : data/legal_r/session/examples.jsonl : clé {key}" in err
    assert not out_dir(root).exists()


def test_publish_r_dataset_refuses_content_block_text(root, env, capsys):
    write_r(root, type="text", text="x")  # dans R, même la forme de bloc est refusée
    assert publish(root, env) == 1
    assert "clé text" in capsys.readouterr().err


@pytest.mark.parametrize(
    "rows,detail",
    [
        ([("r-e1", "Cass. soc., 31 février 2021, n° 1", "fake", "judilibre")], "fausse attribuée"),
        ([("r-e1", "Cass. soc., 31 février 2021, n° 1", "fake", "jade")], "fausse attribuée"),
        ([("r-e1", "Cass. soc., 3 février 2021, n° 1", "real", "slm:qwen")], "vraie attribuée"),
        ([("r-e1", "Cass. soc., 3 février 2021, n° 1", "maybe", "judilibre")], "hors real"),
        ([("r-e1", "Cass. soc., 3 février 2021, n° 1", "real", "wikipedia")], "inconnue"),
        ([("r-e1", "Cass. soc., 3 février 2021, n° 1", "fake", "slm:")], "inconnue"),
    ],
)
def test_publish_r_dataset_refuses_fake_attributed_to_public_base(root, env, capsys, rows, detail):
    write_r(root, rows)
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "refus r_source_mismatch : heldout/legal_r/eval/sources.jsonl" in err and detail in err


def test_publish_r_dataset_requires_sources_with_same_ids(root, env, capsys):
    write_r(root, sources=False)
    assert publish(root, env) == 1
    assert "sources.jsonl absent" in capsys.readouterr().err
    write_r(root)
    path = root / "heldout" / "legal_r" / "eval" / "sources.jsonl"
    path.write_text(path.read_text("utf-8").splitlines()[0] + "\n", "utf-8")
    assert publish(root, env) == 1
    assert "id différents d'examples.jsonl (2 absents, 0 en trop)" in capsys.readouterr().err


@pytest.mark.parametrize(
    "notice,detail",
    [
        (None, "fichier absent"),
        (NOTICE.replace(NOTICE_PHRASE, "Judilibre"), NOTICE_PHRASE),
        (NOTICE.replace(LICENCE_URL, "etalab"), "URL de la licence"),
        (NOTICE.replace("extraction du 2026-11-08", "extraite"), "extraction du AAAA-MM-JJ"),
        (NOTICE.replace("2026-11-08", "2026-11-01"), "date d'extraction 2026-11-08"),
    ],
)
def test_publish_r_dataset_requires_notice_attribution(root, env, capsys, notice, detail):
    write_r(root)
    if notice is None:
        (env / "NOTICE").unlink()
    else:
        (env / "NOTICE").write_text(notice, "utf-8")
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "refus r_attribution_missing" in err and detail in err


def test_publish_r_dataset_requires_extraction_date(root, env, capsys):
    write_r(root, extraction=None)
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "refus r_attribution_missing : data/legal_r/session/dataset.json" in err
    assert "dataset.json sans extraction_date" in err


def test_publish_r_archive_publishes_its_reserved_raws(root, env):
    """R2 : l'archive de R contient son réservé ; `reserved_example` ne la contrôle pas."""
    write_r(root)
    assert publish(root, env) == 0
    content = members(out_dir(root) / "r-lot1.tar.gz")
    assert R_ROWS[0][1].encode() in content["heldout/legal_r/eval/examples.jsonl"]


# --- `nnww publish --check` et `nnww table` (Q3) ----------------------------------------------


def check(env: Path, root: Path, *paths: Path) -> int:
    argv = ["publish", "--check", *map(str, paths), "--root", str(root)]
    return main(argv + ["--config", str(env / "publish.toml"), "--env-file", str(env / ".env")])


def test_publish_check_paths(root, env, tmp_path, capsys):
    clean = tmp_path / "lot1.md"
    clean.write_text("| typed | 4/6 |\n", "utf-8")
    assert check(env, root, clean) == 0
    assert "fichiers contrôlés : 1" in capsys.readouterr().out
    dirty = tmp_path / "rapport.md"
    dirty.write_text(f"Exemple cité : « {RAW} ».\n", "utf-8")
    assert check(env, root, clean, dirty) == 1
    assert codes(capsys) == ["reserved_example"]
    assert check(env, root, tmp_path / "absent.md") == 2


def test_publish_check_refuses_r_mention_without_r_republish(root, env, tmp_path, capsys):
    write_config(env, r_republish=False)
    path = tmp_path / "lot1.json"
    path.write_text(json.dumps({"task": "legal_r"}), "utf-8")
    other = tmp_path / "lot1.md"
    other.write_text("legal_s_reserved et legal_rx\n", "utf-8")
    assert check(env, root, path, other) == 1
    err = capsys.readouterr().err
    assert "refus r_without_republish : " in err and "lot1.md" not in err


def test_publish_check_and_lot_are_exclusive(root, env, tmp_path):
    path = tmp_path / "a.md"
    path.write_text("x", "utf-8")
    assert main(["publish", "1", "--check", str(path)]) == 2
    assert main(["publish", "--root", str(root)]) == 2


def test_table_fails_when_check_refuses(root, env, tmp_path, capsys, monkeypatch):
    from artefacts import typed_spec

    from nn_weight_writing.tasks.registry import TASKS

    monkeypatch.setitem(TASKS, "typed", typed_spec())
    out = tmp_path / "mesures"
    out.mkdir()
    argv = ["table", "--lot", "1", "--root", str(root), "--out", str(out)]
    argv += ["--config", str(env / "publish.toml"), "--env-file", str(env / ".env")]
    assert main(argv) == 0
    assert "fichiers contrôlés : 2" in capsys.readouterr().out
    (out / "decisions-lot1.toml").write_text(f'# note : "{RAW}"\n', "utf-8")
    assert main(argv) == 1
    err = capsys.readouterr().err
    assert "refus reserved_example : " in err and "decisions-lot1.toml" in err


def test_report_and_publish_follow_dependency_graph():
    """`report/` et `publish/` n'importent ni session, ni providers, ni sandbox, ni baselines,
    ni torch ; `publish/` n'importe que `journal`, `evaluation.schema` et lui-même."""
    package = Path(__file__).resolve().parents[1] / "src" / "nn_weight_writing"
    forbidden = ("session", "providers", "sandbox", "baselines", "torch")
    allowed = {
        "report": ("journal", "budget", "config", "report", "evaluation.schema"),
        "publish": ("journal", "publish", "evaluation.schema"),
    }
    for name, prefixes in allowed.items():
        for path in (package / name).glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text("utf-8"))):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for module in names:
                    assert module.split(".")[0] not in forbidden, (path.name, module)
                    if module.startswith("nn_weight_writing."):
                        sub = module.removeprefix("nn_weight_writing.")
                        assert sub.startswith(prefixes), (path.name, module)


def test_refusal_codes_are_the_spec_ones():
    assert {c.value for c in PublishRefusalCode} == {
        "key_pattern",
        "secret_value",
        "reserved_example",
        "no_heldout",
        "r_without_republish",
        "r_forbidden_field",
        "r_source_mismatch",
        "r_attribution_missing",
        "output_exists",
        "r_party_name",
        "r_raw_too_long",
        "forbidden_path",
        "uncheckable",
    }


# --- revue, passe 2 : membres illisibles, suffixes, encodages, liens ------------------------------


def test_publish_checks_json_inside_text_blocks(root, env, capsys):
    tool_result = json.dumps({"id": "x1", "raw": "a" * 161, "zones": {}})
    set_detail(session(root), json.dumps({"content": [{"type": "text", "text": tool_result}]}))
    assert publish(root, env) == 1
    assert sorted(codes(capsys)) == ["r_forbidden_field", "r_raw_too_long"]


def test_publish_refuses_unreadable_json_line_but_checks_the_others(root, env, capsys):
    notes = session(root) / "frozen" / "notes.jsonl"
    notes.write_text("pas du json\n" + json.dumps({"id": "x1", "raw": "a" * 161}) + "\n", "utf-8")
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "refus uncheckable : " in err and "JSON illisible (ligne 1)" in err
    assert "refus r_raw_too_long : " in err


def test_publish_accepts_blank_lines_and_unicode_separators_in_jsonl(root, env):
    # `json.dumps(ensure_ascii=False)` laisse U+2028 et U+0085 bruts : pas des fins de ligne JSONL.
    line = json.dumps({"id": "x1", "note": "a\u2028b\x85c"}, ensure_ascii=False)
    notes = session(root) / "frozen" / "notes.jsonl"
    notes.write_text(line + "\n\n   \n", "utf-8")
    assert publish(root, env) == 0


def test_publish_accepts_utf8_bom(root, env):
    notes = session(root) / "frozen" / "notes.json"
    notes.write_bytes(b"\xef\xbb\xbf" + json.dumps({"ok": 1}).encode())
    assert publish(root, env) == 0


@pytest.mark.parametrize("name", ["notes.log", "notes.yaml", "NOTES", "page.html"])
def test_publish_checks_any_text_suffix(root, env, capsys, name):
    (session(root) / "frozen" / name).write_text(f"cité : {RAW}\n", "utf-8")
    assert publish(root, env) == 1
    assert codes(capsys) == ["reserved_example"]


def test_publish_refuses_unknown_binary_and_text_arrays(root, env, capsys):
    import gzip

    import numpy as np

    frozen = session(root) / "frozen"
    (frozen / "notes.gz").write_bytes(gzip.compress(RAW.encode()))
    buffer = io.BytesIO()
    np.savez_compressed(buffer, w=np.zeros(2), names=np.array([RAW]))
    (frozen / "extra.npz").write_bytes(buffer.getvalue())
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "notes.gz : ni texte" in err and "tableau names.npy non numérique" in err


def test_publish_finds_reserved_in_utf16_and_with_zero_width(root, env, capsys):
    (session(root) / "frozen" / "a.txt").write_bytes(RAW.encode("utf-16"))
    (session(root) / "frozen" / "b.md").write_text(RAW[:5] + "​" + RAW[5:], "utf-8")
    assert publish(root, env) == 1
    assert codes(capsys) == ["reserved_example", "reserved_example"]


def test_publish_refuses_symlink(root, env, capsys, tmp_path):
    target = tmp_path / "secret.txt"
    target.write_text("x", "utf-8")
    try:
        (session(root) / "frozen" / "lien.txt").symlink_to(target)
    except OSError:
        pytest.skip("liens symboliques indisponibles")
    assert publish(root, env) == 1
    assert "lien symbolique" in capsys.readouterr().err


def test_session_task_is_read_from_first_open_event(tmp_path):
    from nn_weight_writing.publish.archive import _session_task

    journal = tmp_path / "journal.jsonl"
    lines = [{"type": "note"}, {"type": "open", "task": "legal_r"}]
    journal.write_text("".join(json.dumps(x) + "\n" for x in lines), "utf-8")
    assert _session_task(journal) == "legal_r"


def test_r_source_mismatch_never_prints_source_value(root, env, capsys):
    write_r(root, rows=[("r-e1", "Cass. soc., 3 février 2021, n° 1", "real", SECRET)])
    assert publish(root, env) == 1
    err = capsys.readouterr().err
    assert "source inconnue" in err and SECRET not in err


def test_r_examples_non_object_line_is_a_mismatch(root, env, capsys):
    write_r(root)
    examples = root / "data" / "legal_r" / "session" / "examples.jsonl"
    examples.write_text(examples.read_text("utf-8") + "[1, 2]\n", "utf-8")
    assert publish(root, env) == 1
    assert "id différents d'examples.jsonl" in capsys.readouterr().err


def test_table_refused_leaves_nothing_in_out(root, env, tmp_path, capsys, monkeypatch):
    from artefacts import typed_spec

    from nn_weight_writing.tasks.registry import TASKS

    monkeypatch.setitem(TASKS, "typed", typed_spec())
    out = tmp_path / "mesures"
    out.mkdir()
    (out / "decisions-lot1.toml").write_text(f'# note : "{RAW}"\n', "utf-8")
    argv = ["table", "--lot", "1", "--root", str(root), "--out", str(out)]
    argv += ["--config", str(env / "publish.toml"), "--env-file", str(env / ".env")]
    assert main(argv) == 1
    assert sorted(p.name for p in out.iterdir()) == ["decisions-lot1.toml"]
