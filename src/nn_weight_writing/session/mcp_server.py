"""Serveur MCP HTTP local du pilote Claude Code (AD-14) sur le catalogue unique (AD-15).

Il expose `catalogue(method)` sous les mêmes noms, schémas et descriptions que le pilote API,
et transmet chaque appel à `ToolService.call`. Il écoute sur 127.0.0.1, port libre, sous un
chemin aléatoire ; il tourne dans un fil à part le temps de la séance.
"""

from __future__ import annotations

import json
import secrets
import socket
import threading
import time

import anyio
import mcp_types as types
import uvicorn
from mcp.server import Server

from nn_weight_writing.journal.writer import json_safe
from nn_weight_writing.session.service import ToolService
from nn_weight_writing.session.tools import catalogue

SERVER_NAME = "nnww"
START_TIMEOUT_S = 20.0


def mcp_tool_name(tool: str) -> str:
    """Nom sous lequel Claude Code présente un outil de ce serveur."""
    return f"mcp__{SERVER_NAME}__{tool}"


def build_server(service: ToolService) -> Server:
    tools = catalogue(service.method)

    async def list_tools(ctx, params) -> types.ListToolsResult:
        return types.ListToolsResult(
            tools=[
                types.Tool(name=t.name, description=t.description, input_schema=t.input_schema)
                for t in tools
            ]
        )

    async def call_tool(ctx, params) -> types.CallToolResult:
        result = await anyio.to_thread.run_sync(service.call, params.name, params.arguments)
        text = json.dumps(json_safe(result), ensure_ascii=False)
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])

    return Server(SERVER_NAME, on_list_tools=list_tools, on_call_tool=call_tool)


class McpToolServer:
    """Contexte : démarre le serveur HTTP dans un fil, expose `url`, l'arrête à la sortie."""

    def __init__(self, service: ToolService) -> None:
        self.service = service
        self.url = ""
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> McpToolServer:
        path = f"/mcp/{secrets.token_urlsafe(16)}"
        app = build_server(self.service).streamable_http_app(streamable_http_path=path)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        config = uvicorn.Config(app, log_level="warning", lifespan="on")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(
            target=self._server.run, kwargs={"sockets": [sock]}, daemon=True
        )
        self._thread.start()
        deadline = time.monotonic() + START_TIMEOUT_S
        while not self._server.started:
            if not self._thread.is_alive() or time.monotonic() > deadline:
                self.__exit__()
                raise RuntimeError("le serveur MCP n'a pas démarré")
            time.sleep(0.02)
        self.url = f"http://127.0.0.1:{port}{path}"
        return self

    def __exit__(self, *exc: object) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=10)

    def mcp_config(self) -> dict:
        """Contenu du fichier `--mcp-config` : ce seul serveur."""
        return {"mcpServers": {SERVER_NAME: {"type": "http", "url": self.url}}}
