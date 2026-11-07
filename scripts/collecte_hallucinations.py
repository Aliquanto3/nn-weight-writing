"""Collecte des hallucinations juridiques de SLM par Ollama (story 1-12a).

Script unique, bibliothèque standard seulement, jamais importé par le paquet `nn_weight_writing`.
Le projet ne lit que les fichiers figés (sha256 dans `manifest.json`).

Usage :
    uv run python scripts/collecte_hallucinations.py pilote  [--sortie DOSSIER]
    uv run python scripts/collecte_hallucinations.py collecte --ensemble noyau|tout [--sortie D]
    uv run python scripts/collecte_hallucinations.py figer   [--sortie DOSSIER]

Chaque génération est une ligne JSONL en ajout seul ; un couple (model, request_id) déjà écrit
est sauté (reprise après interruption).

Le compteur de rendement (`compter_motifs`) est GROSSIER : il ne sert qu'à dimensionner la
collecte. Ce n'est PAS l'extracteur de références de 1-12 (pas de grille d'incohérence, pas de
retrait des noms de parties, pas de vérification contre une base).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

OLLAMA = "http://localhost:11434"
REQUETES = Path(__file__).with_name("collecte") / "requetes.json"
SORTIE_DEFAUT = Path("data") / "r" / "collecte"

MODELES = [
    "qwen3.5:0.8b",
    "qwen3.5:2b",
    "qwen3.5:4b",
    "gemma4:e2b-it-qat",
    "gemma4:e4b-it-qat",
    "ministral-3:3b",
    "phi4-mini:3.8b",
    "granite4.2:3b",
    "lfm3:1.7b-q4_K_M",
    "nemotron-3-nano:4b",
]
MODELES_PILOTE = ["qwen3.5:2b", "gemma4:e4b-it-qat", "ministral-3:3b"]
# Fixées avant le pilote : 5 Cour de cassation, 5 Conseil d'État, les deux tournures.
REQUETES_PILOTE = [
    "cass-001-directe",
    "cass-004-naturelle",
    "cass-008-directe",
    "cass-012-naturelle",
    "cass-017-directe",
    "ce-002-naturelle",
    "ce-006-directe",
    "ce-009-naturelle",
    "ce-014-directe",
    "ce-019-naturelle",
]
OPTIONS = {"temperature": 0, "seed": 0, "num_predict": 512}
SEUIL_REFERENCES = 600
GENERATIONS_NOYAU = 800
GENERATIONS_TOUT = 1600

# --- Compteur grossier -------------------------------------------------------------------------

MOIS = (
    "janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|"
    "décembre|decembre"
)
MOTIFS = {
    "pourvoi": re.compile(r"\b\d{2}-\d{2}\.\d{3}\b"),
    "requete_ce": re.compile(
        r"(?:requête|req\.|n[°ºo]s?)\s*(?:n[°ºo]\s*)?\.?\s*(\d{5,6})\b", re.IGNORECASE
    ),
    "ecli": re.compile(r"\bECLI:[A-Za-z]{2}:[A-Za-z0-9]+:\d{4}:[A-Za-z0-9.]+", re.IGNORECASE),
    "cass": re.compile(
        r"\bCass(?:\.|ation)[^\n]{0,80}?(?:chambre|\bch\.|\bciv\.|\bcrim\.|\bsoc\.|\bcom\.)",
        re.IGNORECASE,
    ),
    "date": re.compile(
        rf"\b\d{{1,2}}(?:er)?\s+(?:{MOIS})\s+\d{{4}}\b|\b\d{{1,2}}/\d{{1,2}}/\d{{4}}\b",
        re.IGNORECASE,
    ),
}


def normaliser_motif(genre: str, texte: str) -> str:
    """Normalisation grossière : minuscules, espaces et ponctuation de bord retirés."""
    t = re.sub(r"\s+", " ", texte.strip().lower()).strip(" .,;:()")
    if genre in ("pourvoi", "ecli"):
        return t.replace(" ", "")
    if genre == "requete_ce":
        return re.sub(r"\D", "", t)
    return t


def compter_motifs(reponse: str) -> list[tuple[str, str]]:
    """Motifs de références d'une réponse, en (genre, valeur normalisée), doublons conservés."""
    trouves = []
    for genre, motif in MOTIFS.items():
        for m in motif.finditer(reponse):
            brut = m.group(1) if genre == "requete_ce" else m.group(0)
            trouves.append((genre, normaliser_motif(genre, brut)))
    return trouves


def rendement(reponses: list[str]) -> dict:
    """Rendement grossier d'un ensemble de réponses."""
    n = len(reponses)
    motifs = [compter_motifs(r) for r in reponses]
    total = sum(len(m) for m in motifs)
    distincts = len({x for m in motifs for x in m})
    sans = sum(1 for m in motifs if not m)
    return {
        "generations": n,
        "motifs": total,
        "motifs_par_generation": total / n if n else 0.0,
        "motifs_distincts": distincts,
        "part_distincte": distincts / total if total else 0.0,
        "sans_motif": sans,
        "part_sans_motif": sans / n if n else 0.0,
    }


def estimer_references(motifs_par_generation: float, part_distincte: float, n_gen: int) -> float:
    """Règle de taille : motifs par génération x part distincte x nombre de générations."""
    return motifs_par_generation * part_distincte * n_gen


def choisir_ensemble(motifs_par_generation: float, part_distincte: float) -> tuple[str, float]:
    """Noyau si l'estimation sur 800 générations atteint 600, sinon tout (1 600 générations)."""
    est = estimer_references(motifs_par_generation, part_distincte, GENERATIONS_NOYAU)
    return ("noyau" if est >= SEUIL_REFERENCES else "tout"), est


# --- Requêtes, reprise, ligne JSONL --------------------------------------------------------------


def charger_requetes() -> list[dict]:
    return json.loads(REQUETES.read_text(encoding="utf-8"))


def selectionner(requetes: list[dict], mode: str) -> list[dict]:
    if mode == "pilote":
        par_id = {r["id"]: r for r in requetes}
        return [par_id[i] for i in REQUETES_PILOTE]
    if mode == "noyau":
        return [r for r in requetes if r["ensemble"] == "noyau"]
    if mode == "tout":
        return list(requetes)
    raise ValueError(f"ensemble inconnu : {mode}")


def deja_ecrits(chemin: Path) -> set[tuple[str, str]]:
    """Couples (model, request_id) déjà dans le JSONL ; une ligne finale tronquée est ignorée."""
    if not chemin.exists():
        return set()
    faits = set()
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        faits.add((d["model"], d["request_id"]))
    return faits


def a_faire(modeles: list[str], requetes: list[dict], faits: set[tuple[str, str]]):
    """Couples restants, modèle en boucle externe (un seul chargement par modèle)."""
    return [(m, r) for m in modeles for r in requetes if (m, r["id"]) not in faits]


def construire_ligne(modele: str, digest: str, version: str, requete: dict, rep: dict) -> dict:
    msg = rep.get("message") or {}
    return {
        "request_id": requete["id"],
        "model": modele,
        "digest": digest,
        "ollama_version": version,
        "prompt": requete["prompt"],
        "response": msg.get("content", ""),
        "done_reason": rep.get("done_reason"),
        "eval_count": rep.get("eval_count"),
        "prompt_eval_count": rep.get("prompt_eval_count"),
        "total_duration_ns": rep.get("total_duration"),
        "load_duration_ns": rep.get("load_duration"),
        "prompt_eval_duration_ns": rep.get("prompt_eval_duration"),
        "eval_duration_ns": rep.get("eval_duration"),
        "timestamp_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "settings": {"stream": False, "think": False, "options": OPTIONS, "system": None},
    }


# --- Ollama ------------------------------------------------------------------------------------


def _http(chemin: str, corps: dict | None = None, timeout: int = 900) -> dict:
    data = None if corps is None else json.dumps(corps).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA + chemin, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - localhost
        return json.loads(r.read().decode("utf-8"))


def version_ollama() -> str:
    return _http("/api/version", timeout=30)["version"]


def digests(modeles: list[str]) -> dict[str, str]:
    tags = {m["name"]: m["digest"] for m in _http("/api/tags", timeout=30)["models"]}
    manquants = [m for m in modeles if m not in tags]
    if manquants:
        raise SystemExit(f"Modèles absents d'Ollama : {manquants}")
    return {m: tags[m] for m in modeles}


def generer(modele: str, prompt: str) -> dict:
    corps = {
        "model": modele,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": OPTIONS,
    }
    for essai in range(3):
        try:
            return _http("/api/chat", corps)
        except urllib.error.URLError, TimeoutError, ConnectionError:
            if essai == 2:
                raise
            time.sleep(10)
    raise RuntimeError("inatteignable")


def executer(sortie: Path, fichier: str, modeles: list[str], requetes: list[dict]) -> None:
    sortie.mkdir(parents=True, exist_ok=True)
    chemin = sortie / fichier
    version = version_ollama()
    dig = digests(modeles)
    restants = a_faire(modeles, requetes, deja_ecrits(chemin))
    total = len(modeles) * len(requetes)
    print(f"Ollama {version} ; {len(restants)} générations à faire sur {total}", flush=True)
    t0 = time.time()
    with chemin.open("a", encoding="utf-8", newline="\n") as f:
        for i, (modele, requete) in enumerate(restants, 1):
            rep = generer(modele, requete["prompt"])
            ligne = construire_ligne(modele, dig[modele], version, requete, rep)
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
            f.flush()
            if i % 20 == 0 or i == len(restants):
                print(f"{i}/{len(restants)} ({time.time() - t0:.0f} s)", flush=True)


# --- Figer -------------------------------------------------------------------------------------


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def figer(sortie: Path) -> dict:
    fichiers = [REQUETES] + [sortie / n for n in ("pilote.jsonl", "collecte.jsonl")]
    manifest: dict = {"fichiers": {}, "ollama_versions": [], "digests": {}}
    for chemin in fichiers:
        if not chemin.exists():
            continue
        manifest["fichiers"][chemin.name] = {
            "sha256": sha256_fichier(chemin),
            "octets": chemin.stat().st_size,
        }
        if chemin.suffix == ".jsonl":
            for ligne in chemin.read_text(encoding="utf-8").splitlines():
                d = json.loads(ligne)
                manifest["digests"][d["model"]] = d["digest"]
                if d["ollama_version"] not in manifest["ollama_versions"]:
                    manifest["ollama_versions"].append(d["ollama_version"])
    chemin_manifest = sortie / "manifest.json"
    if chemin_manifest.exists():
        os.chmod(chemin_manifest, stat.S_IWRITE | stat.S_IREAD)
    chemin_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for chemin in [*fichiers, chemin_manifest]:
        if chemin.exists():
            os.chmod(chemin, stat.S_IREAD)
    return manifest


# --- Rapport du pilote -------------------------------------------------------------------------


def lire_jsonl(chemin: Path) -> list[dict]:
    return [json.loads(ligne) for ligne in chemin.read_text(encoding="utf-8").splitlines()]


def rapport_pilote(sortie: Path) -> None:
    lignes = lire_jsonl(sortie / "pilote.jsonl")
    g = rendement([d["response"] for d in lignes])
    est = choisir_ensemble(g["motifs_par_generation"], g["part_distincte"])
    print(json.dumps(g, indent=1))
    for m in MODELES_PILOTE:
        r = rendement([d["response"] for d in lignes if d["model"] == m])
        print(m, json.dumps(r))
    duree = sum(d["total_duration_ns"] or 0 for d in lignes) / 1e9
    print(f"durée cumulée {duree:.0f} s ; par génération {duree / len(lignes):.1f} s")
    print(f"estimation sur 800 générations : {est[1]:.0f} ; ensemble retenu : {est[0]}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sp = p.add_subparsers(dest="cmd", required=True)
    for nom in ("pilote", "collecte", "figer"):
        s = sp.add_parser(nom)
        s.add_argument("--sortie", type=Path, default=SORTIE_DEFAUT)
        if nom == "collecte":
            s.add_argument("--ensemble", choices=["noyau", "tout"], required=True)
    a = p.parse_args(argv)
    requetes = charger_requetes()
    if a.cmd == "pilote":
        executer(a.sortie, "pilote.jsonl", MODELES_PILOTE, selectionner(requetes, "pilote"))
        rapport_pilote(a.sortie)
    elif a.cmd == "collecte":
        executer(a.sortie, "collecte.jsonl", MODELES, selectionner(requetes, a.ensemble))
    else:
        print(json.dumps(figer(a.sortie), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
