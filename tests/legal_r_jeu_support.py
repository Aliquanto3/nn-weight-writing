"""Monde de fixtures du jeu R (story 1-13) : classement, extraction, Judilibre, index du CE.

Tout est écrit par ce module, d'après des règles fixées ici : aucune donnée de la collecte, du
classement réel ni de `data/r/`. Seul le transport HTTP de Judilibre est un double (frontière
réseau) ; le client, le cache, le normaliseur et la grille sont ceux du projet.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from nn_weight_writing.datasets.legal_r.ce_index import CeIndex
from nn_weight_writing.datasets.legal_r.dataset import FakeRow, Pair, type_of
from nn_weight_writing.datasets.legal_r.grid import GRID_VERSION, nuss_types
from nn_weight_writing.datasets.legal_r.judilibre import BASE_URL
from nn_weight_writing.datasets.legal_r.normalize import NORMALIZER_ID
from nn_weight_writing.datasets.legal_r.pool import RealCandidate
from nn_weight_writing.datasets.legal_r.r_facts import r_facts_sha256
from nn_weight_writing.datasets.legal_rules import is_working_day
from nn_weight_writing.tasks.legal.facts import facts_sha256
from nn_weight_writing.tasks.legal.reference import Reference, format_reference

CC_CODES = {
    "civ. 1re": "civ1",
    "civ. 2e": "civ2",
    "civ. 3e": "civ3",
    "com.": "comm",
    "soc.": "soc",
    "crim.": "cr",
}
CE_FORMATIONS = {"6e ch.": "6ème chambre", "Sect.": "Section du Contentieux"}
RATE = '[{"window":62204,"type":"throttle","remaining":999999}]'
MODELS = ("qwen3.5:2b", "gemma3:1b", "llama3.2:1b")


def raw_of(jurisdiction, formation, y, m, d, number) -> str:
    return format_reference(Reference(jurisdiction, formation, d, m, y, number))


def versions() -> dict:
    return {
        "normalizer": NORMALIZER_ID,
        "grid": GRID_VERSION,
        "r_facts_sha256": r_facts_sha256(),
        "facts_sha256": facts_sha256(),
    }


def classement_row(uid, jurisdiction, formation, y, m, d, number, klass, rules=(), **extra):
    try:
        canonical = raw_of(jurisdiction, formation, y, m, d, number) if formation else None
    except ValueError, IndexError:
        canonical = None
    rules = sorted(rules)
    row = {
        "schema": 1,
        "unit_id": uid,
        "jurisdiction": jurisdiction,
        "formation": formation,
        "year": y,
        "month": m,
        "day": d,
        "number": number,
        "ecli": None,
        "canonical": canonical,
        "class": klass,
        "rules": rules,
        "nuss_types": list(nuss_types(frozenset(rules))),
        "unverifiable_reason": None,
        "partial_match": None,
        "grid_false_positive": False,
        "class_conflict": False,
        "verification": {"status": "absent"},
        "citations": [
            {"model": extra.pop("model", MODELS[0]), "digest": "0" * 12, "request_id": "q"}
        ],
        "source": "slm",
        "versions": versions(),
    }
    row.update(extra)
    return row


def extraction_row(row: dict) -> dict:
    raw = row["canonical"] or "texte sans référence"
    model = row["citations"][0]["model"]
    return {
        "unit_id": row["unit_id"],
        "model": model,
        "request_id": "q",
        "start": 0,
        "end": len(raw),
        "raw": raw,
    }


# --- objets synthétiques pour les tests unitaires ------------------------------------------


def fake(uid, jurisdiction="cc", formation="civ. 1re", y=2015, m=3, d=12, number=None, **kw):
    rules = tuple(sorted(kw.pop("rules", ())))
    number = number or (
        f"{(y - 1) % 100:02d}-10.{int(uid[-3:]):03d}"
        if jurisdiction == "cc"
        else f"{460000 + int(uid[-3:])}"
    )
    return FakeRow(
        unit_id=uid,
        jurisdiction=jurisdiction,
        formation=formation,
        year=y,
        month=m,
        day=d,
        number=number,
        raw=kw.pop("raw", None) or raw_of(jurisdiction, formation, y, m, d, number),
        type_id=type_of(rules, nuss_types(frozenset(rules))),
        rules=rules,
        nuss_types=nuss_types(frozenset(rules)),
        model=kw.pop("model", MODELS[0]),
        klass="incoherent" if rules else "coherent_absent",
        **kw,
    )


def real(jurisdiction, formation, day: date, number, source_id=None) -> RealCandidate:
    return RealCandidate(
        jurisdiction=jurisdiction,
        formation=formation,
        day=day,
        number=number,
        raw=raw_of(jurisdiction, formation, day.year, day.month, day.day, number),
        source="judilibre" if jurisdiction == "cc" else "ce-opendata",
        source_id=source_id or f"id-{jurisdiction}-{number}",
        update_date=None,
        numbers=frozenset({number}),
        origin={"number": number},
    )


def synthetic_pairs(n: int) -> list[Pair]:
    """`n` paires distinctes : juridictions, classes visibles et périodes mélangées."""
    pairs = []
    years = (1995, 2008, 2018, 2023)
    for i in range(n):
        jurisdiction = "cc" if i % 3 else "ce"
        y = 2023 if jurisdiction == "ce" else years[i % 4]
        rules = ("R-O1",) if i % 2 and jurisdiction == "cc" else ()
        formation = "civ. 4e" if rules else ("civ. 1re" if jurisdiction == "cc" else "6e ch.")
        uid = f"r-u{i:05d}"
        if jurisdiction == "cc":
            f_number, r_number = f"{(y - 1) % 100:02d}-1{i // 1000}.{i % 1000:03d}", None
            r_number = f"{(y - 1) % 100:02d}-2{i // 1000}.{i % 1000:03d}"
            r_form = "civ. 1re"
        else:
            f_number, r_number, r_form = f"{400000 + i}", f"{500000 + i}", "6e ch."
        f_row = fake(
            uid, jurisdiction, formation, y, 3, 12, f_number, rules=rules, model=MODELS[i % 3]
        )
        pairs.append(Pair(f_row, real(jurisdiction, r_form, date(y, 3, 13), r_number)))
    return pairs


# --- monde du script `construire` ----------------------------------------------------------


def working_days(start: date, count: int, step: int = 7) -> list[date]:
    out, day = [], start
    while len(out) < count:
        if is_working_day(day):
            out.append(day)
        day += timedelta(days=step)
    return out


class World:
    """Fausses, Judilibre (transport en mémoire) et index du CE cohérents entre eux."""

    def __init__(self, n_cc: int = 120, n_ce: int = 16) -> None:
        self.rows: list[dict] = []
        self.cc_days = working_days(date(2003, 1, 6), n_cc, step=37)
        self.ce_days = working_days(date(2022, 1, 10), n_ce, step=23)
        self.found_day: date | None = None
        self.error_day: date | None = None
        chambers = list(CC_CODES)
        uid = 0
        for i, day in enumerate(self.cc_days):
            uid += 1
            klass = "incoherent" if i % 3 == 0 else "coherent_absent"
            rules = ("R-O1",) if klass == "incoherent" else ()
            formation = "civ. 4e" if rules else chambers[i % len(chambers)]
            number = f"{(day.year - 1) % 100:02d}-1{i % 10}.{900 + i % 100:03d}"
            self.rows.append(
                classement_row(
                    f"r-u{uid:05d}",
                    "cc",
                    formation,
                    day.year,
                    day.month,
                    day.day,
                    number,
                    klass,
                    rules,
                    model=MODELS[i % 3],
                )
            )
        for i, day in enumerate(self.ce_days):
            uid += 1
            formation = list(CE_FORMATIONS)[i % 2]
            self.rows.append(
                classement_row(
                    f"r-u{uid:05d}",
                    "ce",
                    formation,
                    day.year,
                    day.month,
                    day.day,
                    f"{470000 + i}",
                    "coherent_absent",
                    model=MODELS[i % 3],
                )
            )
        # Hors du dénominateur, ou exclues d'office (D2).
        extra = [
            ("cc", "civ. 1re", 2010, 5, 4, "09-10.001", "exists", ()),
            ("cc", "civ. 1re", 2010, 5, 5, "09-10.002", "partial", ()),
            ("cc", "civ. 2e", 1975, 5, 6, "74-10.003", "incoherent", ("R-O1",)),
            ("cc", "civ. 2e", 2027, 5, 11, "26-10.004", "incoherent", ("R-C3",)),
            ("ce", "6e ch.", 2023, 5, 9, "471999", "incoherent", ("R-E3",)),
        ]
        for jur, form, y, m, d, number, klass, rules in extra:
            uid += 1
            self.rows.append(
                classement_row(f"r-u{uid:05d}", jur, form, y, m, d, number, klass, rules)
            )
        self.future_uid = f"r-u{uid - 1:05d}"

    # Arrêts synthétiques d'un jour : deux par chambre, écarts d'année 1 et 2.
    def cc_results(self, day: date) -> list[dict]:
        if not is_working_day(day):
            return []
        out = []
        doy = day.timetuple().tm_yday
        for k, code in enumerate(CC_CODES.values()):
            for gap in (1, 2):
                number = f"{(day.year - gap) % 100:02d}-{20 + 10 * gap + k}.{doy:03d}"
                out.append(
                    {
                        "id": f"cc-{day.isoformat()}-{code}-{gap}",
                        "jurisdiction": "cc",
                        "chamber": code,
                        "number": number,
                        "numbers": [number],
                        "decision_date": day.isoformat(),
                        "type": "arret",
                        "text": "TEXTE-INTEGRAL-SECRET",
                    }
                )
        if day == self.found_day:
            row = next(
                r
                for r in self.rows
                if (r["year"], r["month"], r["day"]) == (day.year, day.month, day.day)
            )
            code = CC_CODES.get(row["formation"], "civ1")
            out.append(
                {
                    "id": "cc-found",
                    "jurisdiction": "cc",
                    "chamber": code,
                    "number": row["number"],
                    "numbers": [row["number"]],
                    "decision_date": day.isoformat(),
                    "type": "arret",
                }
            )
        return out

    def transport(self, url: str, headers):
        assert url.startswith(BASE_URL)
        parts = urlsplit(url)
        path = parts.path[len(urlsplit(BASE_URL).path) :]
        params = dict(parse_qsl(parts.query))
        if path == "/search":
            data = {"total": 0, "next_page": None, "relaxed": True, "results": []}
        elif path == "/scan":
            day = date.fromisoformat(params["date_start"])
            if day == self.error_day:
                return 500, {"x-rate-limit": RATE}, b"{}"
            results = self.cc_results(day)
            data = {"total": len(results), "next_batch": None, "results": results}
        else:
            raise AssertionError(f"route absente : {path}")
        return 200, {"x-rate-limit": RATE}, json.dumps(data).encode("utf-8")

    def ce_records(self) -> list[dict]:
        records = []
        for day in self.ce_days:
            for offset in range(0, 6):
                current = day + timedelta(days=offset)
                if not is_working_day(current):
                    continue
                for k, text in enumerate(CE_FORMATIONS.values()):
                    number = f"{480000 + current.toordinal() % 9000 * 2 + k}"
                    records.append(
                        {
                            "Numero_Dossier": number,
                            "Date_Lecture": current.isoformat(),
                            "Formation_Jugement": text,
                            "Type_Decision": "Décision",
                            "Date_Mise_Jour": current.isoformat(),
                        }
                    )
        return records


def write_world(world: World, root: Path) -> dict:
    """Écrit pré-étude, porte, index du CE, jeux de S et dépôt git sous `root`."""
    import hashlib

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    pre = root / "pre"
    (pre / "interne").mkdir(parents=True)
    classement = pre / "classement.jsonl"
    classement.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in world.rows), encoding="utf-8"
    )
    extraction = pre / "interne" / "extraction.jsonl"
    extraction.write_text(
        "".join(json.dumps(extraction_row(r), ensure_ascii=False) + "\n" for r in world.rows),
        encoding="utf-8",
    )
    (pre / "resume.json").write_text('{"decision": "comparatif"}\n', encoding="utf-8")
    manifest = {
        "outputs": {
            "classement.jsonl": sha(classement),
            "interne/extraction.jsonl": sha(extraction),
            "resume.json": sha(pre / "resume.json"),
        }
    }
    (pre / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    gate = root / "r_gate.toml"
    gate.write_text(
        'decision = "comparatif"\nbasis = "p_d1"\np = 0.4\nlow = 0.33\nhigh = 0.47\nn = 200\n'
        f'tight = false\nreserves = []\nclassement_sha256 = "{sha(classement)}"\n',
        encoding="utf-8",
    )
    ce = root / "ce_index"
    CeIndex(world.ce_records()).save(ce / "index.jsonl")
    ce_manifest = {"finished_at": "2026-11-06T10:00:00Z", "index_sha256": sha(ce / "index.jsonl")}
    (ce / "manifest.json").write_text(json.dumps(ce_manifest), encoding="utf-8")
    s_root = root / "s"
    s_raw = world.rows[1]["canonical"]  # une fausse égale à un raw de S : exclue (S7)
    real_in_s = world.cc_results(world.cc_days[4])[0]
    s_real = raw_of(
        "cc",
        "civ. 1re",
        world.cc_days[4].year,
        world.cc_days[4].month,
        world.cc_days[4].day,
        real_in_s["number"],
    )
    for task in ("legal_s", "legal_s_reserved"):
        for part in ("data", "heldout"):
            folder = s_root / part / task / ("session" if part == "data" else "eval")
            folder.mkdir(parents=True)
            rows = [
                {"id": f"legal-{part}-1", "raw": s_raw},
                {"id": f"legal-{part}-2", "raw": s_real},
            ]
            (folder / "examples.jsonl").write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
            )
    repo = root / "repo"
    repo.mkdir()
    for args in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", *args], cwd=repo, check=True)
    (repo / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
        cwd=repo,
        check=True,
    )
    return {
        "pre": pre,
        "gate": gate,
        "ce": ce,
        "ce_sha": sha(ce / "manifest.json"),
        "s_root": s_root,
        "repo": repo,
        "out": root / "out",
        "cache": root / "cache",
        "s_raws": {s_raw, s_real},
    }
