"""Agrégation et rendu du tableau d'un lot (`nnww table`, CAP-12) : mêmes entrées, mêmes octets.

Règles (spec 1-14 et décisions Q6, Q7, Q12) :

- case de séance : `(tâche, méthode, size_target, modèle, config)` ;
- tentative : la dernière séance gelée (`open.ts`) d'une tentative compte si elle existe, sinon
  la dernière ; les autres sont « rejouées » ;
- exactitude principale : moyenne sur les tentatives comptées, une tentative non gelée (échec,
  erreur, gel invalide) ou en erreur d'évaluation comptant 0 ; secondaire : moyenne sur les
  seules gelées évaluées, avec `k/n` ;
- chaque case porte l'agrégat de toutes les séances et l'agrégat après décisions.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from nn_weight_writing.budget import ledger as ledger_mod
from nn_weight_writing.report.collect import Baseline, Evaluation, Lot, Session, collect, config_id
from nn_weight_writing.report.decisions import Decision, DecisionsError, read_decisions


@dataclass
class Table:
    data: dict
    markdown: str
    issues: list[str]  # points qui font échouer --strict


# --- valeurs -----------------------------------------------------------------------------------


def _rate(entry: dict | None) -> float | None:
    if not entry or not entry.get("n"):
        return None
    return round(entry["correct"] / entry["n"], 6)


def _groups(metrics: dict) -> dict[str, dict | None]:
    """Vraies, fausses connues, tenues à l'écart (comptes entiers)."""
    by_label = metrics.get("by_label") or {}
    ood = metrics.get("ood")
    fake = by_label.get("fake")
    known = None
    if fake is not None:
        known = dict(fake)
        if ood:
            known = {"correct": fake["correct"] - ood["correct"], "n": fake["n"] - ood["n"]}
    return {"real": by_label.get("real"), "fake_known": known, "held_out": ood}


def _state(evaluation: Evaluation | None, frozen: bool) -> str:
    if not frozen:
        return "unfrozen"
    if evaluation is None or not evaluation.evaluated:
        return "not_evaluated"
    if evaluation.metrics.get("error"):
        return "error"
    return "ok"


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 6) if values else None


def _stdev(values: list[float]) -> float | None:
    return round(statistics.stdev(values), 6) if len(values) >= 2 else None


def _median(values: list[float]) -> float | None:
    return round(float(statistics.median(values)), 6) if values else None


# --- séances -----------------------------------------------------------------------------------


def _case_key(s: Session) -> tuple:
    o = s.open
    return (o["task"], o["method"], o.get("size_target"), o["model"], s.config)


def _counted(sessions: list[Session]) -> set[str]:
    by_attempt: dict[tuple, list[Session]] = defaultdict(list)
    for s in sessions:
        by_attempt[(_case_key(s), s.open["attempt"])].append(s)
    counted = set()
    for group in by_attempt.values():
        frozen = [s for s in group if s.frozen]
        pick = max(frozen or group, key=lambda s: (s.open["ts"], s.id))
        counted.add(pick.id)
    return counted


def _decision_for(
    ident: str, task: str, config: str | None, chemin: str | None, by_id, groups
) -> Decision | None:
    """Décision d'une séance (`chemin` None) ou d'un témoin (`config` None)."""
    if ident in by_id:
        return by_id[ident]
    for group in groups:
        if group.task is not None and group.task != task:
            continue
        if group.config is not None and group.config != config:
            continue
        if group.path is not None and group.path != chemin:
            continue
        return group
    return None


def _aggregate(sessions: list[Session], targets: list[str]) -> dict:
    """Agrégat d'une liste de tentatives comptées."""
    main: list[float] = []
    ok: list[float] = []
    pending = False
    attempts = []
    groups: dict[str, list[float]] = defaultdict(list)
    cross: dict[str, list[float]] = defaultdict(list)
    legibility: list[float] = []
    for s in sorted(sessions, key=lambda s: (s.open["attempt"], s.id)):
        state = _state(s.native, s.frozen)
        value = None
        if state == "ok":
            value = _rate(s.native.metrics["accuracy"])
            ok.append(value)
            for name, entry in _groups(s.native.metrics).items():
                if _rate(entry) is not None:
                    groups[name].append(_rate(entry))
            ablation = s.native.metrics.get("ablation")
            if ablation:
                legibility.append(ablation["legibility"]["rate"])
        if state == "not_evaluated":
            pending = True
        else:
            main.append(value if value is not None else 0.0)
        for target in targets:
            evaluation = s.cross.get(target)
            if evaluation and not evaluation.metrics.get("error"):
                cross[target].append(_rate(evaluation.metrics["accuracy"]))
        attempts.append({"attempt": s.open["attempt"], "state": state, "accuracy": value})
    frozen = [s for s in sessions if s.frozen]
    return {
        "n": len(sessions),
        "frozen": len(frozen),
        "evaluated_ok": len(ok),
        "accuracy_mean": None if pending else _mean(main),
        "accuracy_sd": None if pending else _stdev(main),
        "accuracy_range": None if pending or not main else [min(main), max(main)],
        "accuracy_frozen_mean": _mean(ok),
        "attempts": attempts,
        "groups": {name: _mean(groups[name]) for name in ("real", "fake_known", "held_out")},
        "cross": {t: _mean(cross[t]) for t in targets},
        "legibility": _mean(legibility),
        "params_nominal": _median([s.freeze["size_nominal"] for s in frozen]),
        "size_script_bytes": _median([s.freeze["size_script_bytes"] for s in frozen]),
        "size_weights_zlib": _median([s.freeze["size_weights_zlib"] for s in frozen]),
        "passes_mean": _mean([float((s.end or {}).get("passes_used") or 0) for s in sessions]),
        "billed_sum": round(sum(s.costs["billed_usd"] for s in sessions), 6),
        "billed_median": _median([s.costs["billed_usd"] for s in sessions]),
        "equiv_sum": round(sum(s.costs["cost_equiv_usd"] for s in sessions), 6),
        "equiv_median": _median([s.costs["cost_equiv_usd"] for s in sessions]),
        "duration_min_median": _median([s.costs["duration_s"] / 60 for s in sessions]),
        "flagged": sum(1 for s in sessions if s.flags),
    }


# --- témoins -----------------------------------------------------------------------------------


def _seed_value(b: Baseline) -> dict:
    """Exactitude d'une graine en comptes entiers (`None` : non évaluée ou en erreur)."""
    ok = b.native and b.native.evaluated and not b.native.metrics.get("error")
    return {"seed": b.run["seed"], "accuracy": b.native.metrics["accuracy"] if ok else None}


def _baseline_rows(baselines: list[Baseline], targets: list[str], status_of) -> list[dict]:
    keyed: dict[tuple, list[Baseline]] = defaultdict(list)
    for b in baselines:
        if b.retrained_from:
            continue
        keyed[
            (b.run.get("task", ""), b.run["baseline"], b.encoder or "", b.run["n"], b.chemin)
        ].append(b)
    rows = []
    for key in sorted(keyed):
        members = sorted(keyed[key], key=lambda b: b.run["seed"])
        rates, groups, cross = [], defaultdict(list), defaultdict(list)
        for b in members:
            if b.native and b.native.evaluated and not b.native.metrics.get("error"):
                rates.append(_rate(b.native.metrics["accuracy"]))
                for name, entry in _groups(b.native.metrics).items():
                    if _rate(entry) is not None:
                        groups[name].append(_rate(entry))
            for t in targets:
                ev = b.cross.get(t)
                if ev and not ev.metrics.get("error"):
                    cross[t].append(_rate(ev.metrics["accuracy"]))
        statuses = sorted({status_of(b) for b in members})
        rows.append(
            {
                "task": key[0],
                "baseline": key[1],
                "encoder": key[2],
                "n": key[3],
                "chemin": key[4],
                "seeds": [b.run["seed"] for b in members],
                "per_seed": [_seed_value(b) for b in members],
                "evaluated": len(rates),
                "accuracy_mean": _mean(rates),
                "accuracy_sd": _stdev(rates),
                "groups": {g: _mean(groups[g]) for g in ("real", "fake_known", "held_out")},
                "cross": {t: _mean(cross[t]) for t in targets},
                "status": statuses,
            }
        )
    return rows


# --- construction ------------------------------------------------------------------------------


def _ledger_rows(path: Path | None, lot: int, lot_data: Lot) -> list:
    if path is None or not Path(path).is_file():
        return []
    lot_data.inputs.read_bytes(Path(path), f"ledger:{Path(path).name}")
    return [r for r in ledger_mod.read(Path(path)) if r.lot == lot and r.status == "closed"]


def _lot_cap(lot: int) -> float | None:
    try:
        from nn_weight_writing.config import load_protocol

        return load_protocol().lot_cap_usd(lot)
    except KeyError, ValueError, OSError:
        return None


def build(
    root: Path, lot: int, decisions_path: Path | None = None, ledger_path: Path | None = None
) -> Table:
    lot_dir = Path(root) / "runs" / str(lot)
    data = collect(lot_dir)
    by_id, groups = ({}, [])
    if decisions_path is not None and Path(decisions_path).is_file():
        data.inputs.read_bytes(Path(decisions_path), f"decisions:{Path(decisions_path).name}")
        by_id, groups = read_decisions(Path(decisions_path))
    known = {s.id for s in data.sessions} | {b.id for b in data.baselines}
    unknown = sorted(set(by_id) - known)
    if unknown:
        raise DecisionsError(f"décisions : identifiants inconnus des artefacts {unknown}")
    matched: dict[str, int] = defaultdict(int)

    def decision(ident: str, task: str, config: str | None, chemin: str | None):
        found = _decision_for(ident, task, config, chemin, by_id, groups)
        if found is not None:
            matched[found.scope] += 1
        return found

    session_decisions = {
        s.id: decision(s.id, s.open["task"], s.config, None) for s in data.sessions
    }
    baseline_decisions = {
        b.id: decision(b.id, b.run.get("task", ""), None, b.chemin) for b in data.baselines
    }
    for group in groups:
        if not matched.get(group.scope):
            raise DecisionsError(f"décisions : {group.scope} ne vise aucun artefact")

    counted = _counted(data.sessions)

    def status(s: Session) -> str:
        d = session_decisions[s.id]
        if d is not None and d.removes:
            return d.status
        return "counted" if s.id in counted else "replayed"

    def baseline_status(b: Baseline) -> str:
        d = baseline_decisions[b.id]
        return d.status if d is not None and d.removes else "counted"

    targets = sorted(
        {t for s in data.sessions for t in s.cross} | {t for b in data.baselines for t in b.cross}
    )
    issues: list[str] = []
    warnings = list(data.warnings)

    # Cases.
    cases: dict[tuple, list[Session]] = defaultdict(list)
    for s in data.sessions:
        cases[_case_key(s)].append(s)
    case_rows = []
    for key in sorted(cases, key=lambda k: (k[0], k[1], k[2] or 0, k[3], k[4])):
        members = cases[key]
        all_counted = [s for s in members if s.id in counted]
        kept = [s for s in members if status(s) == "counted"]
        replayed = [s for s in members if s.id not in counted]
        heldouts = {
            s.native.target.get("examples_sha256") for s in kept if s.native and s.native.evaluated
        }
        if len(heldouts) > 1:
            warnings.append(f"case {'/'.join(map(str, key))} : jeux réservés différents")
        case_rows.append(
            {
                "task": key[0],
                "method": key[1],
                "size_target": key[2],
                "model": key[3],
                "config": key[4],
                "all_sessions": _aggregate(all_counted, targets),
                "after_decisions": _aggregate(kept, targets),
                "replayed": {
                    "n": len(replayed),
                    "billed_sum": round(sum(s.costs["billed_usd"] for s in replayed), 6),
                },
            }
        )

    # Témoins et même réseau.
    baseline_rows = _baseline_rows(data.baselines, targets, baseline_status)
    sessions_by_id = {s.id: s for s in data.sessions}
    origins: dict[str, list[Baseline]] = defaultdict(list)
    for b in data.baselines:
        if b.retrained_from:
            origins[b.retrained_from].append(b)
    same_rows = []
    for origin in sorted(origins):
        members = sorted(origins[origin], key=lambda b: b.run["seed"])
        rates = [
            _rate(b.native.metrics["accuracy"])
            for b in members
            if b.native and b.native.evaluated and not b.native.metrics.get("error")
        ]
        source = sessions_by_id.get(origin)
        session_rate = None
        if source and _state(source.native, source.frozen) == "ok":
            session_rate = _rate(source.native.metrics["accuracy"])
        mean = _mean(rates)
        same_rows.append(
            {
                "session": origin,
                "n": members[0].run["n"],
                "session_accuracy": session_rate,
                "retrained_mean": mean,
                "retrained_sd": _stdev(rates),
                "seeds": [b.run["seed"] for b in members],
                "per_seed": [_seed_value(b) for b in members],
                "gap": None
                if mean is None or session_rate is None
                else round(mean - session_rate, 6),
            }
        )

    # Évaluations croisées.
    cross_rows = []
    for owner in [*data.sessions, *data.baselines]:
        for target, ev in sorted(owner.cross.items()):
            groups_ = _groups(ev.metrics) if not ev.metrics.get("error") else {}
            cross_rows.append(
                {
                    "path": owner.path,
                    "written_task": ev.target.get("written_task"),
                    "target": target,
                    "accuracy": _rate(ev.metrics.get("accuracy")),
                    "error": ev.metrics.get("error"),
                    "real": _rate(groups_.get("real")),
                    "fake_known": _rate(groups_.get("fake_known")),
                    "held_out": _rate(groups_.get("held_out")),
                }
            )
    cross_rows.sort(key=lambda r: (r["path"], r["target"]))

    # Drapeaux.
    flag_rows = []
    for s in sorted(data.sessions, key=lambda s: s.id):
        if not s.flags:
            continue
        d = session_decisions[s.id]
        judged = d is not None and d.audit == "judged"
        to_judge = status(s) == "counted" and not judged
        if to_judge:
            issues.append(f"séance à drapeaux à juger : {s.id}")
        example_ids = sorted({i for f in s.flags.values() for i in f["example_ids"]})[:5]
        flag_rows.append(
            {
                "session": s.id,
                "flagged_script_runs": max(f["script_runs"] for f in s.flags.values()),
                "script_runs": s.script_runs,
                "kinds": {k: f["count"] for k, f in s.flags.items()},
                "example_ids": example_ids,
                "judgement": (
                    {"status": d.status, "date": d.date, "reason": d.reason} if judged else None
                ),
                "to_judge": to_judge,
            }
        )

    # Séances.
    session_rows = []
    not_evaluated = []
    for s in sorted(data.sessions, key=lambda s: s.id):
        state = _state(s.native, s.frozen)
        if state == "not_evaluated":
            not_evaluated.append(s.path)
        if s.native and s.native.evaluated and s.freeze:
            if s.native.tree_sha256 != s.freeze.get("tree_sha256"):
                warnings.append(f"{s.path} : eval.json d'un autre gel (tree_sha256)")
        end = s.end or {}
        session_rows.append(
            {
                "session": s.id,
                "case": "/".join(str(v) for v in _case_key(s)),
                "attempt": s.open["attempt"],
                "seed": s.open.get("seed"),
                "status": status(s),
                "end": end.get("reason"),
                "detail": (end.get("detail") or "")[:60],
                "passes": end.get("passes_used"),
                "turns": s.turns,
                "refusals": sorted(set(s.refusals)),
                "costs": s.costs,
                "tree_sha256": (s.freeze or {}).get("tree_sha256"),
                "state": state,
                "accuracy": _rate(s.native.metrics.get("accuracy")) if state == "ok" else None,
                "accuracy_counts": s.native.metrics["accuracy"] if state == "ok" else None,
            }
        )
    for b in sorted(data.baselines, key=lambda b: b.path):
        if not (b.native and b.native.evaluated):
            not_evaluated.append(b.path)
        elif b.native.tree_sha256 != b.run.get("tree_sha256"):
            warnings.append(f"{b.path} : eval.json d'un autre gel (tree_sha256)")

    # Coûts et registre.
    by_model: dict[tuple, dict] = defaultdict(lambda: {"billed_usd": 0.0, "cost_equiv_usd": 0.0})
    for s in data.sessions:
        entry = by_model[(s.open["model"], s.open["driver"])]
        entry["billed_usd"] += s.costs["billed_usd"]
        entry["cost_equiv_usd"] += s.costs["cost_equiv_usd"]
    rows = _ledger_rows(ledger_path, lot, data)
    ledger_by_id: dict[str, object] = {}
    for row in rows:
        ledger_by_id.setdefault(row.session_id, row)
    journal_ids = {s.id for s in data.sessions}
    billed = round(sum(s.costs["billed_usd"] for s in data.sessions), 6)
    equiv = round(sum(s.costs["cost_equiv_usd"] for s in data.sessions), 6)
    ledger_billed = round(sum(r.billed_usd for r in ledger_by_id.values()), 6)
    ledger_equiv = round(sum(r.cost_equiv_usd for r in ledger_by_id.values()), 6)
    cap = _lot_cap(lot)
    costs = {
        "by_model": [
            {
                "model": m,
                "driver": d,
                "billed_usd": round(v["billed_usd"], 6),
                "cost_equiv_usd": round(v["cost_equiv_usd"], 6),
            }
            for (m, d), v in sorted(by_model.items())
        ],
        "billed_usd": billed,
        "cost_equiv_usd": equiv,
        "lot_cap_usd": cap,
        "billed_share_of_cap": None if not cap else round(billed / cap, 6),
        "ledger_billed_usd": ledger_billed,
        "ledger_cost_equiv_usd": ledger_equiv,
        "gap_billed_usd": round(billed - ledger_billed, 6),
        "gap_cost_equiv_usd": round(equiv - ledger_equiv, 6),
        "only_in_journals": sorted(journal_ids - set(ledger_by_id)),
        "only_in_ledger": sorted(set(ledger_by_id) - journal_ids),
    }

    configs = {}
    for s in data.sessions:
        cid, fields = config_id(s.open)
        configs[cid] = fields

    decisions_rows = [
        {
            "scope": d.scope,
            "status": d.status,
            "audit": d.audit,
            "date": d.date,
            "reason": d.reason,
            "ref": d.ref,
            "matched": matched.get(d.scope, 0),
        }
        for d in sorted([*by_id.values(), *groups], key=lambda d: d.scope)
    ]
    for d in decisions_rows:
        if d["status"] == "pending":
            issues.append(f"décision à juger : {d['scope']}")
    removed = [
        {"path": s.path, "status": status(s), "reason": session_decisions[s.id].reason}
        for s in sorted(data.sessions, key=lambda s: s.id)
        if session_decisions[s.id] is not None and session_decisions[s.id].removes
    ] + [
        {"path": b.path, "status": baseline_status(b), "reason": baseline_decisions[b.id].reason}
        for b in sorted(data.baselines, key=lambda b: b.path)
        if baseline_status(b) != "counted"
    ]
    issues += [f"non évalué : {p}" for p in not_evaluated]
    issues += [f"avertissement : {w}" for w in warnings]

    labels = sorted(data.inputs.files)
    result = {
        "lot": lot,
        "inputs": {
            "journals": sum(1 for p in labels if p.endswith("/journal.jsonl")),
            "run_json": sum(1 for p in labels if p.endswith("/run.json")),
            "eval_json": sum(1 for p in labels if p.rsplit("/", 1)[-1].startswith("eval")),
            "fingerprint": data.inputs.fingerprint(),
        },
        "targets": targets,
        "cases": case_rows,
        "baselines": baseline_rows,
        "same_network": same_rows,
        "cross": cross_rows,
        "flags": flag_rows,
        "sessions": session_rows,
        "costs": costs,
        "configs": dict(sorted(configs.items())),
        "decisions": decisions_rows,
        "removed": removed,
        "not_evaluated": sorted(not_evaluated),
        "warnings": sorted(warnings),
    }
    from nn_weight_writing.report.render import markdown

    return Table(result, markdown(result), issues)


def write(table: Table, out_dir: Path, lot: int) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"lot{lot}.md"
    js = out_dir / f"lot{lot}.json"
    md.write_bytes(table.markdown.encode("utf-8"))
    payload = json.dumps(table.data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    js.write_bytes(payload.encode("utf-8"))
    return md, js
