"""Corpus d'évasions du bac à sable (AD-5, D2, D4) : chaque cas connu doit échouer.

Deux niveaux : le filtre statique refuse chaque cas avec son code ; puis, filtre contourné
(`_spawn`), l'isolement d'exécution fait encore échouer les cas qui n'exigent pas de
souligné (espaces de noms restreints, builtins réduits, hook d'audit).
"""

from __future__ import annotations

import types

import numpy as np
import pytest

from nn_weight_writing.sandbox import _bootstrap
from nn_weight_writing.sandbox.filter import (
    FITTING_FUNCTIONS,
    FORBIDDEN_ATTRIBUTES,
    Profile,
    _attribute_violation,
)
from nn_weight_writing.sandbox.runner import _spawn, run

NP = "import numpy as np\n"
BUILD = "\ndef build():\n    return {'L0.W': np.ones((1, 1)), 'L0.b': np.ones(1)}\n"

# (identifiant, profil, code, code de refus attendu du filtre)
CORPUS = [
    (
        "cadres-generateur",
        "A",
        "g = (x for x in [1])\nh = g.gi_frame.f_back.f_globals",
        "forbidden_attribute",
    ),
    ("np-ma-core-builtins", "A", NP + "b = np.ma.core.builtins", "forbidden_attribute"),
    ("np-f2py-os", "A", NP + "o = np.f2py.os", "forbidden_attribute"),
    ("np-ctypeslib", "A", NP + "c = np.ctypeslib", "forbidden_attribute"),
    ("string-formatter", "B", "import string\nf = string.Formatter()", "forbidden_import"),
    ("np-load-pickle", "A", NP + "w = np.load('x.npy', allow_pickle=True)", "forbidden_attribute"),
    ("import-os-deja-charge", "A", "import os\nos.listdir('.')", "forbidden_import"),
    ("re-enum-sys", "B", "import re\ns = re.enum.sys", "forbidden_attribute"),
    ("sys-modules", "B", "import sys\nm = sys.modules", "forbidden_import"),
    ("os-write-fd1", "A", "import os\nos.write(1, b'x')", "forbidden_import"),
    ("os-write-fd2", "B", "from os import write\nwrite(2, b'x')", "forbidden_import"),
    ("alias-ajustement", "A", "from numpy.linalg import lstsq as f", "fitting_function"),
    ("getattr-nom-construit", "A", NP + "f = getattr(np, 'lo' + 'ad')", "forbidden_name"),
    (
        "subclasses-par-match",
        "B",
        "match ():\n    case tuple(__class__=c):\n        pass",
        "forbidden_attribute",
    ),
    ("subclasses-par-vars", "B", "s = vars(type(()))['__subcl' + 'asses__']", "forbidden_name"),
    ("subclasses-direct", "B", "s = ().__class__.__base__.__subclasses__()", "forbidden_attribute"),
    ("builtins-du-module", "B", "o = __builtins__['open']", "forbidden_name"),
    ("open", "B", "f = open('x')", "forbidden_name"),
    ("exec", "A", "exec('import os')", "forbidden_name"),
    ("str-format", "B", "s = '{0.__class__}'.format(1)", "forbidden_attribute"),
    ("ndarray-tofile", "A", NP + "np.zeros(1).tofile('x.bin')", "forbidden_attribute"),
    ("ndarray-dump", "A", NP + "np.zeros(1).dump('x.pkl')", "forbidden_attribute"),
    ("ndarray-ctypes", "A", NP + "p = np.zeros(1).ctypes", "forbidden_attribute"),
    ("np-fromregex", "A", NP + "a = np.fromregex('x', 'a', [])", "forbidden_attribute"),
    ("np-lib-npyio", "A", NP + "a = np.lib.npyio", "forbidden_attribute"),
    ("np-testing", "A", NP + "t = np.testing", "forbidden_attribute"),
    ("import-dynamique", "B", "m = __import__('os')", "forbidden_name"),
]


@pytest.mark.parametrize(
    ("case", "profile", "code", "expected"), CORPUS, ids=[c[0] for c in CORPUS]
)
def test_filter_refuses_each_case(case, profile, code, expected):
    payload = {"examples": ["a"]} if profile == "B" else None
    result = run(code, Profile(profile), payload, timeout_s=30)
    assert result.ok is False
    assert result.refused
    assert expected in [v.code for v in result.violations]


# Filtre contourné : (identifiant, profil, code, fragment attendu de l'erreur d'exécution)
RUNTIME = [
    ("np-ma", "A", NP + "b = np.ma" + BUILD, "has no attribute 'ma'"),
    ("np-f2py", "A", NP + "o = np.f2py" + BUILD, "has no attribute 'f2py'"),
    ("np-ctypeslib", "A", NP + "c = np.ctypeslib" + BUILD, "has no attribute 'ctypeslib'"),
    ("np-load", "A", NP + "w = np.load" + BUILD, "has no attribute 'load'"),
    ("np-lstsq", "A", NP + "f = np.linalg.lstsq" + BUILD, "has no attribute 'lstsq'"),
    ("import-os", "A", "import os" + BUILD, "ImportError: module non autorisé : os"),
    ("import-sys", "A", "import sys" + BUILD, "ImportError: module non autorisé : sys"),
    ("import-string", "A", "import string" + BUILD, "module non autorisé : string"),
    ("open", "A", "open('x')" + BUILD, "NameError"),
    ("getattr", "A", "getattr(1, 'real')" + BUILD, "NameError"),
    ("type", "A", "t = type(())" + BUILD, "NameError"),
    # Le hook d'audit coupe l'ouverture de fichier en C : NumPy lève une SystemError.
    ("ndarray-tofile", "A", NP + "np.zeros(1).tofile('x.bin')" + BUILD, "'tofile'"),
    ("ndarray-dump", "A", NP + "np.zeros(1).dump('x.pkl')" + BUILD, "module non autorisé"),
    ("audit-import", "A", NP + "np.show_runtime()" + BUILD, "audit refusé : import"),
    ("audit-import-info", "A", NP + "np.info(np.zeros)" + BUILD, "audit refusé : import"),
]


@pytest.mark.parametrize(
    ("case", "profile", "code", "fragment"), RUNTIME, ids=[c[0] for c in RUNTIME]
)
def test_runtime_layer_without_filter(case, profile, code, fragment):
    result = _spawn(code, Profile(profile), None, 30)
    assert result.ok is False
    assert fragment in result.error


@pytest.mark.parametrize(
    ("case", "code", "fragment"),
    [
        ("re-enum-sys", "import re\ns = re.enum.sys", "has no attribute 'enum'"),
        ("re-functools", "import re\nf = re.functools", "has no attribute 'functools'"),
        ("datetime-sys", "import datetime\ns = datetime.sys", "has no attribute 'sys'"),
        ("import-os", "import os", "module non autorisé : os"),
    ],
)
def test_runtime_layer_profile_b(case, code, fragment):
    result = _spawn(code + "\ndef predict(raw):\n    return 1", Profile.B, {"examples": ["a"]}, 30)
    assert result.ok is False
    assert fragment in result.value[0]["error"]


def test_fake_result_frame_on_stdout_has_no_effect():
    forged = '{"ok": true, "value": {"L0.W": {"shape": [1, 1], "dtype": "float32", "data": [9.0]}}}'
    code = NP + f"print('\\x1eNNWW-FRAME 00000000000000000000000000000000 ' + {forged!r})" + BUILD
    result = run(code, Profile.A, None, timeout_s=30)
    assert result.ok is True
    assert result.value["L0.W"].tolist() == [[1.0]]
    assert "NNWW-FRAME" in result.log


# --- D2 : aucun module interdit atteignable depuis les objets exposés ----------------------

FORBIDDEN_MODULES = {"sys", "os", "builtins", "importlib", "subprocess", "ctypes"}
DROP = frozenset(FORBIDDEN_ATTRIBUTES | FITTING_FUNCTIONS)


def _exposed(profile: str) -> dict[str, object]:
    for name in _bootstrap.PROFILE_MODULES[profile]:
        __import__(name)
    tables = _bootstrap._restricted_tables(profile, DROP)
    spaces = _bootstrap._namespaces(tables)
    roots: dict[str, object] = {name: space for name, space in spaces.items() if "." not in name}
    builtins_table = _bootstrap._builtins(spaces, dict(vars(__import__("builtins"))))
    roots.update({f"builtins.{k}": v for k, v in builtins_table.items()})
    return roots


def _walk(roots: dict[str, object], depth: int, cap: int = 400_000) -> list[str]:
    """Parcours en largeur des attributs admis par le filtre ; renvoie les modules atteints."""
    reached: list[str] = []
    keep: list[object] = []
    seen: set[int] = set()
    frontier = list(roots.items())
    for _ in range(depth):
        following = []
        for path, obj in frontier:
            try:
                names = dir(obj)
            except Exception:
                continue
            for name in names:
                if _attribute_violation(name, 0) is not None:
                    continue
                try:
                    value = getattr(obj, name)
                except Exception:
                    continue
                if isinstance(value, types.ModuleType):
                    reached.append(f"{path}.{name} -> {value.__name__}")
                    continue
                if id(value) in seen or len(seen) >= cap:
                    continue
                seen.add(id(value))
                keep.append(value)
                following.append((f"{path}.{name}", value))
        frontier = following
    return reached


def test_profile_a_reaches_no_module():
    roots = _exposed("A")
    np_space = roots["numpy"]
    assert not hasattr(np_space, "ma") and not hasattr(np_space, "lib")
    assert not hasattr(np_space.linalg, "lstsq") and hasattr(np_space.linalg, "norm")
    roots.update(
        {
            "array": np.zeros((2, 2), dtype=np.float32),
            "rng": np.random.default_rng(0),
            "dtype": np.dtype("float32"),
            "scalar": np.float32(1.0),
        }
    )
    reached = _walk(roots, depth=3)
    assert reached == []


def test_profile_b_reaches_no_module():
    import datetime
    import re

    roots = _exposed("B")
    assert not hasattr(roots["re"], "enum")
    roots.update(
        {
            "pattern": re.compile("a+"),
            "match": re.match("a", "a"),
            "datetime": datetime.datetime(2000, 1, 1),
            "delta": datetime.timedelta(days=1),
        }
    )
    reached = _walk(roots, depth=4)
    assert reached == []
    assert not any(m.split(" -> ")[1] in FORBIDDEN_MODULES for m in reached)


def test_walk_detects_modules_on_real_objects():
    import re

    reached = _walk({"re": re}, depth=1)
    assert any(m.endswith("-> enum") for m in reached)
