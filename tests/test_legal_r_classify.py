"""Classes, classement publié et commandes de la phase B (story 1-12, D6, D7, P1, P8, P9).

Collecte factice, réponses Judilibre enregistrées et index CE de fixtures : aucun accès réseau.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import date
from pathlib import Path

import pytest
from legal_r_support import (
    EMPTY_SCAN,
    EMPTY_SEARCH,
    KEY,
    FakeTransport,
    ce_archive,
    ok,
)
from test_legal_r_frozen import line, write_collection

from nn_weight_writing.datasets.legal_r.ce_index import CeIndex, parse_archive
from nn_weight_writing.datasets.legal_r.classify import (
    CLASSEMENT_FIELDS,
    Unit,
    build_units,
    citation_from,
    classement_row,
    classify_unit,
    read_classement,
    write_classement,
    write_extraction,
)
from nn_weight_writing.datasets.legal_r.existence import Verification
from nn_weight_writing.datasets.legal_r.extract import extract_references
from nn_weight_writing.datasets.legal_r.normalize import fields_from_extracted, normalize
from nn_weight_writing.datasets.legal_r.r_facts import RFacts
from nn_weight_writing.tasks.legal.facts import load_facts

SCRIPT = Path(__file__).parents[1] / "scripts" / "pre_etude_r.py"
FACTS = load_facts()
RELIABLE = RFacts(recall_reliable={"cc": True, "ce": True})
GEN = date(2026, 11, 7)
MODELS = ("qwen3.5:0.8b", "qwen3.5:2b", "gemma4:e2b-it-qat")


def load_script():
    spec = importlib.util.spec_from_file_location("pre_etude_r", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def citations(text, model="qwen3.5:2b", request_id="cass-001-directe"):
    return [
        citation_from(
            ext,
            normalize(fields_from_extracted(ext)),
            model=model,
            digest="sha256:" + "b" * 64,
            request_id=request_id,
            generation_date=GEN,
        )
        for ext in extract_references(text)
    ]


def one_unit(text) -> Unit:
    (unit,) = build_units(citations(text), MODELS)
    return unit


def classify(text, status="absent", r_facts=RELIABLE, **extra):
    unit = one_unit(text)
    return classify_unit(
        unit,
        facts=FACTS,
        r_facts=r_facts,
        verify=lambda ref: Verification(status, **extra),
    )


def test_class_order():
    assert classify("TA de Paris, 3 mai 2019, n° 1912345").klass == "out_of_scope"
    assert classify("CA Lyon, 12 mars 2015, n° 13/04567").klass == "out_of_scope"  # P5
    partial = classify("Cass. civ. 1re, 12 mars 2015")
    assert (partial.klass, partial.verification) == ("partial", None)  # AC7
    partial_bad = classify("Cass. civ. 1re, 30 février 2015")
    assert (partial_bad.klass, partial_bad.rules) == ("partial", {"R-C1"})  # P3
    found = classify("Cass. civ. 4e, 12 mars 2015, n° 13-27.123", "exists", found_id="x")
    assert (found.klass, found.grid_false_positive, found.rules) == ("exists", True, {"R-O1"})
    real = classify("Cass. soc., 12 mars 2015, n° 13-27.123", "exists")
    assert (real.klass, real.grid_false_positive) == ("exists", False)
    incoherent = classify("Cass. civ. 4e, 12 mars 2015, n° 13-27.123", "absent")
    assert incoherent.klass == "incoherent"
    outside = classify(
        "Cass. civ. 4e, 12 mars 1985, n° 13-27.123", "unverifiable", reason="before_window"
    )
    assert outside.klass == "unverifiable"  # R-O1 hors domaine F avant 2001
    coherent = classify("Cass. soc., 12 mars 2015, n° 13-27.123", "absent", partial_match="date")
    assert (coherent.klass, coherent.partial_match) == ("coherent_absent", "date")
    formation = classify(
        "Cass. soc., 12 mars 2015, n° 13-27.123", "absent", partial_match="formation"
    )
    assert (formation.klass, formation.partial_match) == ("coherent_absent", "formation")
    error = classify("Cass. soc., 12 mars 2015, n° 13-27.123", "unverifiable", reason="api_error")
    assert (error.klass, error.unverifiable_reason) == ("unverifiable", "api_error")
    unreliable = RFacts(recall_reliable={"cc": False, "ce": True})
    weak = classify("Cass. soc., 12 mars 2015, n° 13-27.123", "absent", r_facts=unreliable)
    assert (weak.klass, weak.unverifiable_reason) == ("unverifiable", "verification_unreliable")
    weak_incoherent = classify("Cass. civ. 4e, 12 mars 2015, n° 13-27.123", r_facts=unreliable)
    assert weak_incoherent.klass == "incoherent"


def test_dedup_and_canonical_citation():
    text = (
        "Cass. soc., 12 mars 2015, n° 13-27.123 ; et encore Cass. soc., 12 mars 2015, n° 13-27123"
    )
    cits = (
        citations(text, model="gemma4:e2b-it-qat", request_id="cass-002")
        + citations("Cass. soc., 12/03/2015, n° 13 27.123", model="qwen3.5:2b", request_id="b")
        + citations("Cass. soc., 12 mars 2015, n° 13-27.123", model="qwen3.5:2b", request_id="a")
        + citations("CE, 5e ch., 12 mars 2019, n° 412345", model="qwen3.5:0.8b")
    )
    units = build_units(cits, MODELS)
    assert [u.unit_id for u in units] == ["r-u00001", "r-u00002"]
    cc = units[0]
    assert cc.key == ("cc", "13-27.123", (2015, 3, 12))
    # Deux fois dans une réponse : une citation ; ordre MODELES, puis request_id, puis start.
    assert [(c.model, c.request_id) for c in cc.citations] == [
        ("qwen3.5:2b", "a"),
        ("qwen3.5:2b", "b"),
        ("gemma4:e2b-it-qat", "cass-002"),
    ]
    assert units[1].key[0] == "ce"


def test_class_conflict_counted():
    cits = citations("Cass. civ. 4e, 12 mars 2015, n° 13-27.123", model="gemma4:e2b-it-qat")
    cits += citations("Cass. soc., 12 mars 2015, n° 13-27.123", model="qwen3.5:2b")
    (unit,) = build_units(cits, MODELS)
    classify_unit(unit, facts=FACTS, r_facts=RELIABLE, verify=lambda r: Verification("absent"))
    # La citation canonique (qwen3.5:2b, cohérente) fixe la classe ; le conflit est compté.
    assert (unit.klass, unit.class_conflict, unit.ref.formation) == (
        "coherent_absent",
        True,
        "soc.",
    )


def test_classement_fields(tmp_path):
    units = build_units(
        citations("l'arrêt Perruche (Cass. ass. plén., 17 novembre 2000, n° 99-13.701)")
        + citations("Dupont c/ Martin, Cass. civ. 1re, 12 mars 2015", model="qwen3.5:0.8b"),
        MODELS,
    )
    for unit in units:
        classify_unit(unit, facts=FACTS, r_facts=RELIABLE, verify=lambda r: Verification("exists"))
    versions = {
        "normalizer": "legal_r.normalize@1",
        "grid": 1,
        "r_facts_sha256": "r",
        "facts_sha256": "f",
    }
    write_classement(tmp_path / "classement.jsonl", units, versions)
    write_extraction(tmp_path / "interne" / "extraction.jsonl", units)
    rows = read_classement(tmp_path / "classement.jsonl")
    assert [r["unit_id"] for r in rows] == ["r-u00001", "r-u00002"]
    for row in rows:
        assert tuple(row) == CLASSEMENT_FIELDS
        assert row["source"] == "slm" and row["schema"] == 1 and row["versions"] == versions
    perruche = rows[1]
    assert perruche["canonical"] == "Cass. ass. plén., 17 novembre 2000, n° 99-13.701"
    assert perruche["citations"] == [
        {"model": "qwen3.5:2b", "digest": "sha256:bbbbb", "request_id": "cass-001-directe"}
    ]
    published = (tmp_path / "classement.jsonl").read_text(encoding="utf-8")
    for leaked in ("Perruche", "Dupont", "Martin", "raw", "arrêt"):
        assert leaked not in published
    internal = [
        json.loads(x)
        for x in (tmp_path / "interne" / "extraction.jsonl").open("r", encoding="utf-8")
    ]
    assert {r["unit_id"] for r in internal} == {"r-u00001", "r-u00002"}
    assert all("raw" in r for r in internal)


def test_samples_reproducible():
    script = load_script()
    rows = [
        {
            "unit_id": f"r-u{i:05d}",
            "class": cls,
            "grid_false_positive": i == 3,
            "partial_match": "formation" if i == 7 else None,
        }
        for i, cls in enumerate(["incoherent", "coherent_absent"] * 50 + ["partial"] * 30, 1)
    ]
    responses = [f"m|q{i:03d}" for i in range(100)]
    with_refs = set(responses[:60])
    first = script.samples_for(rows, responses, with_refs, 0)
    again = script.samples_for(rows, responses, with_refs, 0)
    shifted = script.samples_for(rows, responses, with_refs, 10)
    assert first == again
    assert first["k1_denominator"] != shifted["k1_denominator"]
    assert len(first["k1_denominator"]) == 60 and len(first["k2_excluded"]) == 20
    assert len(first["k3_responses_with_refs"]) == 30
    assert len(first["k3_responses_without_refs"]) == 10
    assert set(first["k3_responses_with_refs"]) <= with_refs
    assert len(first["k4_coherent_absent"]) == 30
    assert first["exhaustive"] == ["r-u00003", "r-u00007"]
    assert script.draw(["a", "b"], 60, 1) == ["a", "b"]


# --- Commandes de la phase B --------------------------------------------------------------

RESPONSES = [
    (
        "qwen3.5:2b",
        "cass-001-directe",
        "Perruche : Cass. ass. plén., 17 novembre 2000, n° 99-13.701.",
    ),
    ("qwen3.5:2b", "cass-002-directe", "Cass. civ. 4e, 12 mars 2015, n° 13-27.123."),
    ("gemma4:e2b-it-qat", "cass-003-directe", "Cass. soc., 12 mars 2015, n° 13-27.124."),
    ("qwen3.5:4b", "cass-003-directe", "Cass. soc., 12 mars 2015, n° 13-27124."),
    ("qwen3.5:2b", "ce-001-directe", "CE, 3e et 8e chambres réunies, 10 juillet 2020, n° 428409."),
    ("qwen3.5:2b", "ce-002-directe", "CE, 3e ch., 10 octobre 2024, n° 447363."),
    ("qwen3.5:2b", "cass-004-directe", "CA Lyon, 12 mars 2015, n° 13/04567."),
    ("qwen3.5:2b", "cass-005-directe", "Cass. civ. 1re, 12 mars 2015."),
    ("qwen3.5:2b", "cass-006-directe", "Je ne connais pas d'arrêt précis."),
]


@pytest.fixture
def phase_b(tmp_path, monkeypatch):
    script = load_script()
    transport = FakeTransport(
        [
            ("/scan", {"date_start": "2000-11-17"}, [ok("scan_cc_2000-11-17.json")]),
            ("/scan", {}, [ok(EMPTY_SCAN)]),
            ("/search", {}, [ok(EMPTY_SEARCH)]),
        ]
    )
    monkeypatch.setattr(script, "FETCH", transport)
    monkeypatch.delenv("JUDILIBRE_KEY_ID", raising=False)
    env = tmp_path / "env"
    env.write_text(f"AUTRE=1\nJUDILIBRE_KEY_ID={KEY}\n", encoding="utf-8")
    collection = tmp_path / "collecte"
    rows = [line(m, r, rid) for m, rid, r in RESPONSES]
    digest = write_collection(collection, rows)
    index = CeIndex(parse_archive(ce_archive(tmp_path / "CE_fixture.zip")))
    index.save(tmp_path / "ce" / "index.jsonl")
    repo = tmp_path / "depot"
    repo.mkdir()
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=repo, check=True)
    (repo / "f.txt").write_text("grille", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "grille"], cwd=repo, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    out = tmp_path / "pre_etude"
    base = [
        "--collecte",
        str(collection),
        "--manifeste-sha256",
        digest,
        "--env-file",
        str(env),
        "--ce-index",
        str(tmp_path / "ce" / "index.jsonl"),
        "--cache",
        str(tmp_path / "cache"),
        "--sortie",
        str(out),
    ]
    monkeypatch.setattr(script, "REPO", repo)  # dépôt git jetable : HEAD et arbre contrôlés
    return {
        "script": script,
        "transport": transport,
        "base": base,
        "head": head,
        "repo": repo,
        "out": out,
        "tmp": tmp_path,
        "digest": digest,
        "collection": collection,
    }


def test_classer_refuses_other_head_or_dirty_tree(phase_b):
    script, base, out = phase_b["script"], phase_b["base"], phase_b["out"]
    assert script.main(["classer", *base, "--grille-figee", "0" * 40]) == 2
    (phase_b["repo"] / "f.txt").write_text("modifié", encoding="utf-8")
    assert script.main(["classer", *base, "--grille-figee", phase_b["head"]]) == 2
    assert not out.exists()
    assert phase_b["transport"].calls == []


def test_classer_refuses_wrong_manifest(phase_b):
    script, base = phase_b["script"], list(phase_b["base"])
    base[base.index(phase_b["digest"])] = "f" * 64
    assert script.main(["classer", *base, "--grille-figee", phase_b["head"]]) == 2
    assert not phase_b["out"].exists()


def test_classer_then_porte(phase_b, capsys):
    script, base, out, tmp = phase_b["script"], phase_b["base"], phase_b["out"], phase_b["tmp"]
    assert script.main(["classer", *base, "--grille-figee", phase_b["head"]]) == 0
    printed = capsys.readouterr().out
    assert "Aucune part calculée" in printed and "p =" not in printed and "0," not in printed
    rows = {r["canonical"] or r["unit_id"]: r for r in read_classement(out / "classement.jsonl")}
    classes = sorted((r["jurisdiction"], r["class"]) for r in rows.values())
    assert classes == [
        ("ca", "out_of_scope"),
        ("cc", "coherent_absent"),
        ("cc", "exists"),
        ("cc", "incoherent"),
        ("cc", "partial"),
        ("ce", "exists"),
        ("ce", "unverifiable"),
    ]
    coherent = rows["Cass. soc., 12 mars 2015, n° 13-27.124"]
    assert [c["model"] for c in coherent["citations"]] == ["qwen3.5:4b", "gemma4:e2b-it-qat"]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["funnel"] == {"generations": 9, "references_extracted": 8, "units": 7}
    assert manifest["grid_commit"] == phase_b["head"]
    assert "classes" not in json.dumps(manifest)
    # P9 : la clé n'apparaît dans aucun fichier écrit ; elle a bien servi au transport.
    assert phase_b["transport"].calls[0][1]["KeyId"] == KEY
    for path in tmp.rglob("*"):
        if path.is_file() and path.name != "env":
            assert KEY.encode() not in path.read_bytes(), path
    # P1 : porte refuse sans verdict, avec un verdict d'un autre classement ou en échec au tour 0.
    gate_path = tmp / "r_gate.toml"
    porte = ["porte", "--sortie", str(out), "--r-gate", str(gate_path)]
    assert script.main(porte) == 2
    sha = script.sha256_file(out / "classement.jsonl")
    verdict = tmp / "controle.json"
    for bad in (
        {"date": "2026-11-08", "classement_sha256": "0" * 64, "verdict": "accepte", "tour": 0},
        {"date": "2026-11-08", "classement_sha256": sha, "verdict": "echec", "tour": 0},
        {"classement_sha256": sha, "verdict": "accepte", "tour": 0},
    ):
        verdict.write_text(json.dumps(bad), encoding="utf-8")
        assert script.main([*porte, "--verdict", str(verdict)]) == 2
    assert not (out / "resume.json").exists() and not gate_path.exists()
    verdict.write_text(
        json.dumps(
            {
                "date": "2026-11-08",
                "classement_sha256": sha,
                "verdict": "accepte",
                "tour": 0,
                "fausses_absences": {"tirees": 1, "trouvees": 0},
            }
        ),
        encoding="utf-8",
    )
    capsys.readouterr()
    assert script.main([*porte, "--verdict", str(verdict)]) == 0
    line_out = capsys.readouterr().out.strip()
    assert line_out == (
        "1.12 · décision · porte R : p = 0,50 [0,09 ; 0,91] sur 2, comparatif, serrée, "
        "réserves : effectif faible ; famille dominante : qwen3.5"
    )
    resume = json.loads((out / "resume.json").read_text(encoding="utf-8"))
    assert resume["p_d1"]["n"] == 2 and resume["decision"] == "comparatif"
    assert resume["line"] == line_out
    assert resume["out_of_scope"] == {"ca": 1}
    gate_text = gate_path.read_text(encoding="utf-8")
    assert 'decision = "comparatif"' in gate_text and f'classement_sha256 = "{sha}"' in gate_text
    assert f'grid_commit = "{phase_b["head"]}"' in gate_text
    assert script.main([*porte, "--verdict", str(verdict)]) == 2  # une seule fois


def test_classer_stops_on_api_errors(phase_b, monkeypatch):
    script = phase_b["script"]
    failing = FakeTransport([("/scan", {}, [(503, {}, b"")]), ("/search", {}, [(503, {}, b"")])])
    monkeypatch.setattr(script, "FETCH", failing)
    assert script.main(["classer", *phase_b["base"], "--grille-figee", phase_b["head"]]) == 3
    assert not (phase_b["out"] / "classement.jsonl").exists()


def test_unknown_jurisdiction_is_partial():
    """D6 : sans juridiction, la référence est incomplète (`partial`), pas hors périmètre."""
    unit = classify("Voir le pourvoi n° 13-27.123 du 12 mars 2015.")
    assert unit.ref.jurisdiction is None
    assert unit.klass == "partial"


def test_unknown_seat_not_published():
    """D3, D6 : un siège hors des 36 (« CA Renault SA ») n'est jamais publié."""
    invented = classify("CA Renault SA, 12 mars 2015, n° 13/04567")
    assert invented.ref.formation == "Renault Sa" and invented.rules >= {"R-O3"}
    row = classement_row(invented, {})
    assert (row["formation"], row["canonical"]) == (None, None)
    assert "Renault" not in json.dumps(row)
    lyon = classement_row(classify("CA Lyon, 12 mars 2015, n° 13/04567"), {})
    assert lyon["formation"] == "Lyon" and lyon["canonical"].startswith("CA Lyon")


def _verdict(path, sha, verdict="accepte", tour=0, drawn=1, found=0, **extra):
    data = {
        "date": "2026-11-08",
        "classement_sha256": sha,
        "verdict": verdict,
        "tour": tour,
        "fausses_absences": {"tirees": drawn, "trouvees": found},
        **extra,
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_porte_false_absences_force_correction(phase_b):
    """P7 : plus d'une fausse absence -> pas de porte au tour 0, même « accepte »."""
    script, base, out, tmp = phase_b["script"], phase_b["base"], phase_b["out"], phase_b["tmp"]
    assert script.main(["classer", *base, "--grille-figee", phase_b["head"]]) == 0
    sha = script.sha256_file(out / "classement.jsonl")
    porte = ["porte", "--sortie", str(out), "--r-gate", str(tmp / "r_gate.toml")]
    for bad in (
        _verdict(tmp / "v.json", sha, drawn=1, found=2),  # trouvées > tirées
        _verdict(tmp / "v.json", sha, drawn=3, found=2),  # tirées != taille du tirage k = 4
        _verdict(tmp / "v.json", sha, drawn=1, found=None),
    ):
        assert script.main([*porte, "--verdict", str(bad)]) == 2
    assert not (out / "resume.json").exists()


def test_classer_single_correction_round(phase_b, capsys):
    """P1 : un second `classer` n'est admis qu'une fois, sur le verdict en échec du tour 0."""
    script, base, out, tmp = phase_b["script"], phase_b["base"], phase_b["out"], phase_b["tmp"]
    head = phase_b["head"]
    assert script.main(["classer", *base, "--grille-figee", head]) == 0
    sha0 = script.sha256_file(out / "classement.jsonl")
    assert script.main(["classer", *base, "--grille-figee", head]) == 2  # sans tour de correction
    accepted = _verdict(tmp / "v0.json", sha0, motif="extracteur")
    assert (
        script.main(["classer", *base, "--grille-figee", head, "--tour-correction", str(accepted)])
        == 2
    )
    no_motif = _verdict(tmp / "v0.json", sha0, verdict="echec")
    assert (
        script.main(["classer", *base, "--grille-figee", head, "--tour-correction", str(no_motif)])
        == 2
    )
    failed = _verdict(tmp / "v0.json", sha0, verdict="echec", motif="rappel de l'extraction")
    assert (
        script.main(["classer", *base, "--grille-figee", head, "--tour-correction", str(failed)])
        == 0
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["tour"] == 1 and manifest["correction"]["previous_classement_sha256"] == sha0
    assert manifest["correction"]["motif"] == "rappel de l'extraction"
    assert script.sha256_file(out / "tour0" / "classement.jsonl") == sha0
    assert (out / "interne" / "tour0" / "extraction.jsonl").is_file()
    assert (
        script.main(["classer", *base, "--grille-figee", head, "--tour-correction", str(failed)])
        == 2
    )
    journal = script.read_journal(out)
    assert [(e["command"], e["tour"]) for e in journal] == [("classer", 0), ("classer", 1)]
    # Porte : le verdict doit être celui du tour 1.
    sha1 = script.sha256_file(out / "classement.jsonl")
    porte = ["porte", "--sortie", str(out), "--r-gate", str(tmp / "r_gate.toml")]
    assert script.main([*porte, "--verdict", str(_verdict(tmp / "v1.json", sha1, tour=0))]) == 2
    assert script.main([*porte, "--verdict", str(_verdict(tmp / "v1.json", sha1, tour=1))]) == 0
    # Une seule porte, même si resume.json disparaît ; plus aucun classement ensuite.
    (out / "resume.json").unlink()
    assert script.main([*porte, "--verdict", str(tmp / "v1.json")]) == 2
    assert (
        script.main(["classer", *base, "--grille-figee", head, "--tour-correction", str(failed)])
        == 2
    )


def test_porte_refuses_changed_r_facts(phase_b):
    """`porte` relit les fenêtres : r_facts.toml doit être celui du classement."""
    script, base, out, tmp = phase_b["script"], phase_b["base"], phase_b["out"], phase_b["tmp"]
    assert script.main(["classer", *base, "--grille-figee", phase_b["head"]]) == 0
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["inputs"]["r_facts.toml"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    sha = script.sha256_file(out / "classement.jsonl")
    porte = ["porte", "--sortie", str(out), "--r-gate", str(tmp / "r_gate.toml")]
    assert script.main([*porte, "--verdict", str(_verdict(tmp / "v.json", sha))]) == 2
    assert not (out / "resume.json").exists()


def test_guard_checks_executed_code_repo(phase_b, monkeypatch):
    """Le contrôle de la grille figée porte sur le dépôt du code exécuté (`REPO`)."""
    script = phase_b["script"]
    assert script.guard_frozen_grid(phase_b["head"]) is None
    elsewhere = phase_b["tmp"] / "ailleurs"  # dossier hors dépôt : aucun HEAD
    elsewhere.mkdir()
    monkeypatch.setattr(script, "REPO", elsewhere)
    assert script.guard_frozen_grid(phase_b["head"]) is not None


def test_classer_stops_on_daily_quota(phase_b, monkeypatch):
    """P8 : quota journalier sous 1 000 -> code 3, rien d'écrit, pas d'entrée au journal."""
    script = phase_b["script"]
    low = '[{"window":62204,"type":"throttle","remaining":999},{"window":0,"remaining":19}]'
    transport = FakeTransport(
        [("/scan", {}, [ok(EMPTY_SCAN, low)]), ("/search", {}, [ok(EMPTY_SEARCH, low)])]
    )
    monkeypatch.setattr(script, "FETCH", transport)
    assert script.main(["classer", *phase_b["base"], "--grille-figee", phase_b["head"]]) == 3
    assert not phase_b["out"].exists()


def test_no_correction_after_porte_even_if_journal_and_resume_removed(phase_b):
    """P1 : le manifeste garde la trace de la porte ; un verdict illisible est refusé (code 2)."""
    script, base, out, tmp = phase_b["script"], phase_b["base"], phase_b["out"], phase_b["tmp"]
    head = phase_b["head"]
    assert script.main(["classer", *base, "--grille-figee", head]) == 0
    sha = script.sha256_file(out / "classement.jsonl")
    garbled = _verdict(tmp / "g.json", sha, verdict="accepte", found=None, motif="x")
    cmd = ["classer", *base, "--grille-figee", head, "--tour-correction"]
    assert script.main([*cmd, str(garbled)]) == 2
    absent = sum(
        1 for r in read_classement(out / "classement.jsonl") if r["class"] == "coherent_absent"
    )
    porte = ["porte", "--sortie", str(out), "--r-gate", str(tmp / "r_gate.toml")]
    accepted = _verdict(tmp / "v.json", sha, drawn=min(30, absent))
    assert script.main([*porte, "--verdict", str(accepted)]) == 0
    (out / "resume.json").unlink()
    (out / "journal.jsonl").unlink()
    assert script.main([*porte, "--verdict", str(accepted)]) == 2
    failed = _verdict(tmp / "f.json", sha, verdict="echec", motif="après coup")
    assert script.main([*cmd, str(failed)]) == 2
