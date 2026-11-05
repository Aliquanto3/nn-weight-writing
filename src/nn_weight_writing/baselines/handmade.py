"""Solutions écrites à la main des tâches jouet, au format de réseau unique (AD-3).

Poids calculés à la main, sans entraînement et sans jamais lire un jeu : elles prouvent que
le harnais (format, chargement, évaluation, empreintes) atteint 100 % sur une solution exacte.
"""

from __future__ import annotations

import numpy as np

from nn_weight_writing.tasks.toy import automaton, compare, get_task, parity


def _dense(n_in: int, n_out: int) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((n_in, n_out), dtype=np.float32), np.zeros(n_out, dtype=np.float32)


def _layers(*sizes: tuple[int, int, str]) -> list[dict]:
    return [{"type": "dense", "in": i, "out": o, "activation": a} for i, o, a in sizes]


def parity_network() -> tuple[dict, dict[str, np.ndarray]]:
    """s = nombre de 1 ; [s >= k] = relu(s - k + 1) - relu(s - k) ; impair = somme alternée."""
    n = parity.LENGTH
    w0, b0 = _dense(n, 2 * n)
    w1, b1 = _dense(2 * n, 2)
    for k in range(1, n + 1):
        sign = 1.0 if k % 2 else -1.0
        up, down = 2 * (k - 1), 2 * (k - 1) + 1
        w0[:, up] = 1.0
        b0[up] = -(k - 1)
        w0[:, down] = 1.0
        b0[down] = -k
        w1[up, 1], w1[down, 1] = sign, -sign  # sortie « impair »
        w1[up, 0], w1[down, 0] = -sign, sign  # sortie « pair » = 1 - impair
    b1[0] = 1.0
    manifest = {
        "encoder": get_task("parity").encoder_id,
        "layers": _layers((n, 2 * n, "relu"), (2 * n, 2, "identity")),
    }
    return manifest, {"L0.W": w0, "L0.b": b0, "L1.W": w1, "L1.b": b1}


def compare_network() -> tuple[dict, dict[str, np.ndarray]]:
    """d = a - b (entiers) ; [d >= 1] = relu(d) - relu(d - 1) ; [d <= -1] de même ; égal = reste."""
    scale = compare.SCALE
    w0, b0 = _dense(2, 4)
    w0[:, 0] = (scale, -scale)  # relu(d)
    w0[:, 1] = (scale, -scale)  # relu(d - 1)
    b0[1] = -1.0
    w0[:, 2] = (-scale, scale)  # relu(-d)
    w0[:, 3] = (-scale, scale)  # relu(-d - 1)
    b0[3] = -1.0
    w1, b1 = _dense(4, 3)  # sorties : less, equal, greater
    w1[:, 0] = (0, 0, 1, -1)
    w1[:, 1] = (-1, 1, -1, 1)
    b1[1] = 1.0
    w1[:, 2] = (1, -1, 0, 0)
    manifest = {
        "encoder": get_task("compare").encoder_id,
        "layers": _layers((2, 4, "relu"), (4, 3, "identity")),
    }
    return manifest, {"L0.W": w0, "L0.b": b0, "L1.W": w1, "L1.b": b1}


def automaton_network() -> tuple[dict, dict[str, np.ndarray]]:
    """Une unité par fenêtre : relu(x_i - x_{i+1} + x_{i+2} - 1) vaut 1 sur 101, 0 sinon."""
    n = automaton.LENGTH
    windows = n - 2
    w0, b0 = _dense(n, windows)
    for i in range(windows):
        w0[i, i], w0[i + 1, i], w0[i + 2, i] = 1.0, -1.0, 1.0
        b0[i] = -1.0
    w1, b1 = _dense(windows, 2)  # v0 = relu(somme), v1 = relu(somme - 1)
    w1[:, 0] = 1.0
    w1[:, 1] = 1.0
    b1[1] = -1.0
    w2, b2 = _dense(2, 2)  # accepte = v0 - v1 = min(somme, 1) ; rejette = 1 - accepte
    w2[:, 0] = (1, -1)
    w2[:, 1] = (-1, 1)
    b2[1] = 1.0
    manifest = {
        "encoder": get_task("automaton").encoder_id,
        "layers": _layers((n, windows, "relu"), (windows, 2, "relu"), (2, 2, "identity")),
    }
    return manifest, {"L0.W": w0, "L0.b": b0, "L1.W": w1, "L1.b": b1, "L2.W": w2, "L2.b": b2}


BUILDERS = {"parity": parity_network, "compare": compare_network, "automaton": automaton_network}


def build(task: str) -> tuple[dict, dict[str, np.ndarray]]:
    try:
        return BUILDERS[task]()
    except KeyError:
        raise KeyError(f"pas de solution écrite à la main pour {task!r}") from None
