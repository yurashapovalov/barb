"""
LLM Models configuration — models and pricing.

Prices in USD per 1M tokens.
"""

from dataclasses import dataclass


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
}

DEFAULT_MODEL = "gemini-3-flash"


def get_model(name: str = DEFAULT_MODEL) -> ModelConfig:
    """Get model config."""
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
