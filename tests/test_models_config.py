"""Tests for config/models.py — pricing and cost calculation."""

from config.models import DEFAULT_MODEL, MODELS, calculate_cost, get_model


class TestGetModel:
    def test_default_model_exists(self):
        assert DEFAULT_MODEL in MODELS

    def test_default_model(self):
        m = get_model()
        assert m.id == MODELS[DEFAULT_MODEL].id

    def test_unknown_model_returns_default(self):
        m = get_model("nonexistent-model")
        assert m.id == get_model(DEFAULT_MODEL).id

    def test_all_models_have_required_fields(self):
        for name, m in MODELS.items():
            assert m.id, f"{name}: missing id"
            assert m.name, f"{name}: missing name"
            assert m.pricing.input >= 0, f"{name}: negative input price"
            assert m.pricing.output >= 0, f"{name}: negative output price"
            assert m.context_window > 0, f"{name}: invalid context_window"


class TestCalculateCost:
    def test_zero_tokens(self):
        result = calculate_cost(input_tokens=0, output_tokens=0)
        assert result["total_cost"] == 0.0

    def test_input_only(self):
        p = get_model().pricing
        result = calculate_cost(input_tokens=1_000_000, output_tokens=0)
        assert result["input_cost"] == p.input
        assert result["output_cost"] == 0.0
        assert result["total_cost"] == p.input

    def test_output_only(self):
        p = get_model().pricing
        result = calculate_cost(input_tokens=0, output_tokens=1_000_000)
        assert result["output_cost"] == p.output
        assert result["total_cost"] == p.output

    def test_cached_tokens_reduce_input_cost(self):
        p = get_model().pricing
        result = calculate_cost(
            input_tokens=1_000_000,
            output_tokens=0,
            cached_tokens=600_000,
        )
        # 400k fresh + 600k cached
        expected = 400_000 / 1_000_000 * p.input + 600_000 / 1_000_000 * p.cache_read
        assert abs(result["input_cost"] - expected) < 1e-10
        assert result["cached_tokens"] == 600_000

    def test_return_structure(self):
        result = calculate_cost(
            input_tokens=100,
            output_tokens=200,
            cached_tokens=10,
        )
        assert set(result.keys()) == {
            "input_tokens",
            "output_tokens",
            "cached_tokens",
            "input_cost",
            "output_cost",
            "total_cost",
        }
