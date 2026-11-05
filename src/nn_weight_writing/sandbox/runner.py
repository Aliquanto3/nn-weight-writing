"""Point d'entrée unique du bac à sable : `run(code, profile, payload) -> SandboxResult` (AD-5).

Rien d'autre n'exécute le code de l'agent. `run` applique le filtre statique puis lance le
sous-processus isolé (`_bootstrap.py`). Le parent ne fait pas confiance à la sortie standard :
la trame de résultat porte un nonce tiré ici et transmis par l'entrée standard, jamais par le
code de l'agent ; toute trame au mauvais nonce ou en double invalide l'exécution (D1).
"""

from __future__ import annotations

import json
import math
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from nn_weight_writing.config import load_protocol
from nn_weight_writing.sandbox.filter import (
    FITTING_FUNCTIONS,
    FORBIDDEN_ATTRIBUTES,
    Profile,
    Violation,
    check,
)

BOOTSTRAP = Path(__file__).with_name("_bootstrap.py")
FRAME_PREFIX = b"\x1eNNWW-FRAME "
LOG_LIMIT = 20_000  # égal à `_bootstrap.LOG_LIMIT` (plafond posé côté enfant)
MAX_WEIGHT_VALUES = 2_000_000
WEIGHT_KEY = re.compile(r"^L(0|[1-9][0-9]{0,3})\.(W|b)$")
ENV_KEEP = ("SYSTEMROOT", "PATH")


@dataclass(frozen=True)
class SandboxResult:
    """Issue d'une exécution. `value` : poids (A) ou une entrée par exemple (B)."""

    ok: bool
    error: str | None = None
    log: str = ""
    value: object = None
    duration_s: float = 0.0
    violations: tuple[Violation, ...] = field(default_factory=tuple)

    @property
    def refused(self) -> bool:
        return bool(self.violations)


class FrameError(ValueError):
    """Trame de résultat absente, en double, au mauvais nonce ou mal formée."""


def child_env() -> dict[str, str]:
    """Environnement du sous-processus : `SYSTEMROOT` et `PATH` seulement, aucune clé d'API."""
    return {key: os.environ[key] for key in ENV_KEEP if key in os.environ}


def run(
    code: str, profile: Profile, payload: dict | None = None, *, timeout_s: float | None = None
) -> SandboxResult:
    """Filtre puis exécute le code de l'agent. Pour B, `payload = {"examples": [raw, ...]}`."""
    profile = Profile(profile)
    violations = check(code, profile)
    if violations:
        return SandboxResult(ok=False, error="refused", violations=tuple(violations))
    if timeout_s is None:
        timeout_s = load_protocol().exec_timeout_s
    return _spawn(code, profile, payload, timeout_s)


def _spawn(code: str, profile: Profile, payload: dict | None, timeout_s: float) -> SandboxResult:
    """Exécute sans filtre : réservé à `run` (et aux tests de défense en profondeur)."""
    profile = Profile(profile)
    nonce = secrets.token_hex(16)
    request = {
        "nonce": nonce,
        "profile": str(profile),
        "code": code,
        "payload": payload,
        "drop": sorted(FORBIDDEN_ATTRIBUTES | FITTING_FUNCTIONS),
    }
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="nnww-sbx-") as cwd:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(BOOTSTRAP)],
                input=json.dumps(request).encode("utf-8"),
                capture_output=True,
                cwd=cwd,
                env=child_env(),
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                ok=False, error=f"timeout ({timeout_s:g} s)", duration_s=_since(start)
            )
    duration = _since(start)
    try:
        frame = parse_frames(proc.stdout, nonce)
    except FrameError as exc:
        stderr = proc.stderr.decode("utf-8", "replace")[-2000:]
        return SandboxResult(
            ok=False, error=f"trame invalide : {exc}; {stderr}", duration_s=duration
        )
    log = str(frame.get("log", ""))[: LOG_LIMIT + 100]  # marge pour le marqueur
    if not frame.get("ok"):
        value = frame.get("value") if profile is Profile.B else None
        try:
            value = _decode_labels(value, payload) if value is not None else None
        except FrameError:
            value = None
        return SandboxResult(
            ok=False, error=str(frame.get("error")), log=log, value=value, duration_s=duration
        )
    try:
        if profile is Profile.A:
            value = decode_weights(frame.get("value"))
        else:
            value = _decode_labels(frame.get("value"), payload)
    except FrameError as exc:
        return SandboxResult(
            ok=False, error=f"résultat invalide : {exc}", log=log, duration_s=duration
        )
    return SandboxResult(ok=True, log=log, value=value, duration_s=duration)


def _since(start: float) -> float:
    return round(time.perf_counter() - start, 6)


def parse_frames(stdout: bytes, nonce: str) -> dict:
    """Extrait l'unique trame au bon nonce ; refuse trame absente, en double ou forgée."""
    frames = []
    for line in stdout.splitlines():
        if not line.startswith(FRAME_PREFIX):
            continue
        rest = line[len(FRAME_PREFIX) :]
        got, _, body = rest.partition(b" ")
        if not secrets.compare_digest(got, nonce.encode("ascii")):
            raise FrameError("trame au mauvais nonce")
        frames.append(body)
    if not frames:
        raise FrameError("aucune trame")
    if len(frames) > 1:
        raise FrameError("trame en double")
    try:
        frame = json.loads(frames[0])
    except json.JSONDecodeError as exc:
        raise FrameError(f"JSON illisible : {exc}") from exc
    if not isinstance(frame, dict) or not isinstance(frame.get("ok"), bool):
        raise FrameError("trame mal formée")
    return frame


def decode_weights(value: object) -> dict[str, np.ndarray]:
    """Valide la sérialisation des poids : clés `L{i}.W|b`, float32, forme et données cohérentes."""
    if not isinstance(value, dict) or not value:
        raise FrameError("poids absents")
    out: dict[str, np.ndarray] = {}
    total = 0
    for key, item in value.items():
        if not isinstance(key, str) or not WEIGHT_KEY.match(key):
            raise FrameError(f"clé de poids invalide : {key!r}")
        if not isinstance(item, dict) or set(item) != {"shape", "dtype", "data"}:
            raise FrameError(f"{key} : entrée mal formée")
        shape, data = item["shape"], item["data"]
        if item["dtype"] != "float32":
            raise FrameError(f"{key} : dtype {item['dtype']!r}")
        if not isinstance(shape, list) or not all(
            type(d) is int and 0 <= d <= MAX_WEIGHT_VALUES for d in shape
        ):
            raise FrameError(f"{key} : forme invalide")
        size = math.prod(shape)
        total += size
        if total > MAX_WEIGHT_VALUES:
            raise FrameError("trop de poids")
        if not isinstance(data, list) or len(data) != size:
            raise FrameError(f"{key} : taille {len(data) if isinstance(data, list) else '?'}")
        if not all(type(x) in (int, float) and math.isfinite(x) for x in data):
            raise FrameError(f"{key} : valeur non finie ou non numérique")
        out[key] = np.asarray(data, dtype=np.float32).reshape(shape)
    return out


def _decode_labels(value: object, payload: dict | None) -> list[dict]:
    expected = len(payload["examples"]) if payload else 0
    if not isinstance(value, list) or len(value) != expected:
        raise FrameError("nombre de labels différent du nombre d'exemples")
    for item in value:
        if not isinstance(item, dict) or len(item) != 1 or not ({"label", "error"} & set(item)):
            raise FrameError("entrée de label mal formée")
    return value
