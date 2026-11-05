"""Une séance complète (`nnww session`, Structural Seed) : réservation au registre, paquet,
prompt système, service d'outils, pilote, puis clôture au registre, même en erreur (AD-11).
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nn_weight_writing.budget import ledger
from nn_weight_writing.config import ModelConfig, Price, ProtocolConfig
from nn_weight_writing.journal.reader import find_last
from nn_weight_writing.providers.types import ModelProvider
from nn_weight_writing.session import prompt
from nn_weight_writing.session.api_driver import ApiLoopDriver
from nn_weight_writing.session.claude_code import ClaudeCodeDriver
from nn_weight_writing.session.refusals import EndReason
from nn_weight_writing.session.service import (
    BUNDLE_DIR,
    JOURNAL_FILE,
    OpenInfo,
    ToolService,
    make_session_id,
)
from nn_weight_writing.tasks.io import materialize_bundle
from nn_weight_writing.tasks.registry import TaskSpec

RUNS_DIR = Path(__file__).resolve().parents[3] / "runs"


@dataclass(frozen=True)
class SessionOutcome:
    session_id: str
    run_dir: Path
    reason: str
    detail: str | None
    billed_usd: float
    cost_equiv_usd: float


def make_provider(model: ModelConfig) -> ModelProvider:
    """Adaptateur du pilote API selon `models.toml` ; `fake` ne s'obtient qu'en test."""
    if model.provider == "openrouter":
        from nn_weight_writing.providers.openrouter import OpenRouterProvider

        return OpenRouterProvider(provider_order=model.provider_order)
    if model.provider == "anthropic":
        from nn_weight_writing.providers.anthropic import AnthropicProvider

        return AnthropicProvider()
    raise ValueError(f"aucun adaptateur réel pour le fournisseur {model.provider}")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_session(
    *,
    task: TaskSpec,
    dataset: str,
    examples: Path,
    method: str,
    model: ModelConfig,
    price: Price,
    protocol: ProtocolConfig,
    attempt: int,
    seed: int,
    lot: int,
    runs_dir: Path | None = None,
    ledger_path: Path | None = None,
    provider: ModelProvider | None = None,
    claude_executable: Sequence[str] = ("claude",),
    claude_config_dir: Path | None = None,
    claude_cwd_root: Path | None = None,
    now: datetime | None = None,
) -> SessionOutcome:
    """Mène une séance ; `ledger.BudgetRefused` si les plafonds refusent l'ouverture."""
    session_id = make_session_id(task.name, method, model.name, attempt, now or datetime.now(UTC))
    run_dir = Path(runs_dir or RUNS_DIR) / str(lot) / session_id
    max_session = protocol.max_session_usd if model.billed else 0.0
    ledger.reserve(session_id, lot, max_session, protocol, ledger_path)
    service: ToolService | None = None
    detail: str | None = None
    try:
        bundle = materialize_bundle(
            examples,
            run_dir / BUNDLE_DIR,
            task=task.name,
            description=task.description,
            encoder=task.codec.encoder_id,
            vocabulary=list(task.vocabulary),
        )
        system = prompt.system_prompt(method, protocol.pass_budget)
        system_path = run_dir / prompt.SYSTEM_PROMPT_FILE
        system_path.write_bytes(system.encode("utf-8"))
        provider_name = provider.name if provider is not None else model.provider
        info = OpenInfo(
            task=task.name,
            dataset=dataset,
            dataset_sha256=_sha256_file(examples),
            method=method,
            model=model.id,
            driver=model.driver,
            provider=provider_name,
            attempt=attempt,
            seed=seed,
            system_prompt_sha256=prompt.sha256_text(system),
            sampling=dict(model.sampling),
            effort=model.effort,
        )
        service = ToolService(run_dir, task.codec, info, protocol)
        task_text = prompt.task_message(bundle)
        if model.driver == "claude_code":
            ClaudeCodeDriver(
                model,
                price,
                executable=claude_executable,
                config_dir=claude_config_dir,
                cwd_root=claude_cwd_root,
            ).run(service, system_path, task_text)
        else:
            ApiLoopDriver(provider or make_provider(model), model, price).run(
                service, system, task_text, max_session
            )
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        if service is not None and not service.ended:
            service.end(EndReason.ERROR, detail)
        raise
    finally:
        totals = service.totals if service is not None else {}
        billed = float(totals.get("billed_usd", 0.0))
        equiv = float(totals.get("cost_equiv_usd", 0.0))
        ledger.close(session_id, lot, billed, equiv, ledger_path)
    end = find_last(run_dir / JOURNAL_FILE, "end") or {}
    return SessionOutcome(
        session_id, run_dir, end.get("reason", ""), end.get("detail"), billed, equiv
    )
