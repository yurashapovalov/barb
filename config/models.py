"""
LLM Models configuration — models and pricing.

Prices in USD per 1M tokens (text only).
"""

from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing per 1M tokens in USD (text only)."""
    input: float          # Input tokens
    output: float         # Output tokens (including thinking)
    cache: float          # Cached input tokens


@dataclass
class ModelConfig:
    """Model configuration."""
    id: str                           # Model ID for API
    name: str                         # Human-readable name
    pricing: ModelPricing             # Pricing info
    context_window: int               # Max context tokens
    max_output: int                   # Max output tokens
    supports_code_execution: bool     # Can execute code
    supports_thinking: bool           # Has thinking mode


# =============================================================================
# MODELS
# =============================================================================

MODELS = {
    "gemini-3-flash": ModelConfig(
        id="gemini-3-flash-preview",
        name="Gemini 3 Flash",
        pricing=ModelPricing(
            input=0.50,     # $0.50 per 1M tokens
            output=3.00,    # $3.00 per 1M tokens (incl. thinking)
            cache=0.05,     # $0.05 per 1M tokens (cached)
        ),
        context_window=1_000_000,
        max_output=65_536,
        supports_code_execution=True,
        supports_thinking=True,
    ),
}

DEFAULT_MODEL = "gemini-3-flash"


# =============================================================================
# HELPERS
# =============================================================================

def get_model(name: str = DEFAULT_MODEL) -> ModelConfig:
    """Get model config by name."""
    return MODELS.get(name, MODELS[DEFAULT_MODEL])


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Calculate cost for a request.

    Returns dict with:
        - input_cost: Cost for input tokens
        - output_cost: Cost for output tokens
        - total_cost: Total cost
        - breakdown: Human-readable breakdown
    """
    config = get_model(model)
    p = config.pricing

    # Non-cached input
    fresh_input = input_tokens - cached_tokens
    input_cost = (fresh_input / 1_000_000) * p.input
    cache_cost = (cached_tokens / 1_000_000) * p.cache

    # Output
    output_cost = (output_tokens / 1_000_000) * p.output

    total = input_cost + cache_cost + output_cost

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "input_cost": input_cost + cache_cost,
        "output_cost": output_cost,
        "total_cost": total,
        "breakdown": f"in:{fresh_input:,}+cache:{cached_tokens:,}→${input_cost+cache_cost:.4f} + out:{output_tokens:,}→${output_cost:.4f} = ${total:.4f}",
    }


def estimate_monthly(
    requests_per_day: int,
    avg_input: int,
    avg_output: int,
    cache_rate: float = 0.0,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Estimate monthly cost.

    Args:
        requests_per_day: Average requests per day
        avg_input: Average input tokens per request
        avg_output: Average output tokens per request
        cache_rate: 0.0-1.0, portion of input from cache

    Returns dict with monthly estimates.
    """
    per_request = calculate_cost(
        input_tokens=avg_input,
        output_tokens=avg_output,
        cached_tokens=int(avg_input * cache_rate),
        model=model,
    )

    requests_month = requests_per_day * 30
    monthly = per_request["total_cost"] * requests_month

    return {
        "model": model,
        "requests_per_day": requests_per_day,
        "requests_per_month": requests_month,
        "cost_per_request": per_request["total_cost"],
        "monthly_cost": monthly,
    }
