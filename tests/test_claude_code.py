"""Pilote Claude Code (AD-14) avec un faux `claude` : contamination, coûts, fins de séance."""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import time

import pytest
from conftest import TEST_PRICE, claude_model, read_journal, scenario

from nn_weight_writing.budget import ledger
from nn_weight_writing.session import prompt
from nn_weight_writing.session.claude_code import (
    DIRECTORY_CACHE_MAX_DEPTH,
    ancestor_memory_files,
    build_command,
    child_env,
    config_dir_problems,
    init_problems,
)
from nn_weight_writing.session.tools import catalogue
from nn_weight_writing.tasks.io import read_bundle

RULES = 'def predict(raw):\n    return "ok"\n'
FREEZE_TURNS = [
    {
        "id": "msg_1",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 200,
            "cache_read_input_tokens": 5000,
            "cache_creation_input_tokens": 400,
        },
        "calls": [["submit_rules", {"code": RULES}]],
    },
    {
        "id": "msg_2",
        "usage": {"input_tokens": 10, "output_tokens": 20},
        "calls": [["run_on_examples", {}], ["freeze", {}]],
    },
]


def types_of(records: list[dict]) -> list[str]:
    return [r["type"] for r in records]


def test_first_request_holds_only_system_prompt_and_task(session_env, monkeypatch):
    """Test de contamination (AD-14) : ce que reçoit `claude`, et rien d'autre."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-0123456789abcdef")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-0123456789abcdef")
    monkeypatch.setenv("CLAUDE_CODE_USE_BEDROCK", "1")
    capture = scenario(monkeypatch, session_env.tmp, {"turns": FREEZE_TURNS})
    outcome = session_env.run(claude_model(), method="B")
    seen = json.loads(capture.read_text("utf-8"))
    run_dir = outcome.run_dir
    # Prompt système : le fichier commun aux deux pilotes ; entrée standard : la tâche seule.
    assert seen["system_prompt"] == (run_dir / "system_prompt.md").read_text("utf-8")
    assert seen["system_prompt"] == prompt.system_prompt("B", 20)
    assert seen["stdin"] == prompt.task_message(read_bundle(run_dir / "bundle"))
    assert seen["stdin"].startswith("# Tâche : toy\n\nDire si la référence est plausible.")
    # Répertoire courant vide, configuration dédiée, aucune clé ni réglage Claude hérité.
    assert seen["cwd_entries"] == []
    assert seen["config_dir"] == str(session_env.config_dir)
    assert seen["sensitive_env"] == []
    argv = seen["argv"]
    assert argv[argv.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in argv
    assert "--disable-slash-commands" in argv
    assert argv[argv.index("--model") + 1] == "claude-sonnet-5-5"
    assert argv[argv.index("--effort") + 1] == "medium"
    assert argv[argv.index("--max-turns") + 1] == "200"
    assert argv[argv.index("--output-format") + 1] == "stream-json"
    assert "--no-session-persistence" in argv and "--verbose" in argv
    for flag in ("--append-system-prompt", "--settings", "--add-dir", "--agents", "--plugin-dir"):
        assert flag not in argv
    assert argv[argv.index("--allowedTools") + 1] == (
        "mcp__nnww__submit_rules,mcp__nnww__run_on_examples,mcp__nnww__freeze"
    )
    # Seul serveur MCP : celui de la séance, en local.
    servers = seen["mcp_config"]["mcpServers"]
    assert list(servers) == ["nnww"]
    assert servers["nnww"]["url"].startswith("http://127.0.0.1:")
    assert outcome.reason == "frozen"


def test_subscription_billed_zero_and_cost_equiv_journaled(session_env, monkeypatch):
    scenario(monkeypatch, session_env.tmp, {"turns": FREEZE_TURNS})
    outcome = session_env.run(claude_model(), method="B")
    records = read_journal(outcome.run_dir)
    calls = [r for r in records if r["type"] == "model_call"]
    # 1000×1 + 200×2 + 5000×0.1 + 400×1.25 = 2400 µ$ ; 10×1 + 20×2 = 50 µ$.
    assert [c["cost_equiv_usd"] for c in calls] == [0.0024, 0.00005]
    assert [c["billed_usd"] for c in calls] == [0.0, 0.0]
    assert calls[0]["cache_read_tokens"] == 5000 and calls[0]["cache_write_tokens"] == 400
    assert calls[0]["provider_cost"] is None
    end = records[-1]
    assert end["type"] == "end" and end["reason"] == "frozen"
    assert end["totals"]["cost_equiv_usd"] == 0.00245 and end["totals"]["billed_usd"] == 0.0
    assert (outcome.billed_usd, outcome.cost_equiv_usd) == (0.0, 0.00245)
    # Registre : réservation de 0 $ puis clôture à 0 $ facturé, coût équivalent consigné.
    rows = ledger.read(session_env.ledger)
    assert [(r.status, r.reserved_usd, r.billed_usd, r.cost_equiv_usd) for r in rows] == [
        ("reserved", 0.0, 0.0, 0.0),
        ("closed", 0.0, 0.0, 0.00245),
    ]
    # Les outils passent par le serveur MCP : journalisés par le service, dans l'ordre.
    tools = [r["tool"] for r in records if r["type"] == "tool_call"]
    assert tools == ["submit_rules", "run_on_examples", "freeze"]
    assert types_of(records)[0] == "open" and records[0]["driver"] == "claude_code"
    assert records[0]["provider"] == "subscription" and records[0]["effort"] == "medium"


def test_repeated_events_of_one_message_count_usage_once(session_env, monkeypatch):
    turns = [
        {
            "id": "msg_x",
            "events": 3,
            "usage": {"input_tokens": 100, "output_tokens": 10},
            "calls": [],
            "text": "Je m'arrête.",
        }
    ]
    scenario(monkeypatch, session_env.tmp, {"turns": turns})
    outcome = session_env.run(claude_model(), method="B")
    calls = [r for r in read_journal(outcome.run_dir) if r["type"] == "model_call"]
    assert [(c["input_tokens"], c["output_tokens"]) for c in calls] == [(100, 10), (0, 0), (0, 0)]
    assert outcome.reason == "pass_budget"
    assert outcome.detail == "l'agent a rendu la main sans geler"


def test_contaminated_init_ends_in_error(session_env, monkeypatch):
    init = {"tools": ["Bash", "mcp__nnww__freeze"], "skills": ["review"]}
    scenario(monkeypatch, session_env.tmp, {"init": init, "turns": FREEZE_TURNS})
    outcome = session_env.run(claude_model(), method="B")
    assert outcome.reason == "error"
    assert outcome.detail.startswith("contamination : outils hors catalogue : ['Bash']")
    assert "skills chargées : ['review']" in outcome.detail
    records = read_journal(outcome.run_dir)
    assert "freeze" not in [r.get("tool") for r in records]


def test_usage_limit_ends_in_error_with_cause(session_env, monkeypatch):
    data = {
        "turns": [
            {
                "id": "msg_1",
                "model": "<synthetic>",
                "text": "Claude AI usage limit reached|1762380000",
                "error": "rate_limit",
            }
        ],
        "result": {"is_error": True, "result": "Claude AI usage limit reached|1762380000"},
    }
    scenario(monkeypatch, session_env.tmp, data)
    outcome = session_env.run(claude_model(), method="B")
    assert outcome.reason == "error"
    assert outcome.detail.startswith("usage_limit : rate_limit : Claude AI usage limit reached")
    records = read_journal(outcome.run_dir)
    # Message synthétique : pas un appel au modèle.
    assert "model_call" not in types_of(records)
    assert ledger.read(session_env.ledger)[-1].status == "closed"


def test_max_turns_ends_in_turn_limit(session_env, monkeypatch):
    data = {
        "turns": [{"id": "m", "usage": {"input_tokens": 5}, "calls": [["run_on_examples", {}]]}],
        "result": {"subtype": "error_max_turns", "is_error": True, "result": ""},
    }
    scenario(monkeypatch, session_env.tmp, data)
    outcome = session_env.run(claude_model(), method="B")
    assert (outcome.reason, outcome.detail) == ("turn_limit", "200 tours")


def test_api_error_ends_in_error(session_env, monkeypatch):
    data = {"result": {"is_error": True, "result": "Not logged in", "terminal_reason": "api_error"}}
    scenario(monkeypatch, session_env.tmp, data)
    outcome = session_env.run(claude_model(), method="B")
    assert outcome.reason == "error"
    assert outcome.detail == "success : Not logged in | api_error"


def test_process_without_result_ends_in_error(session_env, monkeypatch):
    scenario(monkeypatch, session_env.tmp, {"result": None, "exit_code": 3})
    outcome = session_env.run(claude_model(), method="B")
    assert outcome.reason == "error"
    assert outcome.detail.startswith("claude terminé sans résultat (code 3)")


def test_session_timeout_kills_process_tree(session_env, monkeypatch, protocol):
    """Un descendant de `claude` qui garde le tube ouvert est tué avec lui (aucun orphelin)."""
    pid_file = session_env.tmp / "child.pid"
    scenario(monkeypatch, session_env.tmp, {"hang": True, "hang_child": str(pid_file)})
    fast = dataclasses.replace(protocol, session_timeout_s=3)
    started = time.monotonic()
    outcome = session_env.run(claude_model(), method="B", protocol=fast)
    assert time.monotonic() - started < 30
    assert (outcome.reason, outcome.detail) == (
        "error",
        "délai de séance dépassé (3 s) : claude tué",
    )
    assert not _alive(int(pid_file.read_text("utf-8")))


def _alive(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, check=False
        ).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@pytest.mark.parametrize("entry", ["CLAUDE.md", "skills"])
def test_config_dir_not_dedicated_refused_before_launch(session_env, monkeypatch, entry):
    capture = scenario(monkeypatch, session_env.tmp, {"turns": FREEZE_TURNS})
    target = session_env.config_dir / entry
    if entry.endswith(".md"):
        target.write_text("# global", "utf-8")
    else:
        (target / "mes-skills").mkdir(parents=True)
    outcome = session_env.run(claude_model(), method="B")
    assert outcome.reason == "error"
    expected = f"{entry} présent" if entry.endswith(".md") else "skills présent : ['mes-skills']"
    assert outcome.detail == f"configuration Claude Code non dédiée : {expected}"
    assert not capture.exists()


def test_config_dir_problems(tmp_path):
    missing = tmp_path / "absent"
    assert config_dir_problems(missing) == [
        f"{missing} absent : connexion unique d'Anaël requise (voir la spec de 1-6)"
    ]
    (tmp_path / "settings.json").write_text('{"$schema": "x"}', "utf-8")
    assert config_dir_problems(tmp_path) == []
    (tmp_path / "settings.json").write_text('{"enabledPlugins": {}, "hooks": {}}', "utf-8")
    assert config_dir_problems(tmp_path) == ["settings.json non vide : ['enabledPlugins', 'hooks']"]


def test_config_dir_plugins_cache_only_admitted(tmp_path):
    assert config_dir_problems(tmp_path) == []  # plugins absent
    plugins = tmp_path / "plugins"
    (plugins / "marketplaces" / "claude-plugins-official").mkdir(parents=True)
    (plugins / "known_marketplaces.json").write_text("{}", "utf-8")
    assert config_dir_problems(tmp_path) == []  # cache de place de marché seul
    (plugins / "installed_plugins.json").write_text('{"version": 2, "plugins": {}}', "utf-8")
    assert config_dir_problems(tmp_path) == []  # table vide
    (plugins / "plugin-directory-cache-v2.json").write_text('{"listings": []}', "utf-8")
    assert config_dir_problems(tmp_path) == []  # catalogue des places de marché


def _cache_problems(tmp_path, content=None, directory=False, name="plugin-directory-cache-v2.json"):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    if directory:
        (plugins / name).mkdir()
    else:
        (plugins / name).write_text(content, "utf-8")
    return config_dir_problems(tmp_path)


def test_config_dir_directory_cache_real_shape_admitted(tmp_path):
    listing = {
        "id": "plugin_01",
        "name": "X",
        "summary": "s",
        "release": {"version": "1"},
        "links": {},
        "surfaces": ["claude_code"],
        "source": {"type": "github"},
        "checks": {"review": {"state": "ok"}},
    }
    data = {
        "schemaVersion": 2,
        "fetchedAt": "2026-11-06T07:31:57Z",
        "listings": [listing],
        "entryNames": {"plugin_01": "x"},
        "entryNameClaims": {"plugin_01": {"repositoryKey": "github.com/a/b#", "lastSeen": "t"}},
    }
    assert _cache_problems(tmp_path, json.dumps(data)) == []


@pytest.mark.parametrize(
    "content",
    [
        '{"listings": [{"id": "p", "installed": true}]}',  # fiche marquée installée
        '{"listings": [], "enabledPlugins": {"x@y": true}}',  # clé inconnue d'activation
        '{"listings": [], "plugins": {"x": {}}}',  # clé inconnue
        '{"listings": {"x": 1}}',  # listings n'est pas une liste
        "[]",  # pas un objet
        "{pas du json",
    ],
)
def test_config_dir_directory_cache_unknown_shape_refused(tmp_path, content):
    assert _cache_problems(tmp_path, content) == [
        "plugins/plugin-directory-cache-v2.json de forme inconnue"
    ]


def test_config_dir_directory_cache_too_deep_refused(tmp_path):
    levels = DIRECTORY_CACHE_MAX_DEPTH  # racine = 1, donc profondeur totale = max + 1
    deep = '{"listings": ' + "[" * levels + "]" * levels + "}"
    assert _cache_problems(tmp_path, deep) == [
        "plugins/plugin-directory-cache-v2.json de forme inconnue"
    ]


def test_config_dir_directory_cache_max_depth_admitted(tmp_path):
    levels = DIRECTORY_CACHE_MAX_DEPTH - 1  # profondeur totale = max exactement
    deep = '{"listings": ' + "[" * levels + "]" * levels + "}"
    assert _cache_problems(tmp_path, deep) == []


def test_config_dir_directory_cache_extreme_depth_refused(tmp_path):
    deep = '{"listings": ' + "[" * 100_000 + "]" * 100_000 + "}"
    assert _cache_problems(tmp_path, deep) == [
        "plugins/plugin-directory-cache-v2.json de forme inconnue"
    ]


def test_config_dir_directory_cache_symlink_refused(tmp_path):
    target = tmp_path / "ailleurs.json"
    target.write_text('{"listings": []}', "utf-8")
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    try:
        (plugins / "plugin-directory-cache-v2.json").symlink_to(target)
    except OSError:
        pytest.skip("liens symboliques non permis sur ce poste")
    assert config_dir_problems(tmp_path) == [
        "plugins/plugin-directory-cache-v2.json de forme inconnue"
    ]


def test_config_dir_directory_cache_as_directory_refused(tmp_path):
    assert _cache_problems(tmp_path, directory=True) != []


def test_config_dir_directory_cache_neighbour_name_refused(tmp_path):
    problems = _cache_problems(tmp_path, '{"listings": []}', name="plugin-directory-cache-v3.json")
    assert problems == ["plugins présent : ['plugin-directory-cache-v3.json']"]


def test_config_dir_synced_account_copies_admitted(tmp_path):
    (tmp_path / "skills" / "synced").mkdir(parents=True)
    (tmp_path / "plugins" / "synced").mkdir(parents=True)
    (tmp_path / "plugins" / "store").mkdir()
    assert config_dir_problems(tmp_path) == []
    (tmp_path / "skills" / "perso").mkdir()
    assert config_dir_problems(tmp_path) == ["skills présent : ['perso']"]


def test_config_dir_installed_plugin_refused(tmp_path):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "installed_plugins.json").write_text(
        '{"version": 2, "plugins": {"x@y": [{"scope": "user"}]}}', "utf-8"
    )
    assert config_dir_problems(tmp_path) == ["plugin installé"]
    (plugins / "installed_plugins.json").write_text("pas du json", "utf-8")
    assert config_dir_problems(tmp_path) == ["plugin installé"]
    (plugins / "installed_plugins.json").unlink()
    (plugins / "cache").mkdir()
    assert config_dir_problems(tmp_path) == ["plugins présent : ['cache']"]


def test_config_dir_settings_theme_admitted_other_key_refused(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text('{"theme": "dark"}', "utf-8")
    assert config_dir_problems(tmp_path) == []
    settings.write_text('{"theme": "dark", "model": "opus"}', "utf-8")
    assert config_dir_problems(tmp_path) == ["settings.json non vide : ['model']"]


def test_child_env_strips_keys_and_claude_settings(tmp_path):
    base = {
        "PATH": "p",
        "ANTHROPIC_API_KEY": "k",
        "anthropic_base_url": "u",
        "OPENROUTER_API_KEY": "k",
        "CLAUDECODE": "1",
        "CLAUDE_CONFIG_DIR": "ailleurs",
        "OPENAI_API_KEY": "k",
    }
    assert child_env(tmp_path, base) == {"PATH": "p", "CLAUDE_CONFIG_DIR": str(tmp_path)}


def test_build_command_without_effort(tmp_path):
    command = build_command(
        ("claude",),
        claude_model(effort=None),
        7,
        tmp_path / "s.md",
        tmp_path / "m.json",
        ["freeze"],
    )
    assert "--effort" not in command
    assert command[:4] == ["claude", "-p", "--tools", ""]
    assert command[command.index("--max-turns") + 1] == "7"


def test_init_problems():
    names = [t.name for t in catalogue("B")]
    good = {
        "tools": ["mcp__nnww__freeze", "ListMcpResourcesTool"],
        "mcp_servers": [{"name": "nnww", "status": "connected"}],
        "plugins": [{"name": "cc-plugin-privacy", "path": "builtin"}],
    }
    assert init_problems(good, names) == []
    bad = {
        "tools": ["Read"],
        "mcp_servers": [{"name": "nnww", "status": "failed"}, {"name": "github"}],
        "plugins": [{"name": "superpowers", "path": "/x"}],
        "slash_commands": ["/review"],
    }
    assert init_problems(bad, names) == [
        "outils hors catalogue : ['Read']",
        "serveurs MCP : ['github', 'nnww']",
        "serveur MCP de la séance injoignable",
        "commandes chargées : ['/review']",
        "plugins tiers : ['superpowers']",
    ]
    builtin = ["claude", "Explore", "general-purpose", "Plan", "statusline-setup"]
    assert init_problems({**good, "agents": builtin}, names) == []
    assert init_problems({**good, "agents": [*builtin, "relecteur"]}, names) == [
        "agents hors intégrés : ['relecteur']"
    ]


def test_config_dir_skills_file_refused(tmp_path):
    (tmp_path / "skills").write_text("x", "utf-8")
    assert config_dir_problems(tmp_path) == ["skills présent"]


def test_config_dir_installed_plugins_not_utf8_refused(tmp_path):
    (tmp_path / "plugins").mkdir()
    (tmp_path / "plugins" / "installed_plugins.json").write_bytes(bytes([0xFF, 0xFE, 0x7B]))
    assert config_dir_problems(tmp_path) == ["plugin installé"]


def test_session_cost_reconciled_with_result_usage_and_1h_cache(session_env, monkeypatch):
    """Flux réel de Claude Code : `output_tokens` partiels dans les événements `assistant`, cache
    écrit en tranche d'une heure, total exact dans `result.usage` (arrivé après le gel)."""
    price = dataclasses.replace(TEST_PRICE, cache_write_1h=2.0)
    turns = [
        {
            "id": "msg_1",
            "usage": {
                "input_tokens": 3,
                "output_tokens": 5,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 1000,
                "cache_creation": {
                    "ephemeral_5m_input_tokens": 0,
                    "ephemeral_1h_input_tokens": 1000,
                },
            },
            "calls": [["submit_rules", {"code": RULES}]],
        },
        {
            "id": "msg_2",
            "usage": {"input_tokens": 2, "output_tokens": 4, "cache_read_input_tokens": 1000},
            "calls": [["run_on_examples", {}], ["freeze", {}]],
        },
        # Message après le gel (texte de fin) : compté, le journal est encore ouvert.
        {"id": "msg_3", "usage": {"input_tokens": 1, "output_tokens": 1}, "text": "Gelé."},
    ]
    final = {
        "input_tokens": 6,
        "output_tokens": 900,
        "cache_read_input_tokens": 2000,
        "cache_creation_input_tokens": 1200,
        "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 1200},
    }
    result = {"usage": final, "total_cost_usd": 0.0042}
    scenario(monkeypatch, session_env.tmp, {"turns": turns, "result": result})
    outcome = session_env.run(claude_model(), method="B", price=price)
    records = read_journal(outcome.run_dir)
    assert outcome.reason == "frozen"
    assert types_of(records)[-3:] == ["model_call", "model_call", "end"]
    calls = [r for r in records if r["type"] == "model_call"]
    # msg_1 : 3×1 + 5×2 + 1000×2 (tranche 1 h) = 2013 µ$.
    assert calls[0]["cache_write_1h_tokens"] == 1000 and calls[0]["cost_equiv_usd"] == 0.002013
    last = calls[-1]
    assert last["exchange"]["reconciliation"] == "result.usage"
    assert last["exchange"]["total_cost_usd"] == 0.0042
    # Écart : entrée 6-6, sortie 900-10, lecture 2000-1000, écriture 1200-1000 (1 h).
    assert (last["input_tokens"], last["output_tokens"]) == (0, 890)
    assert (last["cache_read_tokens"], last["cache_write_tokens"]) == (1000, 200)
    assert last["cache_write_1h_tokens"] == 200
    totals = records[-1]["totals"]
    assert (totals["output_tokens"], totals["cache_write_tokens"]) == (900, 1200)
    # Total de séance = `result.usage` au tarif : 6×1 + 900×2 + 2000×0,1 + 1200×2 = 4406 µ$.
    assert totals["cost_equiv_usd"] == 0.004406 == outcome.cost_equiv_usd
    rows = ledger.read(session_env.ledger)
    assert rows[-1].cost_equiv_usd == 0.004406


def test_tool_call_after_freeze_refused_and_not_journaled(session_env, monkeypatch):
    turns = [
        *FREEZE_TURNS,
        {"id": "msg_3", "usage": {"input_tokens": 1}, "calls": [["run_on_examples", {}]]},
    ]
    scenario(monkeypatch, session_env.tmp, {"turns": turns})
    outcome = session_env.run(claude_model(), method="B")
    records = read_journal(outcome.run_dir)
    tools = [r["tool"] for r in records if r["type"] == "tool_call"]
    assert tools == ["submit_rules", "run_on_examples", "freeze"]
    assert outcome.reason == "frozen" and records[-1]["type"] == "end"


def test_successful_answer_mentioning_rate_limit_is_not_usage_limit(session_env, monkeypatch):
    data = {"result": {"result": "J'ai lu « rate limit » dans un exemple ; je rends la main."}}
    scenario(monkeypatch, session_env.tmp, data)
    outcome = session_env.run(claude_model(), method="B")
    assert (outcome.reason, outcome.detail) == ("pass_budget", "l'agent a rendu la main sans geler")


def test_session_timeout_kills_hung_claude(session_env, monkeypatch, protocol):
    scenario(monkeypatch, session_env.tmp, {"hang": True})
    fast = dataclasses.replace(protocol, session_timeout_s=1.5)
    started = time.monotonic()
    outcome = session_env.run(claude_model(), method="B", protocol=fast)
    assert time.monotonic() - started < 60
    assert (outcome.reason, outcome.detail) == (
        "error",
        "délai de séance dépassé (1.5 s) : claude tué",
    )
    assert ledger.read(session_env.ledger)[-1].status == "closed"


@pytest.mark.parametrize("entry", ["CLAUDE.md", "CLAUDE.local.md", ".claude/CLAUDE.md"])
def test_memory_file_above_cwd_refused_before_launch(session_env, monkeypatch, entry):
    """Claude Code charge les `CLAUDE.md` des parents du répertoire courant (AD-14)."""
    capture = scenario(monkeypatch, session_env.tmp, {"turns": FREEZE_TURNS})
    parent = session_env.cwd_root / f"parent-{entry.replace('/', '_')}"
    root = parent / "racine"
    root.mkdir(parents=True)
    memory = parent / entry
    memory.parent.mkdir(exist_ok=True)
    memory.write_text("# consignes parasites", "utf-8")
    outcome = session_env.run(claude_model(), method="B", claude_cwd_root=root)
    assert outcome.reason == "error"
    assert outcome.detail.startswith("contamination : fichiers de mémoire au-dessus")
    assert str(memory) in outcome.detail
    assert not capture.exists()


def test_ancestor_memory_files(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    assert ancestor_memory_files(tmp_path / "a" / "b") == ancestor_memory_files(tmp_path)
    (tmp_path / "a" / "CLAUDE.md").write_text("x", "utf-8")
    found = ancestor_memory_files(tmp_path / "a" / "b")
    assert (tmp_path / "a" / "CLAUDE.md").resolve() in found


def test_ancestor_memory_files_follows_logical_and_resolved_paths(tmp_path):
    """Un lien vers une racine propre ne masque pas un `CLAUDE.md` au-dessus du lien."""
    (tmp_path / "propre").mkdir()
    (tmp_path / "salie").mkdir()
    (tmp_path / "salie" / "CLAUDE.md").write_text("x", "utf-8")
    link = tmp_path / "salie" / "lien"
    try:
        link.symlink_to(tmp_path / "propre", target_is_directory=True)
    except OSError:
        pytest.skip("liens symboliques non permis")
    assert ancestor_memory_files(tmp_path / "propre") == []
    assert ancestor_memory_files(link) == [tmp_path / "salie" / "CLAUDE.md"]


def test_timeout_after_freeze_keeps_frozen(session_env, monkeypatch, protocol):
    """Gel puis `claude` bloqué : le délai le tue, la séance reste gelée, le registre est clos."""
    scenario(monkeypatch, session_env.tmp, {"turns": FREEZE_TURNS, "hang_after_turns": True})
    fast = dataclasses.replace(protocol, session_timeout_s=3)
    outcome = session_env.run(claude_model(), method="B", protocol=fast)
    records = read_journal(outcome.run_dir)
    assert outcome.reason == "frozen" and records[-1]["type"] == "end"
    assert records[-1]["passes_used"] == 1
    assert ledger.read(session_env.ledger)[-1].status == "closed"


def test_error_after_freeze_keeps_frozen_and_is_raised(session_env, monkeypatch):
    """`result.usage` illisible après le gel : erreur remontée et consignée, séance gelée."""
    result = {"usage": {"output_tokens": "n/a"}}
    scenario(monkeypatch, session_env.tmp, {"turns": FREEZE_TURNS, "result": result})
    with pytest.raises(ValueError):
        session_env.run(claude_model(), method="B")
    (run_dir,) = (session_env.ledger.parent / "runs").rglob("journal.jsonl")
    end = read_journal(run_dir.parent)[-1]
    assert end["type"] == "end" and end["reason"] == "frozen"
    assert end["detail"].startswith("ValueError")
    assert ledger.read(session_env.ledger)[-1].status == "closed"
