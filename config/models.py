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
    input: float      # Input tokens
    output: float     # Output tokens
    thinking: float   # Thinking tokens
    cache: float      # Cached input tokens


@dataclass
class ModelConfig:
    """Model configuration."""
    id: str
    name: str
    pricing: ModelPricing
    context_window: int
    max_output: int
    thinking_budget: int | None = None  # Gemini 2.5: None = dynamic, 0 = off
    thinking_level: str | None = None   # Gemini 3: "minimal", "low", "medium", "high"


MODELS = {
    "gemini-2.5-flash": ModelConfig(
        id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        pricing=ModelPricing(
            input=0.30,
            output=2.50,
            thinking=2.50,
            cache=0.03,
        ),
        context_window=1_000_000,
        max_output=65_536,
        thinking_budget=0,
    ),
}

DEFAULT_MODEL = "gemini-2.5-flash"


def get_model(name: str = DEFAULT_MODEL) -> ModelConfig:
    """Get model config."""
    if name not in MODELS:
        log.warning("Unknown model '%s', using default '%s'", name, DEFAULT_MODEL)
    return MODELS.get(name, MODELS[DEFAULT_MODEL])


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    thinking_tokens: int = 0,
    cached_tokens: int = 0,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Calculate cost for a request."""
    p = get_model(model).pricing

    fresh_input = input_tokens - cached_tokens

    input_cost = (fresh_input / 1_000_000) * p.input
    cache_cost = (cached_tokens / 1_000_000) * p.cache
    output_cost = (output_tokens / 1_000_000) * p.output
    thinking_cost = (thinking_tokens / 1_000_000) * p.thinking

    total = input_cost + cache_cost + output_cost + thinking_cost

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "cached_tokens": cached_tokens,
        "input_cost": input_cost + cache_cost,
        "output_cost": output_cost,
        "thinking_cost": thinking_cost,
        "total_cost": total,
    }
