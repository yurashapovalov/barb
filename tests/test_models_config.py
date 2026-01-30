"""Tests for config/models.py — pricing and cost calculation."""

from config.models import DEFAULT_MODEL, calculate_cost, get_model


class TestGetModel:
    def test_known_model(self):
        m = get_model("gemini-3-flash")
        assert m.id == "gemini-3-flash-preview"
        assert m.name == "Gemini 3 Flash"
        assert m.pricing.input == 0.50
        assert m.pricing.output == 3.00

    def test_default_model(self):
        m = get_model()
        assert m.id == get_model(DEFAULT_MODEL).id

    def test_unknown_model_returns_default(self):
        m = get_model("nonexistent-model")
        assert m.id == get_model(DEFAULT_MODEL).id


class TestCalculateCost:
    def test_zero_tokens(self):
        result = calculate_cost(input_tokens=0, output_tokens=0)
        assert result["total_cost"] == 0.0
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0

    def test_input_only(self):
        # 1M input tokens at $0.10/1M (flash-lite default)
        result = calculate_cost(input_tokens=1_000_000, output_tokens=0)
        assert result["input_cost"] == 0.10
        assert result["output_cost"] == 0.0
        assert result["total_cost"] == 0.10

    def test_output_only(self):
        # 1M output tokens at $0.40/1M (flash-lite default)
        result = calculate_cost(input_tokens=0, output_tokens=1_000_000)
        assert result["output_cost"] == 0.40
        assert result["total_cost"] == 0.40

    def test_mixed(self):
        result = calculate_cost(
            input_tokens=500_000,
            output_tokens=100_000,
            model="gemini-2.5-flash-lite",
        )
        # input: 500k * 0.10 / 1M = 0.05
        # output: 100k * 0.40 / 1M = 0.04
        assert abs(result["input_cost"] - 0.05) < 1e-10
        assert abs(result["output_cost"] - 0.04) < 1e-10
        assert abs(result["total_cost"] - 0.09) < 1e-10

    def test_cached_tokens_reduce_input_cost(self):
        # 1M input, 600k cached → 400k fresh at $0.10 + 600k at $0.01
        result = calculate_cost(
            input_tokens=1_000_000,
            output_tokens=0,
            cached_tokens=600_000,
            model="gemini-2.5-flash-lite",
        )
        # fresh: 400k * 0.10 / 1M = 0.04
        # cache: 600k * 0.01 / 1M = 0.006
        expected = 0.04 + 0.006
        assert abs(result["input_cost"] - expected) < 1e-10
        assert result["cached_tokens"] == 600_000

    def test_thinking_tokens(self):
        result = calculate_cost(
            input_tokens=0,
            output_tokens=0,
            thinking_tokens=1_000_000,
            model="gemini-3-flash",
        )
        # thinking: 1M * 3.00 / 1M = 3.00
        assert result["thinking_cost"] == 3.00
        assert result["total_cost"] == 3.00

    def test_return_structure(self):
        result = calculate_cost(
            input_tokens=100, output_tokens=200, thinking_tokens=50, cached_tokens=10,
        )
        assert set(result.keys()) == {
            "input_tokens", "output_tokens", "thinking_tokens", "cached_tokens",
            "input_cost", "output_cost", "thinking_cost", "total_cost",
        }

    def test_specific_model(self):
        # gemini-3-flash: input=$0.50, output=$3.00
        result = calculate_cost(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            model="gemini-3-flash",
        )
        assert result["input_cost"] == 0.50
        assert result["output_cost"] == 3.00
        assert result["total_cost"] == 3.50
