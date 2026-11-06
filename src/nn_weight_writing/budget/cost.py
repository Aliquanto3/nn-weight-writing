"""Seule formule de coût (AD-11) : coût équivalent API et coût facturé d'un appel."""

from __future__ import annotations

from nn_weight_writing.config import ModelConfig, Price
from nn_weight_writing.providers.types import Usage


def cost_equiv_usd(usage: Usage, price: Price) -> float:
    """Jetons × tarif daté de `pricing.toml`, quel que soit le pilote ; arrondi à 6 décimales."""
    long_write = min(usage.cache_write_1h, usage.cache_write)
    long_price = price.cache_write if price.cache_write_1h is None else price.cache_write_1h
    micro = (
        usage.input * price.input
        + usage.output * price.output
        + usage.cache_read * price.cache_read
        + (usage.cache_write - long_write) * price.cache_write
        + long_write * long_price
    )
    return round(micro / 1_000_000, 6)


def billed_usd(model: ModelConfig, cost_equiv: float) -> float:
    """0 par l'abonnement ; le calcul tarifaire par une API (Anthropic, OpenRouter)."""
    return cost_equiv if model.billed else 0.0
