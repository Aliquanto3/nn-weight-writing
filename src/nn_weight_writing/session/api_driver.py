"""Pilote API (`ApiLoopDriver`, AD-10) : boucle d'outils sur un `ModelProvider`.

Chaque réponse devient un `model_call` (usage, deux coûts, échange) transmis au service d'outils,
seul écrivain du journal ; chaque appel d'outil passe par `ToolService.call`. Fins : gel
(`frozen`), réponse sans appel d'outil (`pass_budget`, AD-6), plafond de séance atteint
(`money_budget`), plafond de tours (`turn_limit`), erreur du fournisseur (`error`).
"""

from __future__ import annotations

import json
import time

from nn_weight_writing.budget.cost import billed_usd, cost_equiv_usd
from nn_weight_writing.config import ModelConfig, Price
from nn_weight_writing.journal.schema import ModelCallEvent
from nn_weight_writing.journal.writer import json_safe
from nn_weight_writing.providers.types import (
    ChatRequest,
    ChatResponse,
    Message,
    ModelProvider,
    TextPart,
    message_to_json,
)
from nn_weight_writing.session.refusals import EndReason
from nn_weight_writing.session.service import ToolService
from nn_weight_writing.session.tools import catalogue

DRIVER = "api"


def decode_arguments(text: str) -> object:
    """Arguments d'un appel d'outil : JSON décodé, ou le texte brut s'il n'est pas du JSON.

    Le service refuse alors l'appel (`invalid_arguments`) sans faire tomber la séance.
    """
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError, RecursionError:
        return text


def model_call_event(
    response: ChatResponse,
    model: ModelConfig,
    price: Price,
    duration_s: float,
    exchange: dict,
) -> ModelCallEvent:
    usage = response.usage
    equiv = cost_equiv_usd(usage, price)
    return ModelCallEvent(
        input_tokens=usage.input,
        output_tokens=usage.output,
        cache_read_tokens=usage.cache_read,
        cache_write_tokens=usage.cache_write,
        cost_equiv_usd=equiv,
        billed_usd=billed_usd(model, equiv),
        provider_cost=usage.provider_cost,
        duration_s=round(duration_s, 6),
        exchange=exchange,
    )


TRUNCATED_STOPS = ("length", "max_tokens")


class ApiLoopDriver:
    name = DRIVER

    def __init__(
        self,
        provider: ModelProvider,
        model: ModelConfig,
        price: Price,
        seed: int | None = None,
    ) -> None:
        self.seed = seed
        self.provider = provider
        self.model = model
        self.price = price

    def run(
        self,
        service: ToolService,
        system: str,
        task_text: str,
        max_session_usd: float,
    ) -> None:
        """Mène la séance jusqu'à sa fin ; `service.end` est toujours appelé."""
        reason, detail = self._loop(service, system, task_text, max_session_usd)
        if not service.ended:
            service.end(reason, detail)

    def _loop(
        self,
        service: ToolService,
        system: str,
        task_text: str,
        max_session_usd: float,
    ) -> tuple[EndReason, str | None]:
        tools = catalogue(service.method)
        messages: list[Message] = [Message("user", (TextPart(task_text),))]
        sent = 0
        for turn in range(1, service.config.turn_limit + 1):
            request = ChatRequest(
                model=self.model.id,
                system=system,
                messages=tuple(messages),
                tools=tools,
                max_tokens=self.model.max_tokens,
                sampling=dict(self.model.sampling),
                effort=self.model.effort,
                seed=self.seed,
            )
            started = time.perf_counter()
            try:
                response = self.provider.complete(request)
            except Exception as exc:  # noqa: BLE001 - toute panne du fournisseur clôt en erreur
                return EndReason.ERROR, f"fournisseur {self.provider.name} : {exc}"
            exchange = {
                "turn": turn,
                "sent": [message_to_json(m) for m in messages[sent:]],
                "response": message_to_json(response.message),
                "stop_reason": response.stop_reason,
                "served_by": response.served_by,
            }
            service.record_model_call(
                model_call_event(
                    response, self.model, self.price, time.perf_counter() - started, exchange
                )
            )
            messages.append(response.message)
            sent = len(messages)
            if max_session_usd > 0 and service.totals["billed_usd"] >= max_session_usd:
                return EndReason.MONEY_BUDGET, f"plafond de séance {max_session_usd:.6f} $ atteint"
            if not response.message.tool_calls and response.stop_reason in TRUNCATED_STOPS:
                # Réponse coupée par `max_tokens` (raisonnement non rendu compris) : ce n'est pas
                # l'agent qui rend la main ; séance perdue par le harnais, à rejouer (AD-14).
                return EndReason.ERROR, (
                    f"réponse tronquée ({response.stop_reason}) à {self.model.max_tokens} jetons"
                )
            if not response.message.tool_calls and not response.message.text.strip():
                # Réponse vide (raisonnement non rendu, `stop`) : ni texte ni outil, même échec
                # qu'une troncature, pas un agent qui rend la main.
                return EndReason.ERROR, (
                    f"réponse vide ({response.stop_reason}) : ni texte ni appel d'outil"
                )
            if not response.message.tool_calls:
                return EndReason.PASS_BUDGET, "l'agent a rendu la main sans geler"
            for call in response.message.tool_calls:
                result = service.call(call.name, decode_arguments(call.arguments))
                if service.ended:
                    return EndReason.FROZEN, None
                text = json.dumps(json_safe(result), ensure_ascii=False)
                messages.append(Message("tool", (TextPart(text),), tool_call_id=call.id))
        return EndReason.TURN_LIMIT, f"{service.config.turn_limit} tours"
