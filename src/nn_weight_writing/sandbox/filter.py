"""Filtre statique du code de l'agent (AD-5, couche 1) et prévention de AD-19.

Le filtre refuse à la soumission ; il ne remplace pas l'isolement du sous-processus
(`sandbox.runner`), qui reste obligatoire. Les codes renvoyés sont des valeurs de
`session.refusals.RefusalCode` (le côté bac à sable n'importe pas `session/`, un test
vérifie la correspondance).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import StrEnum


class Profile(StrEnum):
    """Profil d'exécution : A = script générateur de poids, B = règles."""

    A = "A"
    B = "B"


# Imports autorisés par profil (AD-5). Pour A, les sous-modules exposés par le bac à sable.
ALLOWED_IMPORTS: dict[Profile, frozenset[str]] = {
    Profile.A: frozenset({"numpy", "numpy.linalg", "numpy.random", "numpy.fft"}),
    Profile.B: frozenset({"re", "datetime", "math", "unicodedata"}),
}

FORBIDDEN_NAMES = frozenset(
    {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
        "input",
        "help",
    }
)

FORBIDDEN_ATTRIBUTE_PREFIXES = ("_", "f_", "gi_", "tb_", "co_", "cr_", "ag_")

FORBIDDEN_ATTRIBUTES = frozenset(
    {
        # Liste de AD-5.
        "format",
        "format_map",
        "ma",
        "f2py",
        "ctypeslib",
        "lib",
        "testing",
        "load",
        "save",
        "savez",
        "savez_compressed",
        "savetxt",
        "fromfile",
        "tofile",
        "memmap",
        "loadtxt",
        "genfromtxt",
        "DataSource",
        # Ajouts de 1-5 (D2) : lecture ou écriture de fichiers depuis NumPy, pont ctypes,
        # et noms de modules sensibles, refusés comme attributs quel que soit l'objet.
        "fromregex",
        "dump",
        "ctypes",
        "sys",
        "os",
        "builtins",
        "importlib",
        "subprocess",
        "shutil",
        "socket",
        "io",
        "pickle",
        "marshal",
        # Revue de 1-5 : `str.mro()` expose `object` ; fermé par prudence.
        "mro",
    }
)

# Fonctions d'ajustement de AD-19 : refusées comme nom, attribut ou import. Liste étendue
# à la revue de 1-5 (décision de l'orchestrateur, à confirmer) : tous les solveurs et
# décompositions de `numpy.linalg` de NumPy 2.5, et les ajustements de `numpy.polynomial`.
FITTING_FUNCTIONS = frozenset(
    {
        # Liste de AD-19.
        "lstsq",
        "svd",
        "pinv",
        "eig",
        "eigh",
        "solve",
        "inv",
        "polyfit",
        "cov",
        "corrcoef",
        # Solveurs et décompositions de `numpy.linalg`.
        "tensorsolve",
        "tensorinv",
        "svdvals",
        "eigvals",
        "eigvalsh",
        "qr",
        "cholesky",
        "matrix_rank",
        # `numpy.polynomial` et ses ajustements (jamais exposé, refusé dès le filtre).
        "polynomial",
        "chebfit",
        "legfit",
        "lagfit",
        "hermfit",
        "hermefit",
    }
)

MAX_STRING_BYTES = 8 * 1024
MAX_NUMBERS = 512

# Codes produits par le filtre (valeurs de RefusalCode).
SYNTAX_ERROR = "syntax_error"
FORBIDDEN_IMPORT = "forbidden_import"
FORBIDDEN_NAME = "forbidden_name"
FORBIDDEN_ATTRIBUTE = "forbidden_attribute"
FORBIDDEN_STATEMENT = "forbidden_statement"
ATTRIBUTE_STORE = "attribute_store"
FITTING_FUNCTION = "fitting_function"
LITERALS_TOO_LARGE = "literals_too_large"
CODE_TOO_COMPLEX = "code_too_complex"
FILTER_CODES = frozenset(
    {
        SYNTAX_ERROR,
        FORBIDDEN_IMPORT,
        FORBIDDEN_NAME,
        FORBIDDEN_ATTRIBUTE,
        FORBIDDEN_STATEMENT,
        ATTRIBUTE_STORE,
        FITTING_FUNCTION,
        LITERALS_TOO_LARGE,
        CODE_TOO_COMPLEX,
    }
)


@dataclass(frozen=True)
class Violation:
    """Une raison de refus, avec la ligne du code de l'agent."""

    code: str
    detail: str
    lineno: int = 0


def _attribute_violation(name: str, lineno: int) -> Violation | None:
    if name in FITTING_FUNCTIONS:
        return Violation(FITTING_FUNCTION, f"fonction d'ajustement : {name}", lineno)
    if name.startswith(FORBIDDEN_ATTRIBUTE_PREFIXES) or name in FORBIDDEN_ATTRIBUTES:
        return Violation(FORBIDDEN_ATTRIBUTE, f"attribut interdit : {name}", lineno)
    return None


def _name_violation(name: str, lineno: int) -> Violation | None:
    if name in FITTING_FUNCTIONS:
        return Violation(FITTING_FUNCTION, f"fonction d'ajustement : {name}", lineno)
    if name in FORBIDDEN_NAMES or name.startswith("__"):
        return Violation(FORBIDDEN_NAME, f"nom interdit : {name}", lineno)
    return None


def _import_violations(node: ast.Import | ast.ImportFrom, profile: Profile) -> list[Violation]:
    allowed = ALLOWED_IMPORTS[profile]
    out: list[Violation] = []
    if isinstance(node, ast.ImportFrom):
        if node.level or not node.module:
            return [Violation(FORBIDDEN_IMPORT, "import relatif", node.lineno)]
        modules = [node.module]
    else:
        modules = [alias.name for alias in node.names]
    for module in modules:
        if module not in allowed:
            out.append(Violation(FORBIDDEN_IMPORT, f"import hors profil {profile}: {module}", 0))
            continue
        for part in module.split(".")[1:]:
            violation = _attribute_violation(part, node.lineno)
            if violation:
                out.append(violation)
    for alias in node.names:
        names = [alias.name.split(".")[-1]] if isinstance(node, ast.ImportFrom) else []
        if alias.asname:
            names.append(alias.asname)
        for name in names:
            if name == "*":
                out.append(Violation(FORBIDDEN_IMPORT, "import *", node.lineno))
                continue
            violation = _attribute_violation(name, node.lineno) or _name_violation(
                name, node.lineno
            )
            if violation:
                out.append(violation)
    return [Violation(v.code, v.detail, v.lineno or node.lineno) for v in out]


def _numeric(value: object) -> bool:
    return isinstance(value, int | float | complex) and not isinstance(value, bool)


def check(code: str, profile: Profile) -> list[Violation]:
    """Renvoie la liste des violations ; vide si le code est admis."""
    try:
        tree = ast.parse(code, filename="<agent>", mode="exec")
    except (SyntaxError, ValueError) as exc:
        return [Violation(SYNTAX_ERROR, str(exc), getattr(exc, "lineno", 0) or 0)]
    except (RecursionError, MemoryError) as exc:
        # Expression trop longue ou trop imbriquée pour l'analyseur de CPython.
        return [Violation(CODE_TOO_COMPLEX, f"code trop complexe : {type(exc).__name__}")]
    out: list[Violation] = []
    string_bytes = 0
    numbers = 0
    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import | ast.ImportFrom):
            out.extend(_import_violations(node, profile))
        elif isinstance(node, ast.Global | ast.Nonlocal):
            out.append(Violation(FORBIDDEN_STATEMENT, type(node).__name__.lower(), lineno))
        elif isinstance(node, ast.Name):
            violation = _name_violation(node.id, lineno)
            if violation:
                out.append(violation)
        elif isinstance(node, ast.Attribute):
            violation = _attribute_violation(node.attr, lineno)
            if violation:
                out.append(violation)
            elif profile is Profile.B and isinstance(node.ctx, ast.Store | ast.Del):
                # B : aucun état ne doit survivre d'un exemple à l'autre (AD-5).
                out.append(
                    Violation(ATTRIBUTE_STORE, f"affectation d'attribut {node.attr}", lineno)
                )
        elif isinstance(node, ast.MatchClass):
            # `case C(attr=x)` lit un attribut par son nom, sans nœud Attribute.
            for name in node.kwd_attrs:
                violation = _attribute_violation(name, lineno)
                if violation:
                    out.append(violation)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                # `'\ud800'` échappé dans le source : constante à substitut isolé.
                string_bytes += len(node.value.encode("utf-8", "surrogatepass"))
            elif isinstance(node.value, bytes):
                string_bytes += len(node.value)
            elif _numeric(node.value):
                numbers += 1
    if string_bytes > MAX_STRING_BYTES:
        out.append(
            Violation(LITERALS_TOO_LARGE, f"{string_bytes} octets de chaînes > {MAX_STRING_BYTES}")
        )
    if numbers > MAX_NUMBERS:
        out.append(Violation(LITERALS_TOO_LARGE, f"{numbers} nombres littéraux > {MAX_NUMBERS}"))
    return out
