"""Filtre statique du bac à sable : imports par profil, noms, attributs, ajustement, littéraux."""

from __future__ import annotations

import pytest

from nn_weight_writing.sandbox.filter import (
    FILTER_CODES,
    FITTING_FUNCTIONS,
    FORBIDDEN_NAMES,
    MAX_NUMBERS,
    MAX_STRING_BYTES,
    Profile,
    check,
)
from nn_weight_writing.session.refusals import RefusalCode


def codes(code: str, profile: str) -> list[str]:
    return [v.code for v in check(code, Profile(profile))]


def test_filter_codes_are_refusal_codes():
    assert FILTER_CODES <= {c.value for c in RefusalCode}


@pytest.mark.parametrize(
    "code",
    [
        "import numpy as np",
        "import numpy.linalg",
        "from numpy import random, fft",
        "from numpy.fft import rfft",
        "from numpy.linalg import norm as n",
    ],
)
def test_profile_a_allows_numpy(code):
    assert codes(code, "A") == []


@pytest.mark.parametrize(
    "code",
    ["import re", "import math", "import os", "import numpy.ma", "from numpy import ma"],
)
def test_profile_a_refuses_other_imports(code):
    assert codes(code, "A")[0] in {"forbidden_import", "forbidden_attribute"}
    assert codes(code, "A")


@pytest.mark.parametrize(
    "code",
    ["import re", "import datetime", "import math", "import unicodedata", "from re import sub"],
)
def test_profile_b_allows_its_modules(code):
    assert codes(code, "B") == []


@pytest.mark.parametrize(
    "code",
    ["import numpy", "import string", "import os.path", "from . import x", "from re import *"],
)
def test_profile_b_refuses_other_imports(code):
    assert codes(code, "B") == ["forbidden_import"]


@pytest.mark.parametrize("name", sorted(FITTING_FUNCTIONS))
def test_fitting_function_as_attribute(name):
    assert codes(f"import numpy as np\nnp.linalg.{name}(1)", "A") == ["fitting_function"]


@pytest.mark.parametrize(
    "code",
    [
        "from numpy.linalg import lstsq as f",
        "from numpy.linalg import svd",
        "from numpy import polyfit as p",
        "from numpy import cov",
        "import numpy.linalg as la\nla.inv(1)",
        "from numpy import linalg as la\nla.pinv(1)",
        "from numpy import corrcoef as eig2",
        "import numpy as np\nfit = np.linalg\nfit.eigh(1)",
    ],
)
def test_fitting_function_through_import_aliases(code):
    assert "fitting_function" in codes(code, "A")


def test_fitting_name_as_alias_target():
    assert codes("from numpy.linalg import norm as solve", "A") == ["fitting_function"]


@pytest.mark.parametrize("name", sorted(FORBIDDEN_NAMES))
def test_forbidden_names(name):
    assert codes(f"x = {name}", "B") == ["forbidden_name"]


def test_dunder_names_refused_single_underscore_allowed():
    assert codes("x = __builtins__", "B") == ["forbidden_name"]
    assert codes("for _ in range(2):\n    pass", "B") == []


@pytest.mark.parametrize(
    "attr", ["__class__", "_private", "f_back", "gi_frame", "tb_next", "co_code", "cr_frame"]
)
def test_forbidden_attribute_prefixes(attr):
    assert codes(f"x = (1).{attr}", "B") == ["forbidden_attribute"]


def test_statements_and_attribute_store():
    assert codes("def f():\n    global x", "B") == ["forbidden_statement"]
    assert codes("def f():\n    x = 1\n    def g():\n        nonlocal x", "B") == [
        "forbidden_statement"
    ]
    assert codes("import re\nre.memo = 1", "B") == ["attribute_store"]
    assert codes("import re\ndel re.sub", "B") == ["attribute_store"]
    # En A, un script s'exécute une fois : les attributs de ses objets restent permis.
    assert codes("class C:\n    def f(self):\n        self.x = 1", "A") == []


def test_match_class_keyword_attributes():
    code = "match ():\n    case tuple(__class__=c):\n        pass"
    assert codes(code, "B") == ["forbidden_attribute"]


def test_string_literal_limit_in_utf8_bytes():
    assert codes(f'x = "{"a" * MAX_STRING_BYTES}"', "B") == []
    assert codes(f'x = "{"a" * (MAX_STRING_BYTES + 1)}"', "B") == ["literals_too_large"]
    # « é » pèse deux octets : 4097 caractères dépassent 8 Ko.
    assert codes(f'x = "{"é" * 4096}"', "B") == []
    assert codes(f'x = "{"é" * 4097}"', "B") == ["literals_too_large"]
    split = f'x = "{"a" * 5000}"\ny = b"{"b" * 3193}"'
    assert codes(split, "B") == ["literals_too_large"]


def test_numeric_literal_limit():
    def numbers(n: int) -> str:
        return "x = [" + ", ".join(str(i % 7 + 0.5) for i in range(n)) + "]"

    assert codes(numbers(MAX_NUMBERS), "A") == []
    assert codes(numbers(MAX_NUMBERS + 1), "A") == ["literals_too_large"]
    bools = "x = [" + ", ".join(["True"] * 600) + "]"
    assert codes(bools, "A") == []
    complexes = "x = [" + ", ".join(["1j"] * 513) + "]"
    assert codes(complexes, "A") == ["literals_too_large"]


def test_syntax_error():
    assert codes("def (", "A") == ["syntax_error"]
