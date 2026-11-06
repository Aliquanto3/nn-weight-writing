"""Service d'outils de séance : état (passes, production, gel) et seul écrivain du journal.

Les pilotes (1-6) appellent `call(tool, arguments)` et transmettent les échanges par
`record_model_call` ; ils n'écrivent jamais le journal eux-mêmes (AD-7). Ces entrées sont
sérialisées par un verrou : le serveur MCP du pilote Claude Code appelle les outils depuis un
autre fil que le lecteur du flux.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from nn_weight_writing import sandbox
from nn_weight_writing.config import ProtocolConfig, load_protocol
from nn_weight_writing.journal.schema import (
    EndEvent,
    FreezeEvent,
    ModelCallEvent,
    OpenEvent,
    PassEvent,
    RefusalEvent,
    ScriptRunEvent,
    ToolCallEvent,
)
from nn_weight_writing.journal.writer import JournalWriter
from nn_weight_writing.network import io as netio
from nn_weight_writing.network.layers import forward
from nn_weight_writing.sandbox.audit import audit
from nn_weight_writing.sandbox.filter import Profile
from nn_weight_writing.session.refusals import EndReason, RefusalCode
from nn_weight_writing.session.tools import TOOLS_BY_NAME, Method, argument_errors
from nn_weight_writing.tasks.base import Codec
from nn_weight_writing.tasks.io import read_bundle

BUNDLE_DIR = "bundle"
JOURNAL_FILE = "journal.jsonl"
FROZEN_DIR = "frozen"
SCRIPT_FILE = "script.py"
RULES_FILE = "rules.py"
DETAIL_LIMIT = 2000


def model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9.-]", "", model.lower())


def make_session_id(task: str, method: str, model: str, attempt: int, now: datetime) -> str:
    """`{task}-{method}-{model_slug}-t{n}-{YYYYMMDDTHHMMSSZ}` (AD-12), `now` en UTC."""
    return f"{task}-{method}-{model_slug(model)}-t{attempt}-{now.strftime('%Y%m%dT%H%M%SZ')}"


def _only_numbers(rows: list) -> bool:
    """Listes imbriquées de `int` ou `float` seulement (parcours itératif, sans récursion)."""
    stack: list[object] = [rows]
    while stack:
        item = stack.pop()
        if type(item) is list:
            stack.extend(item)
        elif type(item) not in (int, float):
            return False
    return True


@dataclass(frozen=True)
class OpenInfo:
    """Champs de l'événement `open` fournis par l'appelant (pilote et modèle : 1-6)."""

    task: str
    dataset: str
    dataset_sha256: str
    method: str
    model: str
    driver: str
    provider: str
    attempt: int
    seed: int
    system_prompt_sha256: str
    sampling: dict = field(default_factory=dict)
    effort: str | None = None


class ToolRefusal(Exception):
    def __init__(self, code: RefusalCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail[:DETAIL_LIMIT]


class ToolService:
    """Une séance : paquet en lecture, production en mémoire, journal en ajout seul."""

    def __init__(
        self,
        run_dir: Path,
        codec: Codec,
        info: OpenInfo,
        config: ProtocolConfig | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.config = config or load_protocol()
        self.bundle = read_bundle(self.run_dir / BUNDLE_DIR)
        if codec.encoder_id != self.bundle.encoder:
            raise ValueError(f"encodeur {codec.encoder_id} ≠ paquet {self.bundle.encoder}")
        self.codec = codec
        self.method = Method(info.method)
        self.frozen_dir = self.run_dir / FROZEN_DIR
        self.passes_used = 0
        self.freeze_attempts = 0
        self.ended = False
        # Gel réussi : plus aucun outil. Le journal est clos aussitôt, sauf si le pilote garde la
        # main (`close_on_freeze = False`) pour y verser l'usage de fin de flux avant `end`.
        self.frozen = False
        self.close_on_freeze = True
        self._end_after_call = False
        self._started = time.perf_counter()
        self._lock = threading.RLock()
        self._totals = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_equiv_usd": 0.0,
            "billed_usd": 0.0,
        }
        # Production courante.
        self.manifest: dict | None = None
        self.weights: dict[str, np.ndarray] | None = None
        self._pending: dict[str, np.ndarray] = {}
        self._written: dict[str, np.ndarray] = {}
        self.script: str | None = None
        self.rules: str | None = None
        self._inputs: np.ndarray | None = None
        self.journal = JournalWriter(
            self.run_dir / JOURNAL_FILE, self.config.journal_schema_version
        )
        self.journal.write(
            OpenEvent(
                session_id=self.run_dir.name,
                task=info.task,
                dataset=info.dataset,
                dataset_sha256=info.dataset_sha256,
                method=str(self.method),
                model=info.model,
                driver=info.driver,
                provider=info.provider,
                attempt=info.attempt,
                seed=info.seed,
                pass_budget=self.config.pass_budget,
                protocol_sha256=self.config.protocol_sha256,
                system_prompt_sha256=info.system_prompt_sha256,
                sampling=dict(info.sampling),
                effort=info.effort,
            )
        )

    # --- Entrées des pilotes -------------------------------------------------------------

    @property
    def passes_remaining(self) -> int:
        return max(self.config.pass_budget - self.passes_used, 0)

    @property
    def totals(self) -> dict:
        """Totaux de jetons et de coûts des `model_call` transmis jusqu'ici."""
        with self._lock:
            return dict(self._totals)

    def call(self, tool: str, arguments: object = None) -> dict:
        """Exécute un outil ; tout appel est journalisé (`tool_call`), refus compris."""
        with self._lock:
            return self._call(tool, arguments)

    def _call(self, tool: str, arguments: object) -> dict:
        arguments = {} if arguments is None else arguments
        if self.ended or self.frozen:
            # Séance gelée ou close : le refus est renvoyé sans être écrit.
            code = RefusalCode.SESSION_CLOSED
            return {"refused": str(code), "detail": "la séance est close"}
        try:
            result = self._dispatch(tool, arguments)
        except ToolRefusal as refusal:
            self.journal.write(RefusalEvent(code=str(refusal.code), detail=refusal.detail))
            result = {"refused": str(refusal.code), "detail": refusal.detail}
        logged = arguments if isinstance(arguments, dict) else {"invalid": repr(arguments)[:200]}
        self.journal.write(ToolCallEvent(tool=str(tool), arguments=logged, result=result))
        if self._end_after_call:
            self._end_after_call = False
            self.frozen = True
            if self.close_on_freeze:
                self.end(EndReason.FROZEN)
        return result

    def record_model_call(self, event: ModelCallEvent) -> None:
        with self._lock:
            self._record_model_call(event)

    def _record_model_call(self, event: ModelCallEvent) -> None:
        if self.ended:
            raise RuntimeError("séance close")
        for key in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"):
            self._totals[key] += getattr(event, key)
        self._totals["cost_equiv_usd"] = round(
            self._totals["cost_equiv_usd"] + event.cost_equiv_usd, 6
        )
        self._totals["billed_usd"] = round(self._totals["billed_usd"] + event.billed_usd, 6)
        self.journal.write(event)

    def end(self, reason: EndReason, detail: str | None = None) -> None:
        """Écrit l'événement `end` et ferme le journal ; une seule fois par séance."""
        with self._lock:
            if self.ended:
                raise RuntimeError("séance déjà close")
            self.ended = True
            totals = {**self._totals, "duration_s": round(time.perf_counter() - self._started, 6)}
            self.journal.write(
                EndEvent(
                    reason=str(EndReason(reason)),
                    passes_used=self.passes_used,
                    totals=totals,
                    detail=None if detail is None else detail[:DETAIL_LIMIT],
                )
            )
            self.journal.close()

    # --- Aiguillage ------------------------------------------------------------------------

    def _dispatch(self, tool: str, arguments: object) -> dict:
        spec = TOOLS_BY_NAME.get(tool) if isinstance(tool, str) else None
        if spec is None:
            raise ToolRefusal(RefusalCode.UNKNOWN_TOOL, f"outil inconnu : {tool!r}")
        if self.method not in spec.methods:
            raise ToolRefusal(
                RefusalCode.METHOD_NOT_ALLOWED,
                f"{tool} n'est pas ouvert à la méthode {self.method}",
            )
        errors = argument_errors(spec.input_schema, arguments)
        if errors:
            raise ToolRefusal(RefusalCode.INVALID_ARGUMENTS, "; ".join(errors))
        if spec.mutates_production and self.passes_used >= self.config.pass_budget:
            raise ToolRefusal(
                RefusalCode.MUTATION_AFTER_BUDGET,
                "budget de passes épuisé : seul freeze reste permis",
            )
        return getattr(self, f"_tool_{tool}")(**arguments)

    def _refuse_from_violations(self, violations: tuple) -> ToolRefusal:
        detail = "; ".join(f"ligne {v.lineno} : {v.detail}" for v in violations)
        return ToolRefusal(RefusalCode(violations[0].code), detail)

    def _audit(self, code: str) -> list[dict]:
        return audit(code, [(e.id, e.raw) for e in self.bundle.examples])

    def _script_run(self, tool: str, code: str, result: sandbox.SandboxResult, flags: list) -> None:
        self.journal.write(
            ScriptRunEvent(
                tool=tool,
                # Un code à substitut isolé est refusé par le filtre, mais journalisé.
                code_sha256=netio.sha256_bytes(code.encode("utf-8", "surrogatepass")),
                ok=result.ok,
                log=result.log,
                flags=flags,
                duration_s=result.duration_s,
                error=result.error,
            )
        )

    # --- Outils ----------------------------------------------------------------------------

    def _tool_declare_network(self, manifest: dict) -> dict:
        if self.weights is not None or any(mask.any() for mask in self._written.values()):
            raise ToolRefusal(RefusalCode.NETWORK_HAS_WEIGHTS, "des poids sont déjà écrits")
        errors = netio.manifest_errors(manifest)
        if errors:
            raise ToolRefusal(RefusalCode.INVALID_MANIFEST, "; ".join(errors))
        if manifest["encoder"] != self.bundle.encoder:
            raise ToolRefusal(
                RefusalCode.ENCODER_MISMATCH, f"l'encodeur de la tâche est {self.bundle.encoder}"
            )
        self.manifest = manifest
        if self.method is Method.A_LITERAL:
            shapes = netio.weight_shapes(manifest)
            self.weights = None
            self._pending = {k: np.zeros(s, dtype=np.float32) for k, s in shapes.items()}
            self._written = {k: np.zeros(s[0], dtype=bool) for k, s in shapes.items()}
        return {"declared": True, "params": netio.n_params(manifest)}

    def _tool_write_weights(self, layer: int, param: str, row_start: int, rows: list) -> dict:
        if self.manifest is None:
            raise ToolRefusal(RefusalCode.NO_NETWORK_DECLARED, "declare_network d'abord")
        key = f"L{layer}.{param}"
        if key not in self._pending:
            raise ToolRefusal(RefusalCode.INVALID_WEIGHTS, f"paramètre inconnu : {key}")
        target = self._pending[key]
        if row_start + len(rows) > target.shape[0]:
            raise ToolRefusal(RefusalCode.INVALID_WEIGHTS, f"{key} a {target.shape[0]} lignes")
        if not _only_numbers(rows):
            # Ni chaîne ni booléen : NumPy convertirait `"1.0"` et `True` en 1.0.
            raise ToolRefusal(RefusalCode.INVALID_WEIGHTS, "valeurs non numériques")
        try:
            values = np.asarray(rows, dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ToolRefusal(
                RefusalCode.INVALID_WEIGHTS, f"valeurs non numériques : {exc}"
            ) from exc
        expected = (len(rows), *target.shape[1:])
        with np.errstate(over="ignore"):
            # Finitude jugée en float32 : `1e300`, fini en float64, deviendrait `inf`.
            values = values.astype(np.float32)
        if values.shape != expected or not np.isfinite(values).all():
            raise ToolRefusal(
                RefusalCode.INVALID_WEIGHTS, f"forme attendue {expected}, valeurs finies en float32"
            )
        target[row_start : row_start + len(rows)] = values
        self._written[key][row_start : row_start + len(rows)] = True
        remaining = int(sum((~mask).sum() for mask in self._written.values()))
        return {"written": len(rows), "rows_remaining": remaining}

    def _tool_submit_script(self, code: str) -> dict:
        if self.manifest is None:
            raise ToolRefusal(RefusalCode.NO_NETWORK_DECLARED, "declare_network d'abord")
        flags = self._audit(code)
        result = sandbox.run(code, Profile.A, None, timeout_s=self.config.exec_timeout_s)
        if result.ok:
            errors = netio.weights_errors(self.manifest, result.value)
            if errors:
                result = sandbox.SandboxResult(
                    ok=False,
                    error="poids non conformes au manifeste : " + "; ".join(errors),
                    log=result.log,
                    duration_s=result.duration_s,
                )
        self._script_run("submit_script", code, result, flags)
        if result.refused:
            raise self._refuse_from_violations(result.violations)
        if result.ok:
            # Seule une soumission réussie remplace la production.
            self.weights = result.value
            self.script = code
        return {"ok": result.ok, "error": result.error, "log": result.log}

    def _tool_submit_rules(self, code: str) -> dict:
        flags = self._audit(code)
        violations = tuple(sandbox.check(code, Profile.B))
        result = sandbox.SandboxResult(
            ok=not violations, error="refused" if violations else None, violations=violations
        )
        self._script_run("submit_rules", code, result, flags)
        if violations:
            raise self._refuse_from_violations(violations)
        self.rules = code
        return {"ok": True}

    def _tool_run_on_examples(self) -> dict:
        if self.passes_used >= self.config.pass_budget:
            raise ToolRefusal(
                RefusalCode.PASS_BUDGET_EXHAUSTED,
                f"{self.config.pass_budget} passes consommées : seul freeze reste permis",
            )
        self.passes_used += 1  # décompte avant exécution (AD-6)
        valid, outputs, error = self._execute()
        self.journal.write(
            PassEvent(
                number=self.passes_used,
                remaining=self.passes_remaining,
                valid=valid,
                outputs=outputs,
                error=error,
            )
        )
        return {
            "pass": self.passes_used,
            "remaining": self.passes_remaining,
            "valid": valid,
            "outputs": outputs,
            "error": error,
        }

    def _tool_freeze(self, blocks: list | None = None) -> dict:
        self.freeze_attempts += 1
        if self.freeze_attempts > self.config.max_freeze_attempts:
            raise ToolRefusal(
                RefusalCode.FREEZE_ATTEMPTS_EXHAUSTED,
                f"au plus {self.config.max_freeze_attempts} tentatives de gel",
            )
        if self.method is Method.B:
            if blocks is not None:
                raise ToolRefusal(RefusalCode.INVALID_BLOCKS, "B se gèle sans blocs")
            if self.rules is None:
                raise ToolRefusal(RefusalCode.NO_PRODUCTION, "aucune règle soumise")
        else:
            self._check_a_production()
            self._check_blocks(blocks)
        valid, _, _ = self._execute()  # ne consomme pas de passe, rien n'est renvoyé
        self._write_frozen(blocks, valid)
        self._end_after_call = True
        return {"frozen": True}

    # --- Production ------------------------------------------------------------------------

    def _current_weights(self) -> dict[str, np.ndarray] | None:
        if self.method is Method.A_LITERAL:
            if self.manifest is None or not all(m.all() for m in self._written.values()):
                return None
            return self._pending
        return self.weights

    def _check_a_production(self) -> None:
        if self.manifest is None:
            raise ToolRefusal(RefusalCode.NO_PRODUCTION, "aucun réseau déclaré")
        if self._current_weights() is None:
            if self.method is Method.A_LITERAL:
                raise ToolRefusal(RefusalCode.WEIGHTS_INCOMPLETE, "des lignes restent à écrire")
            raise ToolRefusal(RefusalCode.NO_PRODUCTION, "aucun script réussi")

    def _check_blocks(self, blocks: list | None) -> None:
        if blocks is None:
            raise ToolRefusal(RefusalCode.INVALID_BLOCKS, "blocs obligatoires pour A")
        errors = netio.manifest_errors({**self.manifest, "blocks": blocks}, with_blocks=True)
        if errors:
            raise ToolRefusal(RefusalCode.INVALID_BLOCKS, "; ".join(errors))
        vocabulary = self.bundle.vocabulary_ids
        unknown = sorted({t for block in blocks for t in block["types"]} - vocabulary)
        if unknown:
            raise ToolRefusal(RefusalCode.TYPE_NOT_IN_VOCABULARY, f"types inconnus : {unknown}")
        hidden = netio.hidden_units(self.manifest)
        seen: set[tuple[int, int]] = set()
        for j, block in enumerate(blocks):
            for unit in map(tuple, block["units"]):
                if unit not in hidden:
                    raise ToolRefusal(
                        RefusalCode.INVALID_BLOCKS, f"bloc {j} : {list(unit)} n'est pas cachée"
                    )
                if unit in seen:
                    raise ToolRefusal(
                        RefusalCode.INVALID_BLOCKS, f"bloc {j} : {list(unit)} en double"
                    )
                seen.add(unit)
        missing = sorted(hidden - seen)
        if missing:
            raise ToolRefusal(
                RefusalCode.INVALID_BLOCKS,
                f"{len(missing)} unité(s) cachée(s) hors blocs, dont {list(missing[0])}",
            )

    def _encoded_inputs(self) -> np.ndarray:
        if self._inputs is None:
            rows = [
                np.asarray(self.codec.encode(e.raw), dtype=np.float32) for e in self.bundle.examples
            ]
            self._inputs = np.stack(rows)
        return self._inputs

    def _execute(self) -> tuple[bool, list, str | None]:
        """Exécute la production sur les exemples : (valide, sorties, erreur)."""
        ids = [e.id for e in self.bundle.examples]
        if self.method is Method.B:
            if self.rules is None:
                return False, [], "aucune règle soumise"
            result = sandbox.run(
                self.rules,
                Profile.B,
                {"examples": [e.raw for e in self.bundle.examples]},
                timeout_s=self.config.exec_timeout_s,
            )
            if not isinstance(result.value, list):
                return False, [], result.error
            outputs = [{"id": i, **item} for i, item in zip(ids, result.value, strict=True)]
            return result.ok, outputs, result.error
        weights = self._current_weights()
        if self.manifest is None or weights is None:
            return False, [], "aucun réseau complet"
        x = self._encoded_inputs()
        n_in = self.manifest["layers"][0]["in"]
        if x.ndim != 2 or x.shape[1] != n_in:
            return (
                False,
                [],
                f"entrées de forme {x.shape}, la couche 0 attend in={n_in}",
            )
        with np.errstate(all="ignore"):
            y = forward(self.manifest, weights, x)
        if not np.isfinite(y).all():
            return False, [], "sorties non finies"
        outputs = []
        for i, row in zip(ids, y, strict=True):
            label = self.codec.decode(row)
            label = label.item() if isinstance(label, np.generic) else label
            outputs.append({"id": i, "output": row.tolist(), "label": label})
        return True, outputs, None

    def _write_frozen(self, blocks: list | None, valid: bool) -> None:
        self.frozen_dir.mkdir(parents=False, exist_ok=False)
        payloads: dict[str, bytes] = {}
        size_nominal = size_script = size_zlib = 0
        if self.method is Method.B:
            payloads[RULES_FILE] = self.rules.encode("utf-8")
            size_script = len(payloads[RULES_FILE])
        else:
            weights = self._current_weights()
            manifest = {**self.manifest, "blocks": blocks}
            payloads[netio.MANIFEST_NAME] = netio.manifest_bytes(manifest)
            payloads[netio.WEIGHTS_NAME] = netio.weights_bytes(self.manifest, weights)
            size_nominal = netio.n_params(self.manifest)
            size_zlib = netio.weights_zlib_size(self.manifest, weights)
            if self.method is Method.A_PROGRAM:
                payloads[SCRIPT_FILE] = self.script.encode("utf-8")
                size_script = len(payloads[SCRIPT_FILE])
        files = {}
        for name, data in payloads.items():
            netio.atomic_write_bytes(self.frozen_dir / name, data)
            files[name] = netio.sha256_bytes(data)
        self.journal.write(
            FreezeEvent(
                files=files,
                tree_sha256=netio.tree_sha256(files),
                valid=valid,
                blocks=blocks,
                size_nominal=size_nominal,
                size_script_bytes=size_script,
                size_weights_zlib=size_zlib,
            )
        )
