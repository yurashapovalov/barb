"""Tests for system prompt generation."""

import pytest

from assistant.prompt import build_system_prompt


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

    def test_contains_run_query_tool(self):
        prompt = build_system_prompt("NQ")
        assert "run_query" in prompt
        assert "ONE tool" in prompt

    def test_has_few_shot_examples(self):
        prompt = build_system_prompt("NQ")
        assert "<examples>" in prompt
        assert "run_query" in prompt
        # Check for Barb Script query structure
        assert "session" in prompt
        assert "from" in prompt
        assert "map" in prompt

    def test_data_shown_separately(self):
        prompt = build_system_prompt("NQ")
        assert "data is shown" in prompt.lower()

    def test_has_structured_sections(self):
        prompt = build_system_prompt("NQ")
        assert "<context>" in prompt
        assert "<instructions>" in prompt
        assert "<examples>" in prompt

    def test_unknown_instrument_raises(self):
        with pytest.raises(ValueError, match="Unknown instrument"):
            build_system_prompt("BOGUS")

    def test_has_percentage_instructions(self):
        prompt = build_system_prompt("NQ")
        # Barb Script approach: two queries for percentage
        assert "percentage" in prompt.lower()
        assert "TWO queries" in prompt

    def test_has_session_instruction(self):
        prompt = build_system_prompt("NQ")
        # Should tell model to use default session for daily+
        assert "session" in prompt.lower()
        assert "daily" in prompt.lower()

    def test_has_follow_up_example(self):
        prompt = build_system_prompt("NQ")
        # Example 5 in the prompt shows follow-up pattern
        assert "Example 5" in prompt
        assert "2023" in prompt  # follow-up period change

    def test_has_barb_script_fields(self):
        prompt = build_system_prompt("NQ")
        # Key Barb Script query fields should be mentioned
        assert "session" in prompt
        assert "from" in prompt
        assert "map" in prompt
        assert "where" in prompt
        assert "group_by" in prompt
        assert "select" in prompt
