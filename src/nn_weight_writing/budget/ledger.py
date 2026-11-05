"""Registre budgétaire `budget/ledger.csv` (AD-11), écrit par la seule fonction `append`.

CSV sans en-tête, `merge=union` : une ligne `reserved` à l'ouverture d'une séance, une ligne
`closed` à la fin (coûts réels), même en erreur. Les lectures dédoublonnent par
`(session_id, status)` (première occurrence). La vérification des plafonds et l'ajout de la
réservation se font sous un même verrou de fichier : deux séances parallèles se voient.
"""

from __future__ import annotations

import csv
import io
import json
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from nn_weight_writing.config import ProtocolConfig
from nn_weight_writing.journal.writer import utc_now

LEDGER_PATH = Path(__file__).resolve().parents[3] / "budget" / "ledger.csv"
FIELDS = ("ts", "session_id", "lot", "status", "reserved_usd", "billed_usd", "cost_equiv_usd")
LOCK_TIMEOUT_S = 30.0
STALE_LOCK_S = 120.0


class Status(StrEnum):
    RESERVED = "reserved"
    CLOSED = "closed"


@dataclass(frozen=True)
class LedgerRow:
    ts: str
    session_id: str
    lot: int
    status: Status
    reserved_usd: float = 0.0
    billed_usd: float = 0.0
    cost_equiv_usd: float = 0.0

    def to_line(self) -> str:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerow(
            [
                self.ts,
                self.session_id,
                self.lot,
                str(self.status),
                f"{self.reserved_usd:.6f}",
                f"{self.billed_usd:.6f}",
                f"{self.cost_equiv_usd:.6f}",
            ]
        )
        return buffer.getvalue()


class BudgetRefused(Exception):
    """Ouverture refusée par un plafond : décision d'Anaël requise (AD-11)."""


@dataclass(frozen=True)
class Spend:
    billed_usd: float
    reserved_open_usd: float

    @property
    def committed_usd(self) -> float:
        return round(self.billed_usd + self.reserved_open_usd, 6)


def read(path: Path | None = None) -> list[LedgerRow]:
    path = Path(path or LEDGER_PATH)
    if not path.exists():
        return []
    rows: list[LedgerRow] = []
    seen: set[tuple[str, str]] = set()
    with open(path, encoding="utf-8", newline="") as handle:
        for number, values in enumerate(csv.reader(handle), start=1):
            if not values:
                continue
            if len(values) != len(FIELDS):
                raise ValueError(f"{path.name} ligne {number} : {len(values)} champs")
            ts, session_id, lot, status, reserved, billed, equiv = values
            key = (session_id, status)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                LedgerRow(
                    ts,
                    session_id,
                    int(lot),
                    Status(status),
                    float(reserved),
                    float(billed),
                    float(equiv),
                )
            )
    return rows


def spend(rows: list[LedgerRow], lot: int | None = None) -> Spend:
    """Facturé (lignes `closed`) et réservations ouvertes (`reserved` sans `closed`)."""
    closed = {r.session_id for r in rows if r.status is Status.CLOSED}
    billed = reserved = 0.0
    for row in rows:
        if lot is not None and row.lot != lot:
            continue
        if row.status is Status.CLOSED:
            billed += row.billed_usd
        elif row.session_id not in closed:
            reserved += row.reserved_usd
    return Spend(round(billed, 6), round(reserved, 6))


class _Lock:
    """Verrou par création exclusive d'un fichier voisin ; un verrou abandonné expire.

    Le fichier porte un jeton : à la sortie, seul son propre verrou est supprimé (un verrou
    brisé comme périmé puis repris par un autre écrivain reste en place).
    """

    def __init__(self, path: Path) -> None:
        self.path = path.with_name(path.name + ".lock")
        self.token = uuid.uuid4().hex.encode("ascii")

    def __enter__(self) -> _Lock:
        deadline = time.monotonic() + LOCK_TIMEOUT_S
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > STALE_LOCK_S:
                        self.path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() > deadline:
                    raise TimeoutError(f"registre verrouillé : {self.path}") from None
                time.sleep(0.05)
            else:
                try:
                    os.write(fd, self.token)
                finally:
                    os.close(fd)
                return self

    def __exit__(self, *exc: object) -> None:
        try:
            if self.path.read_bytes() == self.token:
                self.path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass


def append(
    row: LedgerRow,
    path: Path | None = None,
    *,
    check: Callable[[list[LedgerRow]], None] | None = None,
) -> LedgerRow:
    """Seul écrivain du registre. `check` lit l'état sous le verrou et peut refuser l'ajout."""
    path = Path(path or LEDGER_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _Lock(path):
        if check is not None:
            check(read(path))
        with open(path, "a", encoding="utf-8", newline="") as handle:
            handle.write(row.to_line())
    return row


def cap_errors(rows: list[LedgerRow], lot: int, amount: float, config: ProtocolConfig) -> list[str]:
    """Facturé + réservations ouvertes + `amount` ≤ plafond, pour le lot et pour le projet."""
    errors = []
    for label, cap, current in (
        (f"lot {lot}", config.lot_cap_usd(lot), spend(rows, lot)),
        ("projet", config.project_cap_usd, spend(rows)),
    ):
        total = round(current.committed_usd + amount, 6)
        if total > cap:
            errors.append(
                f"plafond {label} : {current.billed_usd:.6f} facturés + "
                f"{current.reserved_open_usd:.6f} réservés + {amount:.6f} > {cap:.2f} $"
            )
    return errors


def reserve(
    session_id: str,
    lot: int,
    amount: float,
    config: ProtocolConfig,
    path: Path | None = None,
) -> LedgerRow:
    """Ligne `reserved` si les plafonds le permettent, sinon `BudgetRefused`.

    Une séance par abonnement réserve 0 $ : la vérification des plafonds ne la bloque pas.
    """
    config.lot_cap_usd(lot)

    def check(rows: list[LedgerRow]) -> None:
        if any(r.session_id == session_id for r in rows):
            raise BudgetRefused(f"séance déjà inscrite au registre : {session_id}")
        if amount > 0:
            errors = cap_errors(rows, lot, amount, config)
            if errors:
                raise BudgetRefused("; ".join(errors) + " : décision d'Anaël requise")

    row = LedgerRow(utc_now(), session_id, lot, Status.RESERVED, reserved_usd=round(amount, 6))
    return append(row, path, check=check)


def close(
    session_id: str,
    lot: int,
    billed: float,
    cost_equiv: float,
    path: Path | None = None,
) -> LedgerRow:
    row = LedgerRow(
        utc_now(),
        session_id,
        lot,
        Status.CLOSED,
        billed_usd=round(billed, 6),
        cost_equiv_usd=round(cost_equiv, 6),
    )
    return append(row, path)


def journal_costs(journal: Path) -> tuple[float, float]:
    """Somme des `billed_usd` et `cost_equiv_usd` des événements `model_call` d'un journal."""
    billed = equiv = 0.0
    if journal.exists():
        for line in journal.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("type") == "model_call":
                billed += float(record["billed_usd"])
                equiv += float(record["cost_equiv_usd"])
    return round(billed, 6), round(equiv, 6)


def reconcile(runs_dir: Path, path: Path | None = None) -> list[LedgerRow]:
    """Clôt les réservations orphelines depuis `runs/<lot>/<session_id>/journal.jsonl`.

    Sans journal, aucun appel n'a eu lieu (l'événement `open` précède tout appel) : 0 $.
    """
    rows = read(path)
    closed = {r.session_id for r in rows if r.status is Status.CLOSED}
    written = []
    for row in rows:
        if row.status is Status.RESERVED and row.session_id not in closed:
            journal = Path(runs_dir) / str(row.lot) / row.session_id / "journal.jsonl"
            billed, equiv = journal_costs(journal)
            written.append(close(row.session_id, row.lot, billed, equiv, path))
    return written
