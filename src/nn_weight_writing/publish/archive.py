"""Assemblage déterministe des archives d'un lot (AD-18, R2) : liste blanche, puis contrôles,
puis écriture, seulement si aucun contrôle ne refuse.

`runs-lot<N>.tar.gz` : sous `runs/<N>/`, pour chaque séance `journal.jsonl`, `system_prompt.md`,
`frozen/**`, `eval.json`, `eval-cross-*.json` ; pour chaque témoin (`**/train/<run_id>/`)
`run.json`, `frozen/**`, `eval*.json` ; plus `runs/<N>/SHA256SUMS`. `r-lot<N>.tar.gz` (si
`r_republish` et un jeu de `r_tasks` sous `data/` ou `heldout/`) : `examples.jsonl`,
`labels.jsonl`, `dataset.json`, `sources.jsonl` de chaque jeu, plus `SHA256SUMS`.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from dataclasses import dataclass, field
from pathlib import Path

from nn_weight_writing.evaluation.schema import (
    EVAL_CROSS_PREFIX,
    EVAL_FILE,
    FROZEN_DIR,
    JOURNAL_FILE,
    RUN_FILE,
)
from nn_weight_writing.journal.reader import JournalError, read_records
from nn_weight_writing.publish.checks import (
    PublishRefusalCode,
    Rules,
    Violation,
    check_member,
    check_notice,
    check_sources,
    example_ids,
    extraction_date,
    is_linked,
    link_violation,
)

SYSTEM_PROMPT_FILE = "system_prompt.md"
SUMS_FILE = "SHA256SUMS"
R_FILES = ("examples.jsonl", "labels.jsonl", "dataset.json", "sources.jsonl")


def runs_archive(lot: int) -> str:
    return f"runs-lot{lot}.tar.gz"


def r_archive(lot: int) -> str:
    return f"r-lot{lot}.tar.gz"


@dataclass
class Plan:
    lot: int
    runs: dict[str, bytes] = field(default_factory=dict)
    r: dict[str, bytes] | None = None
    r_status: str = ""
    ignored: list[str] = field(default_factory=list)
    sessions: int = 0
    baselines: int = 0
    violations: list[Violation] = field(default_factory=list)


def _session_task(journal: Path) -> str:
    """`task` du premier événement `open` ; journal illisible : lu ligne à ligne."""
    try:
        for record in read_records(journal):
            if record.get("type") == "open":
                return record.get("task") or ""
        return ""
    except JournalError, ValueError, KeyError:
        pass
    with open(journal, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and record.get("type") == "open":
                task = record.get("task")
                return task if isinstance(task, str) else ""
    return ""


def _json_task(data: bytes, *keys: str) -> set[str]:
    try:
        value = json.loads(data)
    except ValueError:
        return set()
    for key in keys[:-1]:
        value = value.get(key, {}) if isinstance(value, dict) else {}
    if not isinstance(value, dict):
        return set()
    return {value.get(keys[-1]) or ""}


def _eval_tasks(data: bytes) -> set[str]:
    return _json_task(data, "target", "task") | _json_task(data, "target", "written_task")


def _dir_members(run_dir: Path, names: tuple[str, ...]) -> list[Path]:
    files = [run_dir / name for name in names if (run_dir / name).is_file()]
    files += sorted(
        p
        for p in run_dir.glob("*.json")
        if p.name == EVAL_FILE or p.name.startswith(EVAL_CROSS_PREFIX)
    )
    files += sorted(p for p in (run_dir / FROZEN_DIR).rglob("*") if p.is_file())
    return sorted(set(files))


def collect_runs(root: Path, lot: int, r_tasks: frozenset[str]) -> tuple[Plan, set[str]]:
    """Membres de l'archive des runs (liste blanche) et ceux qui sont des artefacts de R."""
    lot_dir = Path(root) / "runs" / str(lot)
    if not lot_dir.is_dir():
        raise FileNotFoundError(f"{lot_dir} : dossier du lot introuvable")
    plan = Plan(lot)
    r_members: set[str] = set()
    prefix = f"runs/{lot}/"

    def add(files: list[Path], is_r: bool) -> None:
        for path in files:
            name = prefix + path.relative_to(lot_dir).as_posix()
            if is_linked(path, lot_dir):  # un lien pourrait viser `.env` ou le réservé
                plan.violations.append(link_violation(name))
                plan.runs[name] = b""
                continue
            data = path.read_bytes()
            plan.runs[name] = data
            if is_r or (path.name.startswith("eval") and _eval_tasks(data) & r_tasks):
                r_members.add(name)

    for run_dir in sorted(p for p in lot_dir.iterdir() if (p / JOURNAL_FILE).is_file()):
        plan.sessions += 1
        task = _session_task(run_dir / JOURNAL_FILE)
        add(_dir_members(run_dir, (JOURNAL_FILE, SYSTEM_PROMPT_FILE)), task in r_tasks)
    for run_dir in sorted(p.parent for p in lot_dir.glob(f"**/train/*/{RUN_FILE}")):
        plan.baselines += 1
        tasks = _json_task((run_dir / RUN_FILE).read_bytes(), "task")
        add(_dir_members(run_dir, (RUN_FILE,)), bool(tasks & r_tasks))
    plan.ignored = sorted(
        prefix + p.relative_to(lot_dir).as_posix()
        for p in lot_dir.rglob("*")
        if p.is_file() and prefix + p.relative_to(lot_dir).as_posix() not in plan.runs
    )
    return plan, r_members


def _r_datasets(root: Path, r_tasks: frozenset[str]) -> list[tuple[str, Path]]:
    found = []
    for task in sorted(r_tasks):
        for base in ("data", "heldout"):
            directory = Path(root) / base / task
            if directory.is_dir():
                found += [
                    (f"{base}/{task}/{d.name}", d)
                    for d in sorted(directory.iterdir())
                    if d.is_dir()
                ]
    return found


def plan(
    root: Path,
    lot: int,
    out: Path,
    rules: Rules,
    notice_path: Path,
) -> Plan:
    """Toutes les listes et tous les contrôles, sans aucune écriture."""
    root = Path(root)
    result, r_members = collect_runs(root, lot, rules.r_tasks)
    found = result.violations
    if rules.reserved is None:
        found.append(Violation("heldout/", PublishRefusalCode.NO_HELDOUT, "aucun jeu réservé"))
    for name, data in sorted(result.runs.items()):
        found += check_member(name, data, rules)
    if not rules.r_republish:
        found += [
            Violation(name, PublishRefusalCode.R_WITHOUT_REPUBLISH, "artefact de R")
            for name in sorted(r_members)
        ]
    datasets = _r_datasets(root, rules.r_tasks)
    if not rules.r_republish:
        result.r_status = "non construite : r_republish n'est pas true"
    elif not datasets:
        result.r_status = "non construite : aucun jeu de r_tasks sous data/ ni heldout/"
    else:
        result.r, dates = {}, []
        for label, directory in datasets:
            for name in R_FILES:
                if is_linked(directory / name, Path(root)):
                    found.append(link_violation(f"{label}/{name}"))
                elif (directory / name).is_file():
                    result.r[f"{label}/{name}"] = (directory / name).read_bytes()
            examples = result.r.get(f"{label}/examples.jsonl")
            ids = None
            if examples is not None:
                ids = example_ids(examples)
            found += check_sources(
                f"{label}/sources.jsonl", result.r.get(f"{label}/sources.jsonl"), ids
            )
            meta = result.r.get(f"{label}/dataset.json")
            dates.append(
                (f"{label}/dataset.json", extraction_date(json.loads(meta)) if meta else None)
            )
        for name, data in sorted(result.r.items()):
            found += check_member(name, data, rules, reserved=False, strict=True)
        notice = notice_path.read_text("utf-8") if notice_path.is_file() else None
        found += check_notice(str(notice_path), notice, dates)
        result.r_status = f"construite ({len(datasets)} jeux)"
    out = Path(out)
    for name in (runs_archive(lot), r_archive(lot), SUMS_FILE):
        if (out / name).exists():
            found.append(
                Violation(str(out / name), PublishRefusalCode.OUTPUT_EXISTS, "existe déjà")
            )
    return result


def with_sums(members: dict[str, bytes], sums_name: str) -> dict[str, bytes]:
    lines = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(members.items())
    )
    return {**members, sums_name: lines.encode("utf-8")}


def tar_gz(members: dict[str, bytes]) -> bytes:
    """Archive reproductible : membres triés, `mtime = 0`, uid et gid nuls, mode 0644."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name in sorted(members):
            data = members[name]
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    packed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=packed, mtime=0) as handle:
        handle.write(raw.getvalue())
    return packed.getvalue()


def write(result: Plan, out: Path) -> list[Path]:
    """Écrit les archives et `<out>/SHA256SUMS` ; à n'appeler que sans violation."""
    if result.violations:
        raise ValueError("publication refusée : rien n'est écrit")
    archives = {
        runs_archive(result.lot): tar_gz(with_sums(result.runs, f"runs/{result.lot}/{SUMS_FILE}"))
    }
    if result.r is not None:
        archives[r_archive(result.lot)] = tar_gz(with_sums(result.r, SUMS_FILE))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, data in sorted(archives.items()):
        with open(out / name, "xb") as handle:
            handle.write(data)
        written.append(out / name)
    sums = "".join(f"{hashlib.sha256(d).hexdigest()}  {n}\n" for n, d in sorted(archives.items()))
    with open(out / SUMS_FILE, "xb") as handle:
        handle.write(sums.encode("utf-8"))
    return [*written, out / SUMS_FILE]
