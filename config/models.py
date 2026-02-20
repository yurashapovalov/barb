"""
LLM Models configuration — models and pricing.

Prices in USD per 1M tokens.
"""

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """Pricing per 1M tokens in USD."""

    input: float
    output: float
    cache_read: float
    cache_write: float


@dataclass
class ModelConfig:
    """Model configuration."""

    id: str
    name: str
    pricing: ModelPricing
    context_window: int
    max_output: int


MODELS = {
    "claude-sonnet-4-5": ModelConfig(
        id="claude-sonnet-4-5-20250929",
        name="Claude Sonnet 4.5",
        pricing=ModelPricing(
            input=3.00,
            output=15.00,
            cache_read=0.30,
            cache_write=3.75,
        ),
        context_window=200_000,
        max_output=16_384,
    ),
    "claude-sonnet-4-6": ModelConfig(
        id="claude-sonnet-4-6",
        name="Claude Sonnet 4.6",
        pricing=ModelPricing(
            input=3.00,
            output=15.00,
            cache_read=0.30,
            cache_write=3.75,
        ),
        context_window=200_000,
        max_output=64_000,
    ),
    "claude-haiku-4-5": ModelConfig(
        id="claude-haiku-4-5-20251001",
        name="Claude Haiku 4.5",
        pricing=ModelPricing(
            input=0.80,
            output=4.00,
            cache_read=0.08,
            cache_write=1.00,
        ),
        context_window=200_000,
        max_output=16_384,
    ),
}

DEFAULT_MODEL = "claude-sonnet-4-5"


def get_model(name: str = DEFAULT_MODEL) -> ModelConfig:
    """Get model config."""
    if name not in MODELS:
        log.warning("Unknown model '%s', using default '%s'", name, DEFAULT_MODEL)
    return MODELS.get(name, MODELS[DEFAULT_MODEL])


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Calculate cost for a request."""
    p = get_model(model).pricing

    fresh_input = input_tokens - cached_tokens

    input_cost = (fresh_input / 1_000_000) * p.input
    cache_cost = (cached_tokens / 1_000_000) * p.cache_read
    output_cost = (output_tokens / 1_000_000) * p.output

    total = input_cost + cache_cost + output_cost

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "input_cost": input_cost + cache_cost,
        "output_cost": output_cost,
        "total_cost": total,
    }
