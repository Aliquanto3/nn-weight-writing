"""Catalogue d'outils unique (AD-15) : mêmes noms, schémas et méthodes pour tous les pilotes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from nn_weight_writing.providers.types import ToolSchema


class Method(StrEnum):
    """Méthodes de l'agent : A-programme, A-littéral, B (règles)."""

    A_PROGRAM = "A-program"
    A_LITERAL = "A-literal"
    B = "B"


A_METHODS = frozenset({Method.A_PROGRAM, Method.A_LITERAL})
ALL_METHODS = frozenset(Method)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    methods: frozenset[Method]
    mutates_production: bool


def _object(properties: dict, required: tuple[str, ...] = ()) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


_CODE = {"type": "string", "minLength": 1, "maxLength": 200_000}

TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "declare_network",
        "Déclare l'architecture du réseau (manifeste : encoder, layers). Rejouable tant "
        "qu'aucun poids n'est écrit.",
        _object({"manifest": {"type": "object"}}, ("manifest",)),
        A_METHODS,
        True,
    ),
    ToolSpec(
        "write_weights",
        "Écrit une tranche de lignes d'un paramètre : W (forme in x out, une ligne par "
        "entrée) ou b (forme out, un nombre par ligne), à partir de row_start.",
        _object(
            {
                "layer": {"type": "integer", "minimum": 0},
                "param": {"enum": ["W", "b"]},
                "row_start": {"type": "integer", "minimum": 0},
                "rows": {"type": "array", "minItems": 1},
            },
            ("layer", "param", "row_start", "rows"),
        ),
        frozenset({Method.A_LITERAL}),
        True,
    ),
    ToolSpec(
        "submit_script",
        "Soumet un script Python (NumPy seul) qui définit build() -> dict des poids "
        "L{i}.W et L{i}.b ; exécuté dans le bac à sable. N'est pas une passe.",
        _object({"code": _CODE}, ("code",)),
        frozenset({Method.A_PROGRAM}),
        True,
    ),
    ToolSpec(
        "submit_rules",
        "Soumet des règles Python (re, datetime, math, unicodedata) qui définissent "
        "predict(raw) -> label. N'est pas une passe.",
        _object({"code": _CODE}, ("code",)),
        frozenset({Method.B}),
        True,
    ),
    ToolSpec(
        "run_on_examples",
        "Exécute la production courante sur tous les exemples du paquet et renvoie les "
        "sorties, jamais un score. Chaque appel consomme une passe, même invalide.",
        _object({}),
        ALL_METHODS,
        False,
    ),
    ToolSpec(
        "freeze",
        "Gèle la production et clôt la séance. Pour A, blocks est obligatoire : il partitionne "
        "les unités cachées, chaque bloc avec sa règle (rule), ses types visés (types, pris "
        "dans le vocabulaire) et ses unités (units, liste de [couche, unité]).",
        _object({"blocks": {"type": "array"}}),
        ALL_METHODS,
        False,
    ),
)

TOOLS_BY_NAME: dict[str, ToolSpec] = {tool.name: tool for tool in TOOLS}


def tools_for(method: Method | str) -> tuple[ToolSpec, ...]:
    """Le catalogue est le même pour tous ; chaque outil déclare ses méthodes autorisées."""
    method = Method(method)
    return tuple(tool for tool in TOOLS if method in tool.methods)


def catalogue(method: Method | str) -> tuple[ToolSchema, ...]:
    """Outils exposés au modèle, identiques pour le pilote API et le serveur MCP (AD-15)."""
    return tuple(
        ToolSchema(tool.name, tool.description, tool.input_schema) for tool in tools_for(method)
    )


_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
}


def argument_errors(schema: dict, arguments: object) -> list[str]:
    """Validation du sous-ensemble de JSON Schema employé par le catalogue."""
    if not isinstance(arguments, dict):
        return ["les arguments doivent être un objet"]
    properties = schema["properties"]
    errors = [f"argument inconnu : {key}" for key in arguments if key not in properties]
    errors += [f"argument manquant : {key}" for key in schema["required"] if key not in arguments]
    for key, rule in properties.items():
        if key not in arguments:
            continue
        value = arguments[key]
        if "enum" in rule and value not in rule["enum"]:
            errors.append(f"{key} : valeur hors de {rule['enum']}")
            continue
        expected = _TYPES.get(rule.get("type", ""))
        if expected and (not isinstance(value, expected) or isinstance(value, bool)):
            errors.append(f"{key} : type {rule['type']} attendu")
            continue
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(f"{key} : minimum {rule['minimum']}")
        if "minLength" in rule and len(value) < rule["minLength"]:
            errors.append(f"{key} : trop court")
        if "maxLength" in rule and len(value) > rule["maxLength"]:
            errors.append(f"{key} : trop long")
        if "minItems" in rule and len(value) < rule["minItems"]:
            errors.append(f"{key} : au moins {rule['minItems']} élément(s)")
    return errors
