"""Rendu Markdown du tableau d'un lot, depuis les lignes de `report.table.build` (sans horloge)."""

from __future__ import annotations

STATUS = {
    "counted": "comptée",
    "replayed": "rejouée",
    "excluded": "écartée",
    "annex": "annexe",
    "kept": "maintenue",
    "pending": "à juger",
}
STATE = {"unfrozen": "-", "error": "inv.", "not_evaluated": "n.é."}
NONE = "—"


def _num(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def pct(value: float | None) -> str:
    return NONE if value is None else _num(value * 100, 1)


def usd(value: float | None) -> str:
    return NONE if value is None else _num(value, 4)


def plain(value: float | None, digits: int = 0) -> str:
    if value is None:
        return NONE
    return _num(value, digits) if digits else f"{round(value):d}"


def mean_sd(mean: float | None, sd: float | None) -> str:
    if mean is None:
        return NONE
    return pct(mean) if sd is None else f"{pct(mean)} ± {pct(sd)}"


def _cell(value: object) -> str:
    text = NONE if value is None or value == "" else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def _attempts(agg: dict) -> str:
    parts = []
    for a in agg["attempts"]:
        value = pct(a["accuracy"]) if a["state"] == "ok" else STATE[a["state"]]
        parts.append(f"t{a['attempt']} {value}")
    return " ; ".join(parts) or NONE


def _accuracy(agg: dict) -> str:
    text = mean_sd(agg["accuracy_mean"], agg["accuracy_sd"])
    if agg["accuracy_range"] and agg["n"] >= 2:
        low, high = agg["accuracy_range"]
        text += f" [{pct(low)} ; {pct(high)}]"
    return text


def _per_seed(row: dict) -> str:
    parts = []
    for entry in row["per_seed"]:
        acc = entry["accuracy"]
        value = f"{acc['correct']}/{acc['n']}" if acc else "n.é."
        parts.append(f"s{entry['seed']} {value}")
    return " ; ".join(parts) or NONE


def _cases(data: dict) -> str:
    targets = data["targets"]
    headers = [
        "Tâche",
        "Méthode",
        "Taille cible",
        "Modèle",
        "Config",
        "Gelées (k/n)",
        "Exactitude réservée, avant décisions (tentatives comptées ; moy. ± é.-t. [étendue])",
        "Exactitude réservée après décisions",
        "Gelées seules (moy.)",
        "Par tentative",
        "Vraies",
        "Fausses connues",
        "Tenues à l'écart (HD)",
        *[f"Croisée → {t}" for t in targets],
        "Lisibilité",
        "Paramètres (nominal, médiane)",
        "Taille effective (script, zlib ; médianes)",
        "Passes (moy.)",
        "Facturé ($, somme ; médiane)",
        "Équivalent API ($, somme ; médiane)",
        "Durée (min, médiane)",
        "Drapeaux (séances)",
        "Rejouées (n ; facturé)",
    ]
    rows = []
    for c in data["cases"]:
        a, k = c["all_sessions"], c["after_decisions"]
        rows.append(
            [
                c["task"],
                c["method"],
                c["size_target"],
                c["model"],
                c["config"],
                f"{k['frozen']}/{k['n']}",
                _accuracy(a),
                _accuracy(k),
                pct(k["accuracy_frozen_mean"]),
                _attempts(k),
                pct(k["groups"]["real"]),
                pct(k["groups"]["fake_known"]),
                pct(k["groups"]["held_out"]),
                *[pct(k["cross"][t]) for t in targets],
                pct(k["legibility"]),
                plain(k["params_nominal"]),
                f"{plain(k['size_script_bytes'])} ; {plain(k['size_weights_zlib'])}",
                plain(k["passes_mean"], 1),
                f"{usd(k['billed_sum'])} ; {usd(k['billed_median'])}",
                f"{usd(k['equiv_sum'])} ; {usd(k['equiv_median'])}",
                plain(k["duration_min_median"], 1),
                k["flagged"],
                f"{c['replayed']['n']} ; {usd(c['replayed']['billed_sum'])}",
            ]
        )
    return table(headers, rows)


def _baselines(data: dict) -> str:
    targets = data["targets"]
    headers = [
        "Tâche",
        "Témoin",
        "Encodeur",
        "Chemin",
        "N",
        "Graines",
        "Exactitude (moy. ± é.-t.)",
        "Par graine (correct/n)",
        "Vraies",
        "Fausses connues",
        "Tenues à l'écart",
        *[f"Croisée → {t}" for t in targets],
        "Statut",
    ]
    rows = [
        [
            b["task"],
            b["baseline"],
            b["encoder"],
            b["chemin"],
            b["n"],
            ", ".join(str(s) for s in b["seeds"]),
            mean_sd(b["accuracy_mean"], b["accuracy_sd"]),
            _per_seed(b),
            pct(b["groups"]["real"]),
            pct(b["groups"]["fake_known"]),
            pct(b["groups"]["held_out"]),
            *[pct(b["cross"][t]) for t in targets],
            ", ".join(STATUS[s] for s in b["status"]),
        ]
        for b in data["baselines"]
    ]
    return table(headers, rows)


def _same(data: dict) -> str:
    headers = [
        "Séance d'origine",
        "N",
        "Exactitude de la séance",
        "Réentraîné (moy. ± é.-t.)",
        "Par graine (correct/n)",
        "Écart",
    ]
    rows = [
        [
            r["session"],
            r["n"],
            pct(r["session_accuracy"]),
            mean_sd(r["retrained_mean"], r["retrained_sd"]),
            _per_seed(r)
            + (
                " (hors moyenne : " + ", ".join(f"s{x}" for x in r["removed_seeds"]) + ")"
                if r.get("removed_seeds")
                else ""
            ),
            pct(r["gap"]),
        ]
        for r in data["same_network"]
    ]
    return table(headers, rows)


def _cross(data: dict) -> str:
    headers = ["Dossier", "Tâche écrite", "Cible", "Exactitude", "Vraies", "Fausses", "HD"]
    rows = [
        [
            r["path"],
            r["written_task"],
            r["target"],
            "inv." if r["error"] else pct(r["accuracy"]),
            pct(r["real"]),
            pct(r["fake_known"]),
            pct(r["held_out"]),
        ]
        for r in data["cross"]
    ]
    return table(headers, rows)


def _flags(data: dict) -> str:
    headers = ["Séance", "script_run (signalés / total)", "Kinds (count)", "Exemples", "Jugement"]
    rows = []
    for r in data["flags"]:
        j = r["judgement"]
        if j:
            judgement = f"{STATUS[j['status']]}, {j['date']} : {j['reason']}"
        else:
            judgement = "à juger" if r["to_judge"] else "hors agrégats"
        rows.append(
            [
                r["session"],
                f"{r['flagged_script_runs']} / {r['script_runs']}",
                ", ".join(f"{k} ({v})" for k, v in r["kinds"].items()),
                ", ".join(r["example_ids"]),
                judgement,
            ]
        )
    return table(headers, rows)


def _sessions(data: dict) -> str:
    headers = [
        "Séance",
        "Case",
        "Tentative",
        "Graine",
        "Statut",
        "Fin",
        "Détail",
        "Passes",
        "Tours",
        "Refus",
        "Jetons (entrée, sortie, cache lu, cache écrit)",
        "Facturé",
        "Équivalent API",
        "Durée (min)",
        "tree_sha256",
        "Exactitude",
    ]
    rows = []
    for r in data["sessions"]:
        c = r["costs"]
        tokens = (
            f"{c['input_tokens']}, {c['output_tokens']}, "
            f"{c['cache_read_tokens']}, {c['cache_write_tokens']}"
        )
        accuracy = STATE.get(r["state"], "")
        if r["state"] == "ok":
            counts = r["accuracy_counts"]
            accuracy = f"{counts['correct']}/{counts['n']} ({pct(r['accuracy'])})"
        rows.append(
            [
                r["session"],
                r["case"],
                r["attempt"],
                r["seed"],
                STATUS[r["status"]],
                r["end"],
                r["detail"],
                r["passes"],
                r["turns"],
                ", ".join(r["refusals"]),
                tokens,
                usd(c["billed_usd"]),
                usd(c["cost_equiv_usd"]),
                plain(c["duration_s"] / 60, 1),
                (r["tree_sha256"] or "")[:12],
                accuracy,
            ]
        )
    return table(headers, rows)


def _costs(data: dict) -> str:
    c = data["costs"]
    rows = [
        [r["model"], r["driver"], usd(r["billed_usd"]), usd(r["cost_equiv_usd"])]
        for r in c["by_model"]
    ]
    rows.append(["**Total**", "", usd(c["billed_usd"]), usd(c["cost_equiv_usd"])])
    rows.append(
        ["Registre (closed)", "", usd(c["ledger_billed_usd"]), usd(c["ledger_cost_equiv_usd"])]
    )
    rows.append(
        ["Écart (journaux − registre)", "", usd(c["gap_billed_usd"]), usd(c["gap_cost_equiv_usd"])]
    )
    text = table(["Modèle", "Pilote", "Facturé ($)", "Équivalent API ($)"], rows)
    cap = c["lot_cap_usd"]
    if cap:
        text += (
            f"\nFacturé du lot : {usd(c['billed_usd'])} $ sur un plafond de {usd(cap)} $ "
            f"({pct(c['billed_share_of_cap'])} %) ; l'équivalent API n'est pas plafonné.\n"
        )
    text += f"\nSéances absentes du registre : {len(c['only_in_journals'])}"
    if c["only_in_journals"]:
        text += " (" + ", ".join(c["only_in_journals"]) + ")"
    text += f".\n\nLignes du registre sans journal : {len(c['only_in_ledger'])}"
    if c["only_in_ledger"]:
        text += " (" + ", ".join(c["only_in_ledger"]) + ")"
    return text + ".\n"


def _configs(data: dict) -> str:
    keys = ["driver", "provider", "effort", "max_tokens", "pass_budget", "sampling"]
    headers = ["Config", *keys, "protocol_sha256", "system_prompt_sha256"]
    rows = [
        [
            cid,
            *[f if not isinstance(f, dict) else str(f) for f in (fields[k] for k in keys)],
            (fields["protocol_sha256"] or "")[:12],
            (fields["system_prompt_sha256"] or "")[:12],
        ]
        for cid, fields in data["configs"].items()
    ]
    return table(headers, rows)


def _decisions(data: dict) -> str:
    if not data["decisions"]:
        return "Aucune décision.\n"
    headers = ["Portée", "Statut", "Audit", "Date", "Motif", "Référence", "Artefacts visés"]
    rows = [
        [
            d["scope"],
            STATUS[d["status"]],
            d["audit"],
            d["date"],
            d["reason"],
            d["ref"],
            d["matched"],
        ]
        for d in data["decisions"]
    ]
    return table(headers, rows)


def _bullets(items: list[str]) -> str:
    return "".join(f"- {item}\n" for item in items) if items else "Aucun.\n"


def markdown(data: dict) -> str:
    inputs = data["inputs"]
    lot = data["lot"]
    removed = [f"{r['path']} : {STATUS[r['status']]} ({r['reason']})" for r in data["removed"]]
    parts = [
        f"# Mesures du lot {lot}\n",
        f"Généré par `nnww table --lot {lot}` ; ne pas éditer.\n",
        f"Entrées lues : {inputs['journals']} journaux, {inputs['run_json']} `run.json`, "
        f"{inputs['eval_json']} `eval*.json` ; empreinte des entrées `{inputs['fingerprint']}`.\n",
        "Exactitude principale : une tentative non gelée ou en erreur compte 0 ; « Gelées seules » "
        "porte sur les tentatives gelées évaluées (k/n). Pourcentages à 1 décimale.\n",
        "## 1. Cases\n",
        _cases(data),
        "## 2. Témoins C et F\n",
        _baselines(data),
        "## 3. C « même réseau »\n",
        _same(data),
        "## 4. Évaluations croisées\n",
        _cross(data),
        "## 5. Drapeaux d'audit par séance\n",
        _flags(data),
        "## 6. Séances\n",
        _sessions(data),
        "## 7. Coûts du lot et registre\n",
        _costs(data),
        "## 8. Configurations\n",
        _configs(data),
        "## 9. Décisions appliquées\n",
        _decisions(data),
        "### Retirées des agrégats\n",
        _bullets(removed),
        "### Non évalués\n",
        _bullets(data["not_evaluated"]),
        "### Avertissements\n",
        _bullets(data["warnings"]),
    ]
    return "\n".join(parts)
