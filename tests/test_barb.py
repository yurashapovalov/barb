"""Unit tests for Barb agent."""

import pytest
from unittest.mock import Mock, patch

from api.barb import Barb, BarbError, Cost, Response


class TestCost:
    def test_default_values(self):
        cost = Cost()
        assert cost.input_tokens == 0
        assert cost.output_tokens == 0
        assert cost.total_cost == 0.0

    def test_with_values(self):
        cost = Cost(input_tokens=100, output_tokens=50, total_cost=0.001)
        assert cost.input_tokens == 100
        assert cost.output_tokens == 50
        assert cost.total_cost == 0.001


class TestResponse:
    def test_response_with_cost(self):
        resp = Response(answer="test", cost=Cost(total_cost=0.01))
        assert resp.answer == "test"
        assert resp.cost.total_cost == 0.01


class TestBarb:
    def test_init_default_instrument(self):
        barb = Barb()
        assert barb.instrument == "NQ"

    def test_init_custom_instrument(self):
        barb = Barb(instrument="ES")
        assert barb.instrument == "ES"

    def test_system_prompt_contains_instrument(self):
        barb = Barb(instrument="NQ")
        prompt = barb._system_prompt()
        assert "NQ" in prompt
        assert "Nasdaq 100" in prompt

    def test_system_prompt_unknown_instrument(self):
        barb = Barb(instrument="UNKNOWN")
        prompt = barb._system_prompt()
        assert prompt == "Unknown instrument"

    def test_holidays_formatting(self):
        barb = Barb()
        holidays = barb._holidays()
        assert "closed" in holidays or "None" in holidays

    def test_events_formatting(self):
        barb = Barb()
        cfg = {"events": ["macro"]}
        events = barb._events(cfg)
        assert "FOMC" in events or "NFP" in events

    @patch('api.barb._get_client')
    def test_ask_success(self, mock_get_client):
        # Mock the Gemini response
        mock_response = Mock()
        mock_response.text = "Test answer"
        mock_response.usage_metadata = Mock(
            prompt_token_count=100,
            candidates_token_count=50,
            thoughts_token_count=0,
            cached_content_token_count=0,
        )

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        barb = Barb()
        result = barb.ask("What is NQ?")

        assert result.answer == "Test answer"
        assert result.cost.input_tokens == 100
        assert result.cost.output_tokens == 50

    @patch('api.barb._get_client')
    @patch('api.barb.time.sleep')  # Don't actually sleep in tests
    def test_ask_retry_on_failure(self, mock_sleep, mock_get_client):
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        barb = Barb()

        with pytest.raises(BarbError) as exc_info:
            barb.ask("What is NQ?")

        assert "Failed after 3 attempts" in str(exc_info.value)
        assert mock_client.models.generate_content.call_count == 3


class TestConfig:
    def test_get_instrument(self):
        from config.market import get_instrument

        nq = get_instrument("NQ")
        assert nq is not None
        assert nq["name"] == "Nasdaq 100 E-mini"
        assert nq["exchange"] == "CME"

    def test_get_instrument_unknown(self):
        from config.market import get_instrument

        result = get_instrument("UNKNOWN")
        assert result is None


class TestModels:
    def test_get_model_default(self):
        from config.models import get_model

        model = get_model()
        assert model.id is not None
        assert model.pricing.input > 0

    def test_calculate_cost(self):
        from config.models import calculate_cost

        result = calculate_cost(1000, 500, 100, 0)
        assert "total_cost" in result
        assert result["total_cost"] > 0
