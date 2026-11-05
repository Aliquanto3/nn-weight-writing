"""Pilote Claude Code (`ClaudeCodeDriver`, AD-14) : `claude -p` par l'abonnement d'Anaël.

`claude` tourne depuis un répertoire courant temporaire vide, sous une racine dont aucun dossier
parent ne porte de fichier de mémoire (`CLAUDE.md`, que Claude Code charge en remontant
l'arborescence ; refus avant lancement sinon), avec un `CLAUDE_CONFIG_DIR` dédié
(connexion unique, aucun réglage ni plugin), sans outil intégré (`--tools ""`), avec le seul
serveur MCP de la séance (`--strict-mcp-config`), le prompt système du pilote API
(`--system-prompt-file`) et la description de tâche sur l'entrée standard. Le pilote lit le flux
`stream-json` : il transmet au service les échanges et l'usage par message (`model_call`,
0 $ facturé) et vérifie à l'initialisation qu'aucun outil, serveur, skill ni plugin tiers n'est
chargé. Les outils passent par le serveur MCP, jamais par le pilote.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import time
from collections.abc import Sequence
from pathlib import Path

from nn_weight_writing.budget.cost import billed_usd, cost_equiv_usd
from nn_weight_writing.config import ModelConfig, Price
from nn_weight_writing.journal.schema import ModelCallEvent
from nn_weight_writing.providers.types import Usage
from nn_weight_writing.session.mcp_server import SERVER_NAME, McpToolServer, mcp_tool_name
from nn_weight_writing.session.refusals import EndReason
from nn_weight_writing.session.service import ToolService
from nn_weight_writing.session.tools import catalogue

DRIVER = "claude_code"
DEFAULT_CONFIG_DIR = Path.home() / ".nnww" / "claude-config"
# Surcharges par l'environnement : dossier de configuration dédié et racine du répertoire courant
# (défaut : dossier temporaire du système ; sous Windows, il est sous le dossier utilisateur).
CONFIG_DIR_ENV = "NNWW_CLAUDE_CONFIG_DIR"
CWD_ROOT_ENV = "NNWW_CLAUDE_CWD_ROOT"
# Fichiers de mémoire que Claude Code lit dans le répertoire courant et chacun de ses parents.
MEMORY_ENTRIES = (
    "CLAUDE.md",
    "CLAUDE.local.md",
    ".claude/CLAUDE.md",
    ".claude/CLAUDE.local.md",
    ".claude/rules",
)
# Variables jamais transmises à `claude` : clés d'API (la séance serait facturée à l'API) et
# réglages qui changeraient le compte, le modèle ou le point d'accès.
STRIPPED_ENV_PREFIXES = ("ANTHROPIC_", "CLAUDE", "OPENROUTER_", "OPENAI_", "AWS_BEARER")
# Entrées d'un dossier de configuration qui chargeraient du contexte ou des outils.
FORBIDDEN_CONFIG_ENTRIES = (
    "CLAUDE.md",
    "plugins",
    "skills",
    "agents",
    "commands",
    "output-styles",
    "hooks",
    "settings.local.json",
)
# Outils de ressources MCP ajoutés par Claude Code à tout serveur MCP ; le nôtre n'en expose pas.
MCP_RESOURCE_TOOLS = frozenset({"ListMcpResourcesTool", "ReadMcpResourceTool"})
USAGE_LIMIT = re.compile(
    r"usage limit|limit reached|hit your limit|rate[ _-]?limit|out of extra usage", re.I
)
USAGE_KEYS = (
    ("input", "input_tokens"),
    ("output", "output_tokens"),
    ("cache_read", "cache_read_input_tokens"),
    ("cache_write", "cache_creation_input_tokens"),
)


def config_dir_problems(path: Path) -> list[str]:
    """Raisons pour lesquelles le dossier ne peut servir de configuration dédiée."""
    if not path.is_dir():
        return [f"{path} absent : connexion unique d'Anaël requise (voir la spec de 1-6)"]
    problems = [f"{name} présent" for name in FORBIDDEN_CONFIG_ENTRIES if (path / name).exists()]
    settings = path / "settings.json"
    if settings.exists():
        try:
            data = json.loads(settings.read_text("utf-8") or "{}")
        except json.JSONDecodeError:
            data = {"?": "illisible"}
        extra = sorted(set(data) - {"$schema"}) if isinstance(data, dict) else ["?"]
        if extra:
            problems.append(f"settings.json non vide : {extra}")
    return problems


def ancestor_memory_files(cwd: Path) -> list[Path]:
    """Fichiers de mémoire présents dans `cwd` ou l'un de ses parents (contamination, AD-14)."""
    # Chemin logique (celui passé à `claude`) et chemin résolu (liens, jonctions, noms courts).
    logical = Path(os.path.abspath(cwd))
    resolved = logical.resolve()
    dirs = dict.fromkeys([logical, *logical.parents, resolved, *resolved.parents])
    return [d / name for d in dirs for name in MEMORY_ENTRIES if (d / name).exists()]


def _kill_tree(process: subprocess.Popen) -> None:
    """Tue `claude` et ses descendants : un petit-enfant qui garderait le tube ouvert bloquerait
    la lecture du flux après la mort du seul parent."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(process.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, 9)
        except OSError:
            pass
    if process.poll() is None:
        process.kill()


def child_env(config_dir: Path, base: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        key: value
        for key, value in (os.environ if base is None else base).items()
        if not key.upper().startswith(STRIPPED_ENV_PREFIXES)
    }
    env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    return env


def build_command(
    executable: Sequence[str],
    model: ModelConfig,
    turn_limit: int,
    system_prompt_path: Path,
    mcp_config_path: Path,
    tool_names: Sequence[str],
) -> list[str]:
    command = [
        *executable,
        "-p",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        str(mcp_config_path),
        "--allowedTools",
        ",".join(mcp_tool_name(name) for name in tool_names),
        "--disable-slash-commands",
        "--system-prompt-file",
        str(system_prompt_path),
        "--model",
        model.id,
        "--max-turns",
        str(turn_limit),
        "--no-session-persistence",
        "--output-format",
        "stream-json",
        "--verbose",
    ]
    if model.effort:
        command += ["--effort", model.effort]
    return command


def init_problems(event: dict, tool_names: Sequence[str]) -> list[str]:
    """Contamination visible dans l'événement `system/init` du flux."""
    expected = {mcp_tool_name(name) for name in tool_names}
    problems = []
    extra_tools = sorted(set(event.get("tools") or []) - expected - MCP_RESOURCE_TOOLS)
    if extra_tools:
        problems.append(f"outils hors catalogue : {extra_tools}")
    servers = event.get("mcp_servers") or []
    names = sorted(s.get("name") if isinstance(s, dict) else str(s) for s in servers)
    if names != [SERVER_NAME]:
        problems.append(f"serveurs MCP : {names}")
    failed = [s for s in servers if isinstance(s, dict) and s.get("status") == "failed"]
    if failed:
        problems.append("serveur MCP de la séance injoignable")
    if event.get("skills"):
        problems.append(f"skills chargées : {event['skills']}")
    if event.get("slash_commands"):
        problems.append(f"commandes chargées : {event['slash_commands']}")
    plugins = [
        p.get("name") if isinstance(p, dict) else str(p)
        for p in event.get("plugins") or []
        if not (isinstance(p, dict) and p.get("path") == "builtin")
    ]
    if plugins:
        problems.append(f"plugins tiers : {plugins}")
    return problems


class _Stream:
    """État de lecture du flux : usage déjà transmis par identifiant de message."""

    def __init__(self) -> None:
        # Claude Code émet un événement `assistant` par bloc de contenu, chacun avec l'usage du
        # message : un `model_call` par événement, mais l'usage n'est compté qu'une fois par
        # identifiant de message (les totaux restent justes).
        self.recorded: dict[str, dict[str, int]] = {}
        self.result: dict | None = None
        self.api_errors: list[str] = []
        self.contamination: list[str] = []
        self.timed_out = False


class ClaudeCodeDriver:
    name = DRIVER

    def __init__(
        self,
        model: ModelConfig,
        price: Price,
        *,
        executable: Sequence[str] = ("claude",),
        config_dir: Path | None = None,
        cwd_root: Path | None = None,
    ) -> None:
        self.model = model
        self.price = price
        self.executable = tuple(executable)
        self.config_dir = Path(config_dir or os.environ.get(CONFIG_DIR_ENV) or DEFAULT_CONFIG_DIR)
        self.cwd_root = Path(cwd_root or os.environ.get(CWD_ROOT_ENV) or tempfile.gettempdir())

    def run(self, service: ToolService, system_prompt_path: Path, task_text: str) -> None:
        """Mène la séance jusqu'à sa fin ; `service.end` est toujours appelé."""
        reason, detail = self._session(service, Path(system_prompt_path), task_text)
        if not service.ended:
            service.end(reason, detail)

    def _session(
        self, service: ToolService, system_prompt_path: Path, task_text: str
    ) -> tuple[EndReason, str | None]:
        problems = config_dir_problems(self.config_dir)
        if problems:
            return EndReason.ERROR, "configuration Claude Code non dédiée : " + "; ".join(problems)
        memory = ancestor_memory_files(self.cwd_root)
        if memory:
            return EndReason.ERROR, (
                "contamination : fichiers de mémoire au-dessus du répertoire courant : "
                + ", ".join(str(p) for p in memory)
                + f" ; choisir une autre racine ({CWD_ROOT_ENV})"
            )
        tool_names = [tool.name for tool in catalogue(service.method)]
        stream = _Stream()
        with (
            tempfile.TemporaryDirectory(dir=self.cwd_root) as tmp,
            McpToolServer(service) as server,
        ):
            cwd = Path(tmp) / "cwd"
            cwd.mkdir()
            mcp_config = Path(tmp) / "mcp.json"
            mcp_config.write_text(json.dumps(server.mcp_config()), "utf-8")
            command = build_command(
                self.executable,
                self.model,
                service.config.turn_limit,
                system_prompt_path,
                mcp_config,
                tool_names,
            )
            code, stderr = self._run_process(command, cwd, task_text, service, tool_names, stream)
        return self._outcome(service, stream, code, stderr)

    def _run_process(
        self,
        command: list[str],
        cwd: Path,
        task_text: str,
        service: ToolService,
        tool_names: list[str],
        stream: _Stream,
    ) -> tuple[int | None, str]:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=child_env(self.config_dir),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name != "nt",
        )
        errors: list[str] = []
        reader = threading.Thread(
            target=lambda: errors.append(process.stderr.read().decode("utf-8", "replace")),
            daemon=True,
        )
        reader.start()

        def expire() -> None:
            stream.timed_out = True
            _kill_tree(process)

        timer = threading.Timer(service.config.session_timeout_s, expire)
        timer.daemon = True
        timer.start()
        try:
            try:
                # Octets UTF-8 tels quels : pas de traduction des fins de ligne sous Windows.
                process.stdin.write(task_text.encode("utf-8"))
                process.stdin.close()
            except OSError:
                pass
            started = time.perf_counter()
            for raw in process.stdout:
                line = raw.decode("utf-8", "replace")
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                self._handle(event, service, tool_names, stream, time.perf_counter() - started)
                started = time.perf_counter()
                if stream.contamination:
                    # Arrêt immédiat du parent, avant tout appel d'outil (sortie de boucle sans
                    # attendre la fin du tube).
                    process.kill()
                    break
            code = process.wait(timeout=60)
        finally:
            timer.cancel()
            if process.poll() is None:
                _kill_tree(process)
                process.wait()
        reader.join(timeout=5)
        return code, "".join(errors)[-2000:]

    def _handle(
        self,
        event: dict,
        service: ToolService,
        tool_names: list[str],
        stream: _Stream,
        duration_s: float,
    ) -> None:
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            stream.contamination = init_problems(event, tool_names)
        elif kind == "assistant":
            message = event.get("message") or {}
            if event.get("error"):
                stream.api_errors.append(f"{event['error']} : {_text(message)}")
            if message.get("model") == "<synthetic>" or event.get("parent_tool_use_id"):
                return
            if not service.ended:
                try:
                    service.record_model_call(self._model_call(message, stream, duration_s))
                except RuntimeError:
                    pass  # séance close entre-temps par le gel (fil du serveur MCP)
        elif kind == "result":
            stream.result = event

    def _model_call(self, message: dict, stream: _Stream, duration_s: float) -> ModelCallEvent:
        """Un `model_call` par événement ; l'usage d'un même message n'est compté qu'une fois."""
        usage = message.get("usage") or {}
        seen = stream.recorded.setdefault(str(message.get("id")), {})
        delta = {}
        for key, source in USAGE_KEYS:
            value = int(usage.get(source) or 0)
            delta[key] = max(value - seen.get(key, 0), 0)
            seen[key] = max(value, seen.get(key, 0))
        equiv = cost_equiv_usd(Usage(**delta), self.price)
        return ModelCallEvent(
            input_tokens=delta["input"],
            output_tokens=delta["output"],
            cache_read_tokens=delta["cache_read"],
            cache_write_tokens=delta["cache_write"],
            cost_equiv_usd=equiv,
            billed_usd=billed_usd(self.model, equiv),
            provider_cost=None,
            duration_s=round(duration_s, 6),
            exchange={
                "message_id": message.get("id"),
                "model": message.get("model"),
                "content": message.get("content") or [],
                "stop_reason": message.get("stop_reason"),
            },
        )

    def _outcome(
        self, service: ToolService, stream: _Stream, code: int | None, stderr: str
    ) -> tuple[EndReason, str | None]:
        if service.ended:
            return EndReason.FROZEN, None
        if stream.contamination:
            return EndReason.ERROR, "contamination : " + "; ".join(stream.contamination)
        if stream.timed_out:
            return EndReason.ERROR, (
                f"délai de séance dépassé ({service.config.session_timeout_s:g} s) : claude tué"
            )
        result = stream.result
        causes = [*stream.api_errors]
        failed = result is not None and (
            result.get("is_error") or result.get("subtype") != "success"
        )
        if failed:
            # Le texte final ne compte que d'une séance en erreur : une réponse réussie qui
            # parle de « rate limit » n'est pas une limite d'usage.
            causes.append(str(result.get("result") or ""))
            causes.append(str(result.get("terminal_reason") or ""))
        joined = " | ".join(c for c in causes if c)
        if USAGE_LIMIT.search(joined) or (
            result is not None and result.get("api_error_status") == 429
        ):
            return EndReason.ERROR, f"usage_limit : {joined}"[:2000]
        if result is None:
            return EndReason.ERROR, f"claude terminé sans résultat (code {code}) : {stderr}"
        if result.get("subtype") == "error_max_turns" or result.get("terminal_reason") in (
            "max_turns",
            "max_turns_reached",
        ):
            return EndReason.TURN_LIMIT, f"{service.config.turn_limit} tours"
        if result.get("is_error") or result.get("subtype") != "success":
            return EndReason.ERROR, f"{result.get('subtype')} : {joined}"[:2000]
        return EndReason.PASS_BUDGET, "l'agent a rendu la main sans geler"


def _text(message: dict) -> str:
    return "".join(
        block.get("text", "")
        for block in message.get("content") or []
        if isinstance(block, dict) and block.get("type") == "text"
    )
