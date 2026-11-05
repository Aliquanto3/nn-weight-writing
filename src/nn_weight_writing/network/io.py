"""Format de réseau unique (AD-3) : validation du manifeste, poids, chargement et empreintes."""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import zlib
from pathlib import Path

import numpy as np

from nn_weight_writing.network.layers import ACTIVATIONS, LAYER_TYPES

SCHEMA_PATH = Path(__file__).with_name("manifest.schema.json")
MANIFEST_NAME = "manifest.json"
WEIGHTS_NAME = "weights.npz"
MAX_LAYERS = 16
MAX_UNITS = 100_000
MAX_PARAMS = 1_000_000
LAYER_KEYS = frozenset({"type", "in", "out", "activation"})
BLOCK_KEYS = frozenset({"rule", "types", "units"})


class NetworkError(ValueError):
    """Manifeste ou poids non conformes au format de AD-3."""


def _is_int(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def manifest_errors(manifest: object, *, with_blocks: bool = False) -> list[str]:
    """Écarts au schéma `manifest.schema.json` (validation écrite à la main, même contenu)."""
    if not isinstance(manifest, dict):
        return ["le manifeste doit être un objet"]
    allowed = {"encoder", "layers"} | ({"blocks"} if with_blocks else set())
    errors = [f"clé inattendue : {key}" for key in manifest if key not in allowed]
    encoder = manifest.get("encoder")
    if not isinstance(encoder, str) or not 1 <= len(encoder) <= 200:
        errors.append("encoder : chaîne de 1 à 200 caractères")
    layers = manifest.get("layers")
    if not isinstance(layers, list) or not 1 <= len(layers) <= MAX_LAYERS:
        return [*errors, f"layers : liste de 1 à {MAX_LAYERS} couches"]
    params = 0
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict) or set(layer) != LAYER_KEYS:
            errors.append(f"couche {i} : clés attendues {sorted(LAYER_KEYS)}")
            continue
        if not isinstance(layer["type"], str) or layer["type"] not in LAYER_TYPES:
            errors.append(f"couche {i} : type inconnu {layer['type']!r}")
        if not isinstance(layer["activation"], str) or layer["activation"] not in ACTIVATIONS:
            errors.append(f"couche {i} : activation inconnue {layer['activation']!r}")
        if not (_is_int(layer["in"], 1, MAX_UNITS) and _is_int(layer["out"], 1, MAX_UNITS)):
            errors.append(f"couche {i} : in et out entiers de 1 à {MAX_UNITS}")
            continue
        if i and isinstance(layers[i - 1], dict) and layers[i - 1].get("out") != layer["in"]:
            errors.append(f"couche {i} : in différent du out de la couche {i - 1}")
        params += layer["in"] * layer["out"] + layer["out"]
    if params > MAX_PARAMS:
        errors.append(f"{params} paramètres > {MAX_PARAMS}")
    if "blocks" in manifest and with_blocks:
        errors.extend(_block_shape_errors(manifest["blocks"]))
    return errors


def _block_shape_errors(blocks: object) -> list[str]:
    if not isinstance(blocks, list):
        return ["blocks : liste attendue"]
    errors = []
    for j, block in enumerate(blocks):
        if not isinstance(block, dict) or set(block) != BLOCK_KEYS:
            errors.append(f"bloc {j} : clés attendues {sorted(BLOCK_KEYS)}")
            continue
        rule, types, units = block["rule"], block["types"], block["units"]
        if not isinstance(rule, str) or not 1 <= len(rule.strip()) <= 2000:
            errors.append(f"bloc {j} : règle en texte requise")
        if not isinstance(types, list) or not types or not all(isinstance(t, str) for t in types):
            errors.append(f"bloc {j} : types, liste non vide d'identifiants")
        if (
            not isinstance(units, list)
            or not units
            or not all(
                isinstance(u, list) and len(u) == 2 and all(_is_int(v, 0, MAX_UNITS) for v in u)
                for u in units
            )
        ):
            errors.append(f"bloc {j} : units, liste non vide de [couche, unité]")
    return errors


def validate_manifest(manifest: object, *, with_blocks: bool = False) -> dict:
    errors = manifest_errors(manifest, with_blocks=with_blocks)
    if errors:
        raise NetworkError("; ".join(errors))
    return manifest  # type: ignore[return-value]


def weight_shapes(manifest: dict) -> dict[str, tuple[int, ...]]:
    """Clés des poids dans l'ordre des couches : `L{i}.W` (in, out) puis `L{i}.b` (out,)."""
    shapes: dict[str, tuple[int, ...]] = {}
    for i, layer in enumerate(manifest["layers"]):
        shapes[f"L{i}.W"] = (layer["in"], layer["out"])
        shapes[f"L{i}.b"] = (layer["out"],)
    return shapes


def n_params(manifest: dict) -> int:
    return sum(math.prod(shape) for shape in weight_shapes(manifest).values())


def hidden_units(manifest: dict) -> set[tuple[int, int]]:
    """Unités cachées : toutes les sorties de toutes les couches sauf la dernière."""
    return {
        (i, unit) for i, layer in enumerate(manifest["layers"][:-1]) for unit in range(layer["out"])
    }


def weights_errors(manifest: dict, weights: dict[str, np.ndarray]) -> list[str]:
    shapes = weight_shapes(manifest)
    errors = []
    if set(weights) != set(shapes):
        missing = sorted(set(shapes) - set(weights))
        extra = sorted(set(weights) - set(shapes))
        errors.append(f"clés attendues ; manquantes {missing}, en trop {extra}")
    for key, shape in shapes.items():
        arr = weights.get(key)
        if arr is None:
            continue
        if arr.dtype != np.float32 or arr.shape != shape:
            errors.append(f"{key} : attendu float32 {shape}, reçu {arr.dtype} {arr.shape}")
        elif not np.isfinite(arr).all():
            errors.append(f"{key} : valeurs non finies")
    return errors


def weights_zlib_size(manifest: dict, weights: dict[str, np.ndarray]) -> int:
    """Octets zlib (niveau 9) des poids float32 concaténés dans l'ordre des clés (AD-7)."""
    raw = b"".join(
        np.ascontiguousarray(weights[key], dtype=np.float32).tobytes()
        for key in weight_shapes(manifest)
    )
    return len(zlib.compress(raw, 9))


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Écrit dans un temporaire du même dossier, puis renomme (AD-8)."""
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def weights_bytes(manifest: dict, weights: dict[str, np.ndarray]) -> bytes:
    buffer = io.BytesIO()
    np.savez(buffer, **{key: weights[key] for key in weight_shapes(manifest)})
    return buffer.getvalue()


def manifest_bytes(manifest: dict) -> bytes:
    return (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def load(directory: Path) -> tuple[dict, dict[str, np.ndarray]]:
    """Charge `manifest.json` et `weights.npz` (sans pickle) et valide l'ensemble."""
    directory = Path(directory)
    manifest = json.loads((directory / MANIFEST_NAME).read_text("utf-8"))
    validate_manifest(manifest, with_blocks=True)
    with np.load(directory / WEIGHTS_NAME, allow_pickle=False) as archive:
        weights = {key: archive[key] for key in archive.files}
    errors = weights_errors(manifest, weights)
    if errors:
        raise NetworkError("; ".join(errors))
    return manifest, weights


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(files: dict[str, str]) -> str:
    """sha256 des lignes `nom sha256` triées, une par ligne, fin de ligne `\\n` (AD-8)."""
    lines = "".join(f"{name} {files[name]}\n" for name in sorted(files))
    return sha256_bytes(lines.encode("utf-8"))
