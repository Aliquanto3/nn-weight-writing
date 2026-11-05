"""Faux `claude -p` pour les tests du pilote Claude Code (aucun appel réseau hors 127.0.0.1).

Il lit ses arguments, le prompt système et l'entrée standard, se connecte au serveur MCP de
`--mcp-config`, écrit ce qu'il a reçu dans `NNWW_FAKE_CLAUDE_CAPTURE` puis rejoue le scénario
JSON de `NNWW_FAKE_CLAUDE_SCENARIO` en émettant un flux `stream-json` :

    {"init": {...}, "turns": [{"id", "usage", "text", "calls": [[outil, arguments]],
     "events": n}], "result": {...} | null, "exit_code": 0, "hang": false}
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import Client


def emit(event: dict) -> None:
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def option(argv: list[str], name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv else None


async def main() -> int:
    argv = sys.argv[1:]
    sys.stdout.reconfigure(encoding="utf-8")
    stdin = sys.stdin.buffer.read().decode("utf-8")
    scenario_path = os.environ.get("NNWW_FAKE_CLAUDE_SCENARIO")
    scenario = json.loads(Path(scenario_path).read_text("utf-8")) if scenario_path else {}
    mcp_config = json.loads(Path(option(argv, "--mcp-config")).read_text("utf-8"))
    url = mcp_config["mcpServers"]["nnww"]["url"]
    async with Client(url) as client:
        listed = (await client.list_tools()).tools
        tools = [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in listed
        ]
        capture = os.environ.get("NNWW_FAKE_CLAUDE_CAPTURE")
        if capture:
            cwd = Path.cwd()
            record = {
                "argv": argv,
                "stdin": stdin,
                "system_prompt": Path(option(argv, "--system-prompt-file")).read_text("utf-8"),
                "cwd": str(cwd),
                "cwd_entries": sorted(p.name for p in cwd.iterdir()),
                "config_dir": os.environ.get("CLAUDE_CONFIG_DIR"),
                "sensitive_env": sorted(
                    k
                    for k in os.environ
                    if k.upper().startswith(("ANTHROPIC", "OPENROUTER", "OPENAI"))
                    or (k.upper().startswith("CLAUDE") and k != "CLAUDE_CONFIG_DIR")
                ),
                "mcp_config": mcp_config,
                "tools": tools,
            }
            Path(capture).write_text(json.dumps(record, ensure_ascii=False), "utf-8")
        init = {
            "type": "system",
            "subtype": "init",
            "tools": [f"mcp__nnww__{t['name']}" for t in tools],
            "mcp_servers": [{"name": "nnww", "status": "connected"}],
            "skills": [],
            "slash_commands": [],
            "plugins": [{"name": "cc-plugin-privacy", "path": "builtin"}],
            "model": option(argv, "--model"),
            **scenario.get("init", {}),
        }
        emit(init)
        if scenario.get("hang"):
            await asyncio.sleep(3600)  # `claude` bloqué : le délai de séance doit le tuer
        for n, turn in enumerate(scenario.get("turns", [])):
            calls = turn.get("calls", [])
            content = [{"type": "text", "text": turn["text"]}] if turn.get("text") else []
            content += [
                {
                    "type": "tool_use",
                    "id": f"toolu_{n}_{i}",
                    "name": f"mcp__nnww__{name}",
                    "input": args,
                }
                for i, (name, args) in enumerate(calls)
            ]
            message = {
                "id": turn.get("id", f"msg_{n}"),
                "model": turn.get("model", option(argv, "--model")),
                "role": "assistant",
                "content": content,
                "stop_reason": "tool_use" if calls else "end_turn",
                "usage": turn.get("usage", {}),
            }
            for _ in range(turn.get("events", 1)):
                event = {"type": "assistant", "message": message, "parent_tool_use_id": None}
                if turn.get("error"):
                    event["error"] = turn["error"]
                emit(event)
            for i, (name, args) in enumerate(calls):
                result = await client.call_tool(name, args)
                text = result.content[0].text if result.content else ""
                emit(
                    {
                        "type": "user",
                        "message": {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": f"toolu_{n}_{i}",
                                    "content": text,
                                }
                            ],
                        },
                    }
                )
    result = scenario.get("result", {})
    if result is not None:
        emit(
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "result": "fini",
                "terminal_reason": "completed",
                "total_cost_usd": 0.0,
                **result,
            }
        )
    return int(scenario.get("exit_code", 0))


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
