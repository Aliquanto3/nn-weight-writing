"""Catalogue d'outils unique (AD-15) et identifiants de séance (AD-12)."""

from __future__ import annotations

from datetime import UTC, datetime

from nn_weight_writing.session.service import ToolService, make_session_id
from nn_weight_writing.session.tools import TOOLS, Method, argument_errors, tools_for


def test_catalogue_matches_spine_table():
    methods = {tool.name: {str(m) for m in tool.methods} for tool in TOOLS}
    assert methods == {
        "declare_network": {"A-program", "A-literal"},
        "write_weights": {"A-literal"},
        "submit_script": {"A-program"},
        "submit_rules": {"B"},
        "run_on_examples": {"A-program", "A-literal", "B"},
        "freeze": {"A-program", "A-literal", "B"},
    }
    assert [t.name for t in tools_for(Method.B)] == ["submit_rules", "run_on_examples", "freeze"]
    mutating = {t.name for t in TOOLS if t.mutates_production}
    assert mutating == {"declare_network", "write_weights", "submit_script", "submit_rules"}


def test_every_tool_has_a_handler():
    for tool in TOOLS:
        assert callable(getattr(ToolService, f"_tool_{tool.name}"))


def test_argument_errors():
    schema = next(t for t in TOOLS if t.name == "write_weights").input_schema
    ok = {"layer": 0, "param": "W", "row_start": 0, "rows": [[1.0]]}
    assert argument_errors(schema, ok) == []
    assert argument_errors(schema, {**ok, "param": "X"}) == ["param : valeur hors de ['W', 'b']"]
    assert argument_errors(schema, {**ok, "layer": True}) == ["layer : type integer attendu"]
    assert argument_errors(schema, {**ok, "row_start": -1}) == ["row_start : minimum 0"]
    assert argument_errors(schema, {**ok, "rows": []}) == ["rows : au moins 1 élément(s)"]
    assert argument_errors(schema, "x") == ["les arguments doivent être un objet"]


def test_session_id_contains_size_target():
    now = datetime(2026, 11, 5, 14, 3, 9, tzinfo=UTC)
    assert make_session_id("legal_s", "A-program", "Claude Sonnet 5.5", 1, now, 10_000) == (
        "legal_s-A-program-1e4-claudesonnet5.5-t1-20261105T140309Z"
    )
    assert make_session_id("legal_s", "A-literal", "m", 1, now, 100_000) == (
        "legal_s-A-literal-1e5-m-t1-20261105T140309Z"
    )


def test_session_id_format():
    now = datetime(2026, 11, 5, 14, 3, 9, tzinfo=UTC)
    assert make_session_id("legal-S", "A-program", "Claude Sonnet 5.5", 2, now) == (
        "legal-S-A-program-claudesonnet5.5-t2-20261105T140309Z"
    )
