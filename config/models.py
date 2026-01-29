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
    thinking_budget: int | None = None  # None = use thinkingLevel, int = use thinkingBudget


MODELS = {
    "gemini-3-flash": ModelConfig(
        id="gemini-3-flash-preview",
        name="Gemini 3 Flash",
        pricing=ModelPricing(
            input=0.50,
            output=3.00,
            thinking=3.00,
            cache=0.05,
        ),
        context_window=1_000_000,
        max_output=65_536,
    ),
    "gemini-2.5-flash-lite": ModelConfig(
        id="gemini-2.5-flash-lite-preview-09-2025",
        name="Gemini 2.5 Flash Lite",
        pricing=ModelPricing(
            input=0.10,
            output=0.40,
            thinking=0.40,
            cache=0.01,
        ),
        context_window=1_000_000,
        max_output=65_536,
        thinking_budget=512,
    ),
}

DEFAULT_MODEL = "gemini-2.5-flash-lite"


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
