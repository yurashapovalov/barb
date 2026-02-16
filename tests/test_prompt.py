"""Tests for system prompt and tool description.

System prompt: identity, instrument context, behavioral rules.
Tool description: query syntax, patterns, examples, function reference.
"""

import pytest

from assistant.prompt import build_system_prompt
from assistant.tools import BARB_TOOL


class TestBuildSystemPrompt:
    def test_contains_instrument(self):
        prompt = build_system_prompt("NQ")
        assert "NQ" in prompt
        assert "Nasdaq 100 E-mini" in prompt

    def test_contains_exchange(self):
        prompt = build_system_prompt("NQ")
        assert "CME" in prompt

    def test_contains_sessions(self):
        prompt = build_system_prompt("NQ")
        assert "RTH" in prompt
        assert "09:30" in prompt
        assert "ETH" in prompt

    def test_contains_data_range(self):
        prompt = build_system_prompt("NQ")
        assert "2008" in prompt

    def test_data_shown_separately(self):
        prompt = build_system_prompt("NQ")
        assert "data is shown" in prompt.lower()

    def test_has_structured_sections(self):
        prompt = build_system_prompt("NQ")
        assert "<instrument>" in prompt
        assert "<instructions>" in prompt
        assert "<transparency>" in prompt
        assert "<acknowledgment>" in prompt

    def test_unknown_instrument_raises(self):
        with pytest.raises(ValueError, match="Unknown instrument"):
            build_system_prompt("BOGUS")

    def test_has_percentage_instructions(self):
        prompt = build_system_prompt("NQ")
        assert "percentage" in prompt.lower()
        assert "TWO queries" in prompt

    def test_has_session_instruction(self):
        prompt = build_system_prompt("NQ")
        assert "without session" in prompt.lower()
        assert "settlement" in prompt.lower()

    def test_has_barb_script_fields(self):
        """Tool description has query field names."""
        desc = BARB_TOOL["description"]
        assert "session" in desc
        assert "map" in desc
        assert "where" in desc
        assert "group_by" in desc


class TestToolDescription:
    def test_has_examples(self):
        desc = BARB_TOOL["description"]
        assert "<examples>" in desc
        assert "run_query" in desc
        assert "Example 5" in desc

    def test_has_patterns(self):
        desc = BARB_TOOL["description"]
        assert "<patterns>" in desc
        assert "MACD cross" in desc
        assert "NFP" in desc

    def test_has_follow_up_example(self):
        desc = BARB_TOOL["description"]
        assert "follow-up" in desc.lower()
        assert "2023" in desc

    def test_has_function_reference(self):
        desc = BARB_TOOL["description"]
        assert "rsi" in desc
        assert "atr" in desc
        assert "sma" in desc
