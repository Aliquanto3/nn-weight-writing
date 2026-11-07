"""Lecture de la collecte figée (story 1-12, D1, AC1). Collecte factice écrite dans `tmp_path`."""

from __future__ import annotations

import hashlib
import json

import pytest

from nn_weight_writing.datasets.legal_r import frozen
from nn_weight_writing.datasets.legal_r.frozen import CollectionError, read_collection

SETTINGS = {"stream": False, "think": False, "options": {"temperature": 0}, "system": None}
REQUESTS = [{"id": "cass-001-directe", "prompt": "Citez un arrêt."}]


def line(model: str, response: str, request_id: str = "cass-001-directe") -> dict:
    return {
        "request_id": request_id,
        "model": model,
        "digest": "sha256:" + "a" * 64,
        "ollama_version": "0.30.0",
        "prompt": "Citez un arrêt.",
        "response": response,
        "done_reason": "stop",
        "timestamp_utc": "2026-11-07T03:00:00Z",
        "settings": SETTINGS,
    }


def write_collection(directory, rows, *, pilot_rows=None, raw: bytes | None = None) -> str:
    """Écrit collecte.jsonl, pilote.jsonl, requetes.json et manifest.json ; renvoie son sha256."""
    directory.mkdir(parents=True, exist_ok=True)
    data = (
        raw
        if raw is not None
        else "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    )
    (directory / "collecte.jsonl").write_bytes(data)
    pilot = "".join(json.dumps(r) + "\n" for r in (pilot_rows or [])).encode("utf-8")
    (directory / "pilote.jsonl").write_bytes(pilot)
    requests = json.dumps(REQUESTS, ensure_ascii=False).encode("utf-8")
    (directory / "requetes.json").write_bytes(requests)
    manifest = {
        "fichiers": {
            name: {"sha256": hashlib.sha256(content).hexdigest(), "octets": len(content)}
            for name, content in (
                ("requetes.json", requests),
                ("pilote.jsonl", pilot),
                ("collecte.jsonl", data),
            )
        },
        "ollama_versions": ["0.30.0"],
        "digests": {},
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    (directory / "manifest.json").write_bytes(manifest_bytes)
    return hashlib.sha256(manifest_bytes).hexdigest()


def test_reads_generations(tmp_path):
    digest = write_collection(tmp_path, [line("qwen3.5:2b", "Cass. soc., 1er mars 2015")])
    (gen,) = read_collection(
        tmp_path, manifest_sha256=digest, requests_path=tmp_path / "requetes.json"
    )
    assert (gen.model, gen.request_id, gen.generation_date) == (
        "qwen3.5:2b",
        "cass-001-directe",
        "2026-11-07",
    )


def test_sha256_checked_before_decoding(tmp_path, monkeypatch):
    digest = write_collection(tmp_path, [line("qwen3.5:2b", "réponse")])
    path = tmp_path / "collecte.jsonl"
    path.write_bytes(path.read_bytes().replace(b"r\xc3\xa9ponse", b"r\xc3\xa9ponsE"))
    decoded = []
    real_loads = json.loads

    def spy(*args, **kwargs):
        decoded.append(args)
        return real_loads(*args, **kwargs)

    monkeypatch.setattr(frozen.json, "loads", spy)
    with pytest.raises(CollectionError, match="empreinte de collecte.jsonl"):
        read_collection(tmp_path, manifest_sha256=digest)
    # Seul le manifeste a été décodé, aucune ligne de la collecte.
    assert len(decoded) == 1


def test_manifest_digest_mismatch_refused(tmp_path):
    write_collection(tmp_path, [line("qwen3.5:2b", "réponse")])
    with pytest.raises(CollectionError, match="--manifeste-sha256"):
        read_collection(tmp_path, manifest_sha256="0" * 64)
    (tmp_path / "manifest.json").unlink()
    with pytest.raises(CollectionError, match="manifest.json absent"):
        read_collection(tmp_path, manifest_sha256="0" * 64)


def test_truncated_line_refused(tmp_path):
    raw = json.dumps(line("qwen3.5:2b", "a")) + "\n" + json.dumps(line("qwen3.5:4b", "b"))[:40]
    digest = write_collection(tmp_path, [], raw=raw.encode("utf-8"))
    with pytest.raises(CollectionError, match="tronquée"):
        read_collection(tmp_path, manifest_sha256=digest)
    bad = write_collection(tmp_path, [], raw=b'{"model": "x"\n')
    with pytest.raises(CollectionError, match="illisible"):
        read_collection(tmp_path, manifest_sha256=bad)


def test_only_collecte_is_read(tmp_path):
    digest = write_collection(
        tmp_path,
        [line("qwen3.5:2b", "collecte")],
        pilot_rows=[line("qwen3.5:2b", "pilote"), line("gemma4:e4b-it-qat", "pilote")],
    )
    gens = read_collection(tmp_path, manifest_sha256=digest)
    assert [g.response for g in gens] == ["collecte"]
    (tmp_path / "pilote.jsonl").write_text("modifié", encoding="utf-8")
    assert [g.response for g in read_collection(tmp_path, manifest_sha256=digest)] == ["collecte"]


def test_prompt_and_settings_checked(tmp_path):
    other = line("qwen3.5:4b", "b")
    other["prompt"] = "Autre consigne."
    digest = write_collection(tmp_path, [line("qwen3.5:2b", "a"), other])
    with pytest.raises(CollectionError, match="prompt différent"):
        read_collection(tmp_path, manifest_sha256=digest, requests_path=tmp_path / "requetes.json")
    changed = line("qwen3.5:4b", "b")
    changed["settings"] = {**SETTINGS, "think": True}
    digest = write_collection(tmp_path, [line("qwen3.5:2b", "a"), changed])
    with pytest.raises(CollectionError, match="réglages"):
        read_collection(tmp_path, manifest_sha256=digest)
