"""Fichier de décisions d'un lot (`docs/mesures/decisions-lot<N>.toml`, décision Q6 de 1-14).

Seule entrée non mesurée du tableau : des décisions datées, jamais des mesures.

```toml
[[session]]               # une séance (session_id) ou un témoin (run_id)
id = "..."
status = "kept"           # kept | excluded | annex | replayed | pending
audit = "judged"          # facultatif : drapeaux d'audit jugés
date = "2026-11-08"
reason = "..."
ref = "..."               # facultatif

[[group]]                 # plusieurs artefacts : tâche, configuration et/ou chemin
task = "parity"           # facultatif
config = "d4523fc4"       # facultatif : identifiant de configuration (séances seulement)
path = "annexe-fields1"   # facultatif : chemin des témoins avant train/ (témoins seulement)
status = "annex"
date = "..."
reason = "..."
```

`excluded`, `annex` et `replayed` retirent des agrégats ; `kept` consigne un maintien ;
`pending` marque une question laissée « à juger » (aucun effet, `--strict` échoue).
Une entrée `[[session]]` prime sur un `[[group]]`.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

STATUSES = ("kept", "excluded", "annex", "replayed", "pending")
REMOVED = frozenset({"excluded", "annex", "replayed"})
AUDITS = ("judged",)


class DecisionsError(ValueError):
    """Fichier de décisions non conforme ou qui vise un artefact inconnu."""


@dataclass(frozen=True)
class Decision:
    status: str
    date: str
    reason: str
    ref: str = ""
    audit: str | None = None
    scope: str = ""  # "session:<id>" ou "group:task=…,path=…"
    task: str | None = None
    path: str | None = None
    config: str | None = None

    @property
    def removes(self) -> bool:
        return self.status in REMOVED


def _entry(raw: dict, where: str, allowed: set[str]) -> dict:
    if not isinstance(raw, dict):
        raise DecisionsError(f"{where} : table attendue")
    extra = sorted(set(raw) - allowed)
    if extra:
        raise DecisionsError(f"{where} : clés inconnues {extra}")
    status = raw.get("status")
    if status not in STATUSES:
        raise DecisionsError(f"{where} : status {status!r} hors {list(STATUSES)}")
    if raw.get("audit") not in (None, *AUDITS):
        raise DecisionsError(f"{where} : audit {raw.get('audit')!r} hors {list(AUDITS)}")
    for key in ("date", "reason"):
        if not str(raw.get(key) or "").strip():
            raise DecisionsError(f"{where} : {key} obligatoire")
    return raw


def read_decisions(path: Path) -> tuple[dict[str, Decision], list[Decision]]:
    """Décisions par identifiant et décisions de groupe ; fichier absent : aucune décision."""
    path = Path(path)
    if not path.is_file():
        return {}, []
    try:
        data = tomllib.loads(path.read_text("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise DecisionsError(f"{path.name} : {exc}") from exc
    extra = sorted(set(data) - {"session", "group"})
    if extra:
        raise DecisionsError(f"{path.name} : sections inconnues {extra}")
    by_id: dict[str, Decision] = {}
    common = {"status", "audit", "date", "reason", "ref"}
    for number, raw in enumerate(data.get("session", []), start=1):
        entry = _entry(raw, f"session {number}", common | {"id"})
        ident = str(entry.get("id") or "")
        if not ident:
            raise DecisionsError(f"session {number} : id obligatoire")
        if ident in by_id:
            raise DecisionsError(f"session {number} : id en double {ident}")
        by_id[ident] = Decision(
            status=entry["status"],
            date=str(entry["date"]),
            reason=str(entry["reason"]),
            ref=str(entry.get("ref") or ""),
            audit=entry.get("audit"),
            scope=f"session:{ident}",
        )
    groups: list[Decision] = []
    for number, raw in enumerate(data.get("group", []), start=1):
        entry = _entry(raw, f"group {number}", common | {"task", "path", "config"})
        if all(entry.get(k) is None for k in ("task", "path", "config")):
            raise DecisionsError(f"group {number} : task, config ou path obligatoire")
        if entry.get("path") is not None and entry.get("config") is not None:
            raise DecisionsError(f"group {number} : path (témoins) et config (séances) exclusifs")
        groups.append(
            Decision(
                status=entry["status"],
                date=str(entry["date"]),
                reason=str(entry["reason"]),
                ref=str(entry.get("ref") or ""),
                audit=entry.get("audit"),
                scope="group:"
                + ",".join(f"{k}={entry[k]}" for k in ("task", "config", "path") if k in entry),
                task=entry.get("task"),
                path=entry.get("path"),
                config=entry.get("config"),
            )
        )
    return by_id, groups
