"""Tâches `legal_s` et `legal_s_reserved` : description, vocabulaire, registre (story 1-9, D7)."""

from __future__ import annotations

import json
import re
import unicodedata

import pytest

from nn_weight_writing.tasks.io import materialize_bundle, read_bundle
from nn_weight_writing.tasks.legal import TASK_S, TASK_S_RESERVED
from nn_weight_writing.tasks.legal.facts import load_facts
from nn_weight_writing.tasks.legal.task import HEAD, SENTENCE_RESERVED, SENTENCE_S, TAIL
from nn_weight_writing.tasks.legal.types import HELD_OUT, KNOWN, TYPES
from nn_weight_writing.tasks.registry import get_task

# Termes simples en sous-chaîne ; termes marqués \b en mot entier (D7).
FORBIDDEN_TERMS: dict[str, list[str]] = {
    "t04": [
        "siege",
        "tribunal",
        "cour d'appel inexistante",
        "cours d'appel existantes",
        "sans cour d'appel",
        "ville",
        *[rf"\b{re.escape(s)}\b" for s in []],  # les 20 sièges sont ajoutés ci-dessous
    ],
    "t07": [
        "sous-sect",
        "creation",
        r"\bcreee?s?\b",
        "reforme",
        "2016",
        "2017",
        "anachron",
        "n'existait pas",
        "a la date",
    ],
    "t09": [
        r"\brg\b",
        r"\brole\b",
        "posterieur a l'arret",
        "posterieure a l'arret",
        "apres l'arret",
        "appel posterieur",
    ],
    "t11": ["autre juridiction", "format d'une autre", "format d'un autre", "croise"],
    "t12": [
        "dimanche",
        "ferie",
        "week-end",
        "weekend",
        "samedi",
        "jour de la semaine",
        "jour ouvr",
        "paques",
        "noel",
        "ascension",
        "toussaint",
        "pentecote",
        "assomption",
        "armistice",
        "14 juillet",
        "1er mai",
        "chome",
        "3133",
    ],
    "all": [rf"\b{t}\b" for t in HELD_OUT],
}
FORBIDDEN_TERMS["t04"] += [rf"\b{re.escape(_normalize)}\b" for _normalize in []]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().replace("’", "'"))
    return "".join(c for c in text if not unicodedata.combining(c))


def seat_terms() -> list[str]:
    return [rf"\b{re.escape(normalize(s))}\b" for s in load_facts().fake_seats]


def all_terms(type_id: str) -> list[str]:
    return [*FORBIDDEN_TERMS[type_id], *(seat_terms() if type_id == "t04" else [])]


def every_term() -> list[str]:
    return [t for key in (*HELD_OUT, "all") for t in all_terms(key)]


def matches(term: str, text: str) -> bool:
    return bool(re.search(term, text)) if term.startswith("\\b") else term in text


def test_reserved_description_names_no_held_out_type():
    texts = [TASK_S_RESERVED.description, *(e["description"] for e in TASK_S_RESERVED.vocabulary)]
    terms = every_term()
    assert len(terms) > 60
    for text in texts:
        folded = normalize(text)
        hits = [t for t in terms if matches(t, folded)]
        assert not hits, (hits, text[:80])
    assert [e["id"] for e in TASK_S_RESERVED.vocabulary] == list(KNOWN)
    assert len(KNOWN) == 10 and not set(KNOWN) & set(HELD_OUT)


def test_forbidden_terms_are_relevant():
    by_id = {e["id"]: e["description"] for e in TASK_S.vocabulary}
    for type_id in HELD_OUT:
        folded = normalize(by_id[type_id])
        assert any(matches(t, folded) for t in all_terms(type_id)), type_id
    # et la description de S, qui montre les 15 types, est bien détectée par ces termes
    folded = normalize(TASK_S.description + " ".join(by_id.values()))
    assert sum(matches(t, folded) for t in all_terms("t12")) >= 3


def test_s_vocabulary_and_metadata():
    assert [e["id"] for e in TASK_S.vocabulary] == [f"t{i:02d}" for i in range(1, 16)]
    assert [t.status for t in TYPES[:3]] == ["attested"] * 3
    assert {t.status for t in TYPES[3:]} == {"reconstructed"}
    by_id = {t.id: t for t in TYPES}
    assert by_id["t02"].nuss == "attested_secondary"
    assert by_id["t01"].nuss == by_id["t03"].nuss == "attested"
    assert {t.nuss for t in TYPES} == {"attested", "attested_secondary", "reconstructed"}
    assert all(e["description"] for e in TASK_S.vocabulary)


def test_descriptions_differ_by_one_sentence():
    s, r = TASK_S.description, TASK_S_RESERVED.description
    assert s != r
    assert s.replace(SENTENCE_S, "") == r.replace(SENTENCE_RESERVED, "")
    assert s == f"{HEAD} {SENTENCE_S}\n\n{TAIL}"
    t06 = next(e for e in TASK_S.vocabulary if e["id"] == "t06")["description"]
    assert "1er novembre 2026" in t06
    assert load_facts().corpus_date.isoformat() == "2026-11-01"
    assert "legal.chars@1" in s and "3 060" in s


def test_registry_and_bundle(tmp_path):
    for name in ("legal_s", "legal_s_reserved"):
        spec = get_task(name)
        assert spec.codec.encoder_id == "legal.chars@1"
        assert spec.session_datasets == ("session",)
    examples = tmp_path / "examples.jsonl"
    rows = [{"id": "legal-s00001", "raw": "CE, Sect., 12 mars 2015, n° 381234"}]
    examples.write_text("".join(json.dumps(r) + "\n" for r in rows), "utf-8")
    spec = get_task("legal_s_reserved")
    materialize_bundle(
        examples,
        tmp_path / "bundle",
        task=spec.name,
        description=spec.description,
        encoder=spec.codec.encoder_id,
        vocabulary=list(spec.vocabulary),
    )
    meta = json.loads((tmp_path / "bundle" / "task.json").read_text("utf-8"))
    assert meta["encoder"] == "legal.chars@1" and meta["task"] == "legal_s_reserved"
    assert [e["id"] for e in meta["vocabulary"]] == list(KNOWN)
    assert read_bundle(tmp_path / "bundle").encoder == "legal.chars@1"


def test_forbidden_terms_catch_a_leak():
    leaked = normalize(TASK_S_RESERVED.description + " Décision rendue un dimanche.")
    assert any(matches(t, leaked) for t in all_terms("t12"))
    with pytest.raises(AssertionError):
        assert not any(matches(t, normalize("CA Lille")) for t in all_terms("t04"))
