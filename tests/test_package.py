import tomllib
from pathlib import Path

import nn_weight_writing


def test_version_matches_pyproject():
    pyproject = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text("utf-8"))
    assert nn_weight_writing.__version__ == pyproject["project"]["version"]
