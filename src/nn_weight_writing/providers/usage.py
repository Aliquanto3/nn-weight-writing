"""Lecture normalisée de l'usage des réponses (constat 1-2), partagée par la sonde et les
adaptateurs : `input` exclut toujours les jetons lus et écrits en cache.
"""

from __future__ import annotations

from typing import Any

from nn_weight_writing.providers.types import Usage


def parse_chat_usage(usage: dict[str, Any] | None) -> dict[str, Any]:
    """Lit le ``usage`` de chat completions. Champs absents : 0 ; ``cost`` absent : ``None``.

    ``prompt_tokens`` inclut les jetons lus et écrits en cache : ``input`` les retire, pour
    avoir la même sémantique que ``input_tokens`` de Messages (``Usage`` de AD-10).
    """
    usage = usage or {}
    details = usage.get("prompt_tokens_details") or {}
    cost = usage.get("cost")
    cache_read = details.get("cached_tokens", 0) or 0
    cache_write = details.get("cache_write_tokens", 0) or 0
    prompt = usage.get("prompt_tokens", 0) or 0
    return {
        "input": max(prompt - cache_read - cache_write, 0),
        "output": usage.get("completion_tokens", 0) or 0,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "cost": float(cost) if cost is not None else None,
    }


def parse_messages_usage(usage: dict[str, Any] | None) -> dict[str, Any]:
    """Lit le ``usage`` de l'endpoint Messages (compatible Anthropic)."""
    usage = usage or {}
    cost = usage.get("cost")
    return {
        "input": usage.get("input_tokens", 0) or 0,
        "output": usage.get("output_tokens", 0) or 0,
        "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
        "cache_write": usage.get("cache_creation_input_tokens", 0) or 0,
        "cost": float(cost) if cost is not None else None,
    }


def to_usage(parsed: dict[str, Any]) -> Usage:
    return Usage(
        input=parsed["input"],
        output=parsed["output"],
        cache_read=parsed["cache_read"],
        cache_write=parsed["cache_write"],
        provider_cost=parsed["cost"],
    )
