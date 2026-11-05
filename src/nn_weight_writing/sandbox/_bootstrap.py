"""Amorçage du sous-processus du bac à sable (AD-5, couches 2 et 3).

Lancé par `sandbox.runner` en `python -I <ce fichier>`, sans rien importer du paquet. Lit
sur l'entrée standard une requête JSON `{nonce, profile, code, payload, drop}`, puis :

1. précharge les modules du profil ;
2. compile le code de l'agent ;
3. construit, à la place des modules, des espaces de noms restreints : seuls les attributs
   publics qui ne sont pas des modules y figurent, moins les noms de `drop` (attributs
   interdits et fonctions d'ajustement) ; aucun chemin d'attributs n'y mène à un module ;
4. pose un hook d'audit, défini en fermeture et sans drapeau, qui refuse `open`, `import`,
   l'accès aux cadres et les familles `os.`, `socket.`, `subprocess.`, etc. ;
5. exécute le code dans un espace de noms neuf (un par exemple pour B), avec des builtins
   réduits et `sys.stdout`/`sys.stderr` redirigés vers un tampon (le `log`) ;
6. écrit une seule trame `\\x1eNNWW-FRAME <nonce> <json>` sur la sortie d'origine et sort
   par `os._exit`, sans finaliseurs.
"""

import io
import json
import os
import sys
import types

FRAME_PREFIX = b"\x1eNNWW-FRAME "

SAFE_BUILTINS = (
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "bytearray",
    "bytes",
    "callable",
    "chr",
    "classmethod",
    "complex",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "frozenset",
    "hash",
    "hex",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "oct",
    "ord",
    "pow",
    "print",
    "property",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "staticmethod",
    "str",
    "sum",
    "tuple",
    "zip",
    "ArithmeticError",
    "AssertionError",
    "AttributeError",
    "Exception",
    "IndexError",
    "KeyError",
    "LookupError",
    "NameError",
    "NotImplementedError",
    "OverflowError",
    "RuntimeError",
    "StopIteration",
    "TypeError",
    "ValueError",
    "ZeroDivisionError",
)

BLOCKED_EVENTS = frozenset({"open", "import", "sys._getframe", "sys._current_frames"})
BLOCKED_PREFIXES = (
    "os.",
    "socket.",
    "subprocess.",
    "ctypes.",
    "_winapi.",
    "winreg.",
    "msvcrt.",
    "shutil.",
)

PROFILE_MODULES = {
    "A": ("numpy", "numpy.linalg", "numpy.random", "numpy.fft"),
    "B": ("re", "datetime", "math", "unicodedata"),
}

MAX_LABEL_CHARS = 1000
LOG_LIMIT = 20_000
TRUNCATED = "\n[log tronqué]"


class _CappedLog(io.TextIOBase):
    """Tampon du `log` plafonné à `LOG_LIMIT` caractères : le reste est jeté, marqueur ajouté."""

    def __init__(self, limit):
        super().__init__()
        self._parts = []
        self._size = 0
        self._limit = limit
        self._truncated = False

    def writable(self):
        return True

    def write(self, s):
        if not isinstance(s, str):
            raise TypeError("write() attend une chaîne")
        room = self._limit - self._size
        if room > 0:
            kept = s[:room]
            self._parts.append(kept)
            self._size += len(kept)
        if len(s) > max(room, 0):
            self._truncated = True
        return len(s)

    def getvalue(self):
        text = "".join(self._parts)
        return text + TRUNCATED if self._truncated else text


def _public_attributes(module, drop):
    """Attributs publics déjà chargés d'un module, sans modules ni noms interdits."""
    out = {}
    for name, value in list(vars(module).items()):
        if name.startswith("_") or name in drop or isinstance(value, types.ModuleType):
            continue
        out[name] = value
    return out


def _warm_up_numpy(numpy):
    """Déclenche avant le hook les imports paresseux de NumPy (affichage, aléa, algèbre)."""
    arr = numpy.arange(3, dtype=numpy.float32)
    str(arr)
    repr(arr)
    repr(numpy.float32(1.5))
    str(numpy.zeros((2, 2), dtype=bool))
    numpy.random.default_rng(0).normal(size=2)
    numpy.linalg.norm(arr)
    numpy.fft.fft(arr)


def _restricted_tables(profile, drop):
    """Tables d'attributs par nom de module importable, sous-modules compris."""
    tables = {}
    for name in PROFILE_MODULES[profile]:
        tables[name] = _public_attributes(sys.modules[name], drop)
    return tables


def _namespaces(tables):
    """Espaces de noms neufs (SimpleNamespace) ; les sous-modules pointent vers les leurs."""
    spaces = {name: types.SimpleNamespace(**attrs) for name, attrs in tables.items()}
    for name, space in spaces.items():
        parent, _, child = name.rpartition(".")
        if parent:
            setattr(spaces[parent], child, space)
    return spaces


def _builtins(spaces, real_builtins):
    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level != 0 or name not in spaces:
            raise ImportError(f"module non autorisé : {name}")
        if fromlist:
            return spaces[name]
        return spaces[name.split(".")[0]]

    table = {name: real_builtins[name] for name in SAFE_BUILTINS}
    table["__import__"] = restricted_import
    table["__build_class__"] = real_builtins["__build_class__"]
    return table


def _fresh_globals(tables, real_builtins):
    spaces = _namespaces(tables)
    return {"__builtins__": _builtins(spaces, real_builtins), "__name__": "agent"}


def _describe(exc):
    """Type, message et ligne du code de l'agent, sans module `traceback` (pas de fichiers)."""
    line = 0
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == "<agent>":
            line = tb.tb_lineno
        tb = tb.tb_next
    where = f" (ligne {line})" if line else ""
    return f"{type(exc).__name__}: {exc}{where}"[:2000]


def _encode_weights(value, numpy):
    if not isinstance(value, dict):
        raise TypeError("build() doit renvoyer un dict nom -> tableau")
    out = {}
    for key, array in value.items():
        if not isinstance(key, str):
            raise TypeError("clé de poids non textuelle")
        arr = numpy.asarray(array, dtype=numpy.float32)
        if not bool(numpy.isfinite(arr).all()):
            raise ValueError(f"{key} : valeurs non finies")
        out[key] = {"shape": list(arr.shape), "dtype": "float32", "data": arr.ravel().tolist()}
    return out


def _check_label(label):
    if label is None or isinstance(label, bool | int | str):
        if isinstance(label, str) and len(label) > MAX_LABEL_CHARS:
            raise ValueError("label trop long")
        if isinstance(label, int) and not isinstance(label, bool) and abs(label) > 2**53:
            raise ValueError("label entier hors bornes")
        return label
    if isinstance(label, float) and label == label and abs(label) != float("inf"):
        return label
    raise TypeError(f"label de type non admis : {type(label).__name__}")


def main():
    out = sys.stdout.buffer
    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    nonce = request["nonce"]
    profile = request["profile"]
    payload = request.get("payload")
    drop = frozenset(request["drop"])
    real_builtins = (
        dict(vars(__builtins__))
        if isinstance(__builtins__, types.ModuleType)
        else (dict(__builtins__))
    )

    # 1. Préchargement des modules du profil.
    for name in PROFILE_MODULES[profile]:
        __import__(name)
    numpy = sys.modules.get("numpy")
    if numpy is not None:
        _warm_up_numpy(numpy)

    frame = {"ok": False, "error": None, "value": None}
    log = _CappedLog(LOG_LIMIT)
    try:
        # 2. Compilation.
        compiled = compile(request["code"], "<agent>", "exec")
        tables = _restricted_tables(profile, drop)
    except SyntaxError as exc:
        compiled = None
        frame["error"] = f"SyntaxError: {exc}"

    if compiled is not None:
        # 3. Hook d'audit, en fermeture et sans drapeau : il ne se désarme pas.
        def audit_hook(event, args):
            if event in BLOCKED_EVENTS or event.startswith(BLOCKED_PREFIXES):
                raise RuntimeError(f"événement d'audit refusé : {event}")

        sys.addaudithook(audit_hook)

        # 4. Exécution, sorties redirigées vers le tampon.
        sys.stdout = log
        sys.stderr = log
        try:
            if profile == "A":
                namespace = _fresh_globals(tables, real_builtins)
                exec(compiled, namespace)
                build = namespace.get("build")
                if not callable(build):
                    raise NameError("le script doit définir build()")
                frame["value"] = _encode_weights(build(), numpy)
                frame["ok"] = True
            else:
                labels = []
                for raw in payload["examples"]:
                    namespace = _fresh_globals(tables, real_builtins)
                    try:
                        exec(compiled, namespace)
                        predict = namespace.get("predict")
                        if not callable(predict):
                            raise NameError("les règles doivent définir predict(raw)")
                        labels.append({"label": _check_label(predict(raw))})
                    except Exception as exc:
                        labels.append({"error": _describe(exc)})
                frame["value"] = labels
                frame["ok"] = all("label" in item for item in labels)
                if not frame["ok"]:
                    frame["error"] = "au moins un exemple en erreur"
        except Exception as exc:
            frame["error"] = _describe(exc)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    frame["log"] = log.getvalue()
    out.write(b"\n" + FRAME_PREFIX + nonce.encode("ascii") + b" ")
    out.write(json.dumps(frame, ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n")
    out.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
