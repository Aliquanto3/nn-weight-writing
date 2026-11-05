"""Format de réseau (AD-3) : schéma, validation, chargement sans pickle, empreintes."""

from __future__ import annotations

import hashlib
import json
import zlib

import numpy as np
import pytest
from conftest import MANIFEST

from nn_weight_writing import network
from nn_weight_writing.network import io as netio
from nn_weight_writing.network.layers import ACTIVATIONS, LAYER_TYPES


def dense(n_in, n_out, activation="relu"):
    return {"type": "dense", "in": n_in, "out": n_out, "activation": activation}


def test_schema_matches_registry():
    schema = json.loads(netio.SCHEMA_PATH.read_text("utf-8"))
    layer = schema["properties"]["layers"]["items"]["properties"]
    assert set(layer["type"]["enum"]) == LAYER_TYPES
    assert set(layer["activation"]["enum"]) == set(ACTIVATIONS)
    assert schema["required"] == ["encoder", "layers"]
    assert set(schema["properties"]["layers"]["items"]["required"]) == netio.LAYER_KEYS
    assert set(schema["properties"]["blocks"]["items"]["required"]) == netio.BLOCK_KEYS
    assert schema["properties"]["layers"]["maxItems"] == netio.MAX_LAYERS


@pytest.mark.parametrize(
    ("manifest", "fragment"),
    [
        ([], "objet"),
        ({**MANIFEST, "extra": 1}, "clé inattendue : extra"),
        ({**MANIFEST, "blocks": []}, "clé inattendue : blocks"),
        ({**MANIFEST, "encoder": ""}, "encoder"),
        ({"encoder": "e", "layers": []}, "layers"),
        ({"encoder": "e", "layers": [dense(2, 2, "gelu")]}, "activation inconnue"),
        ({"encoder": "e", "layers": [dense(2, 3), dense(4, 1)]}, "in différent"),
        ({"encoder": "e", "layers": [dense(2000, 1000)]}, "paramètres"),
        ({"encoder": "e", "layers": [dense(True, 1)]}, "entiers"),
        ({"encoder": "e", "layers": [dense(2, 1, ["relu"])]}, "activation inconnue"),
        ({"encoder": "e", "layers": [{**dense(2, 1), "type": ["dense"]}]}, "type inconnu"),
    ],
)
def test_manifest_errors(manifest, fragment):
    errors = netio.manifest_errors(manifest)
    assert errors and any(fragment in e for e in errors)


def test_valid_manifest_shapes_and_hidden_units():
    assert netio.manifest_errors(MANIFEST) == []
    assert netio.weight_shapes(MANIFEST) == {
        "L0.W": (2, 3),
        "L0.b": (3,),
        "L1.W": (3, 1),
        "L1.b": (1,),
    }
    assert netio.n_params(MANIFEST) == 13
    assert netio.hidden_units(MANIFEST) == {(0, 0), (0, 1), (0, 2)}
    assert netio.hidden_units({"encoder": "e", "layers": [dense(2, 1)]}) == set()


def test_forward_matches_hand_computation():
    weights = {
        "L0.W": np.array([[1, -1, 0.5], [0, 1, 0.5]], dtype=np.float32),
        "L0.b": np.array([0, 0, -1], dtype=np.float32),
        "L1.W": np.array([[1], [1], [1]], dtype=np.float32),
        "L1.b": np.array([0.5], dtype=np.float32),
    }
    y = network.forward(MANIFEST, weights, np.array([[2.0, 1.0]], dtype=np.float32))
    # h = relu([2, -1, 0.5]) = [2, 0, 0.5] ; y = 2.5 + 0.5.
    assert y.dtype == np.float32 and y.tolist() == [[3.0]]


def test_load_refuses_pickled_arrays(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps(MANIFEST), "utf-8")
    np.savez(tmp_path / "weights.npz", **{"L0.W": np.array([object()], dtype=object)})
    with pytest.raises(ValueError, match="allow_pickle"):
        network.load(tmp_path)


def test_load_checks_weight_shapes(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps(MANIFEST), "utf-8")
    weights = {k: np.zeros(s, dtype=np.float32) for k, s in netio.weight_shapes(MANIFEST).items()}
    weights["L1.b"] = np.zeros(2, dtype=np.float32)
    np.savez(tmp_path / "weights.npz", **weights)
    with pytest.raises(network.NetworkError, match="L1.b"):
        network.load(tmp_path)


def test_tree_sha256_is_sorted_lines():
    files = {"b.txt": "2" * 64, "a.txt": "1" * 64}
    expected = hashlib.sha256(f"a.txt {'1' * 64}\nb.txt {'2' * 64}\n".encode()).hexdigest()
    assert network.tree_sha256(files) == expected


def test_weights_zlib_size_follows_key_order():
    weights = {k: np.ones(s, dtype=np.float32) for k, s in netio.weight_shapes(MANIFEST).items()}
    raw = np.ones(13, dtype=np.float32).tobytes()
    assert netio.weights_zlib_size(MANIFEST, weights) == len(zlib.compress(raw, 9))
