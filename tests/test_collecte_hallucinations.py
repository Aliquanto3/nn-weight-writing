"""Tests des fonctions pures de scripts/collecte_hallucinations.py (sans Ollama)."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "collecte_hallucinations", RACINE / "scripts" / "collecte_hallucinations.py"
)
col = importlib.util.module_from_spec(spec)
spec.loader.exec_module(col)


def test_requetes_structure() -> None:
    reqs = col.charger_requetes()
    assert len(reqs) == 160
    assert len({r["id"] for r in reqs}) == 160
    assert reqs[0]["id"] == "cass-001-directe"
    assert {r["ensemble"] for r in reqs} == {"noyau", "reserve"}
    assert sum(r["ensemble"] == "noyau" for r in reqs) == 80
    for j in ("cassation", "conseil_etat"):
        assert sum(r["juridiction"] == j for r in reqs) == 80
        assert len({r["theme"] for r in reqs if r["juridiction"] == j}) == 40
    assert {r["tournure"] for r in reqs} == {"directe", "naturelle"}
    assert len(col.selectionner(reqs, "pilote")) == 10
    assert len(col.selectionner(reqs, "noyau")) == 80
    assert all(r["ensemble"] == "noyau" for r in col.selectionner(reqs, "pilote"))
    with pytest.raises(ValueError):
        col.selectionner(reqs, "autre")


def test_compteur_motifs() -> None:
    texte = (
        "Cass. civ. 1re chambre, 12 mars 2019, pourvoi n° 18-12.345. "
        "CE, 5 juin 2020, requête n° 421234. ECLI:FR:CCASS:2019:C100123. 18-12.345 encore."
    )
    m = col.compter_motifs(texte)
    assert ("pourvoi", "18-12.345") in m
    assert m.count(("pourvoi", "18-12.345")) == 2
    assert ("requete_ce", "421234") in m
    assert ("ecli", "ecli:fr:ccass:2019:c100123") in m
    assert ("date", "12 mars 2019") in m
    assert any(g == "cass" for g, _ in m)
    assert col.compter_motifs("Je ne peux pas citer d'arrêt précis.") == []


def test_rendement() -> None:
    r = col.rendement(["pourvoi 18-12.345 et 18-12.345", "rien", "pourvoi 19-10.001"])
    assert r["generations"] == 3
    assert r["motifs"] == 3
    assert r["motifs_distincts"] == 2
    assert r["sans_motif"] == 1
    assert r["part_distincte"] == pytest.approx(2 / 3)
    assert r["motifs_par_generation"] == pytest.approx(1.0)
    assert col.rendement([])["motifs_par_generation"] == 0.0


def test_regle_de_taille() -> None:
    assert col.estimer_references(2.0, 0.5, 800) == pytest.approx(800)
    assert col.choisir_ensemble(2.0, 0.5)[0] == "noyau"
    assert col.choisir_ensemble(1.5, 0.5) == ("noyau", pytest.approx(600))
    assert col.choisir_ensemble(1.49, 0.5)[0] == "tout"


def test_reprise_et_ligne(tmp_path: Path) -> None:
    reqs = col.selectionner(col.charger_requetes(), "pilote")
    ligne = col.construire_ligne(
        "m1", "dig", "0.1", reqs[0], {"message": {"content": "x"}, "done_reason": "stop"}
    )
    assert ligne["request_id"] == "cass-001-directe"
    assert ligne["response"] == "x"
    assert ligne["error"] is None
    err = col.construire_ligne(
        "m1", "d", "0.1", reqs[0], {"error": "boucle", "done_reason": "error"}
    )
    assert (err["response"], err["error"], err["done_reason"]) == ("", "boucle", "error")
    assert ligne["settings"]["options"] == {"temperature": 0, "seed": 0, "num_predict": 512}
    assert ligne["settings"]["think"] is False
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", ligne["timestamp_utc"])
    f = tmp_path / "a.jsonl"
    f.write_text(json.dumps(ligne) + "\n" + '{"model": "m1", "requ', encoding="utf-8")
    faits = col.deja_ecrits(f)
    assert faits == {("m1", "cass-001-directe")}
    restants = col.a_faire(["m1", "m2"], reqs, faits)
    assert len(restants) == 19
    assert ("m1", reqs[0]) not in restants
    assert restants[0][0] == "m1" and restants[-1][0] == "m2"
    assert col.deja_ecrits(tmp_path / "absent.jsonl") == set()


def test_figer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # figer() met requetes.json en lecture seule : travailler sur une copie.
    copie = tmp_path / "requetes.json"
    shutil.copyfile(col.REQUETES, copie)
    monkeypatch.setattr(col, "REQUETES", copie)
    ligne = {"model": "m1", "digest": "d1", "ollama_version": "9.9"}
    (tmp_path / "pilote.jsonl").write_text(json.dumps(ligne) + "\n", encoding="utf-8")
    man = col.figer(tmp_path)
    assert man["digests"] == {"m1": "d1"}
    assert man["ollama_versions"] == ["9.9"]
    assert man["fichiers"]["pilote.jsonl"]["sha256"] == col.sha256_fichier(
        tmp_path / "pilote.jsonl"
    )
    assert "collecte.jsonl" not in man["fichiers"]
    assert not (tmp_path / "pilote.jsonl").stat().st_mode & 0o200
    col.figer(tmp_path)  # idempotent : le manifeste en lecture seule est réécrit
    assert not copie.stat().st_mode & 0o200
    assert os.access(RACINE / "scripts" / "collecte" / "requetes.json", os.W_OK)
    for f in tmp_path.iterdir():
        os.chmod(f, stat.S_IWRITE | stat.S_IREAD)  # nettoyage de tmp_path sous Windows


def test_reprise_apres_ligne_tronquee(tmp_path: Path) -> None:
    reqs = col.selectionner(col.charger_requetes(), "pilote")
    rep = {"message": {"content": "x"}, "done_reason": "stop"}
    l1 = col.construire_ligne("m1", "d", "0.1", reqs[0], rep)
    f = tmp_path / "c.jsonl"
    f.write_text(json.dumps(l1) + "\n" + '{"model": "m1", "requ', encoding="utf-8")
    assert col.reparer_fin(f) == len('{"model": "m1", "requ')
    assert col.reparer_fin(f) == 0
    l2 = col.construire_ligne("m1", "d", "0.1", reqs[1], rep)
    with f.open("a", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(l2) + "\n")
    assert [d["request_id"] for d in col.lire_jsonl(f)] == [reqs[0]["id"], reqs[1]["id"]]
    g = tmp_path / "seule.jsonl"
    g.write_text('{"model"', encoding="utf-8")
    col.reparer_fin(g)
    assert g.read_bytes() == b""
    assert col.reparer_fin(tmp_path / "absent.jsonl") == 0


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_sortie_defaut_vise_le_depot_principal(tmp_path: Path) -> None:
    principal = tmp_path / "principal"
    principal.mkdir()
    _git("init", "-q", cwd=principal)
    _git(
        "-c",
        "user.email=t@t",
        "-c",
        "user.name=t",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "i",
        cwd=principal,
    )
    _git("worktree", "add", "-q", str(tmp_path / "wt"), cwd=principal)
    (tmp_path / "wt" / "scripts").mkdir()
    attendu = principal.resolve()
    assert col.racine_depot_principal(tmp_path / "wt" / "scripts") == attendu
    assert col.racine_depot_principal(principal) == attendu
    assert col.sortie_defaut().is_absolute()
    assert col.sortie_defaut().parts[-3:] == ("data", "r", "collecte")


def test_rapport_pilote_exclut_les_erreurs(tmp_path: Path, capsys) -> None:
    reqs = col.selectionner(col.charger_requetes(), "pilote")
    ok = col.construire_ligne(
        "qwen3.5:2b", "d", "0.1", reqs[0], {"message": {"content": "18-12.345"}}
    )
    err = col.construire_ligne("qwen3.5:2b", "d", "0.1", reqs[1], {"done_reason": "error"})
    ancien = {k: v for k, v in ok.items() if k != "error"}  # ligne antérieure à la clé « error »
    (tmp_path / "pilote.jsonl").write_text(
        "".join(json.dumps(d) + "\n" for d in (ok, err, ancien)), encoding="utf-8"
    )
    col.rapport_pilote(tmp_path)
    sortie = capsys.readouterr().out
    assert "1 génération(s) en erreur exclue(s)" in sortie
    assert '"generations": 2' in sortie and '"sans_motif": 0' in sortie


def test_paquet_nimporte_ni_script_ni_ollama() -> None:
    for f in (RACINE / "src" / "nn_weight_writing").rglob("*.py"):
        src = f.read_text(encoding="utf-8")
        assert not re.search(r"^\s*(import|from)\s+(ollama|collecte_hallucinations)\b", src, re.M)
        assert "collecte_hallucinations" not in src


def test_generer_consigne_erreur_500(monkeypatch: pytest.MonkeyPatch) -> None:
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error":"token repeat limit reached"}')

        def log_message(self, *a) -> None:
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(col, "OLLAMA", f"http://127.0.0.1:{srv.server_port}")
    monkeypatch.setattr(col.time, "sleep", lambda s: None)
    try:
        rep = col.generer("m", "p")
    finally:
        srv.shutdown()
    assert rep == {"error": "token repeat limit reached", "done_reason": "error"}
