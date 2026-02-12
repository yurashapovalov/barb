"""Tests for system prompt generation.

Detailed tests live in tests/assistant/test_system_prompt.py and
tests/assistant/test_context.py. This file has basic smoke tests.
"""

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

    def test_has_few_shot_examples(self):
        prompt = build_system_prompt("NQ")
        assert "<examples>" in prompt
        assert "run_query" in prompt
        assert "session" in prompt
        assert "map" in prompt

    def test_data_shown_separately(self):
        prompt = build_system_prompt("NQ")
        assert "data is shown" in prompt.lower()

    def test_has_structured_sections(self):
        prompt = build_system_prompt("NQ")
        assert "<instrument>" in prompt
        assert "<instructions>" in prompt
        assert "<examples>" in prompt

    def test_unknown_instrument_raises(self):
        with pytest.raises(ValueError, match="Unknown instrument"):
            build_system_prompt("BOGUS")

    def test_has_percentage_instructions(self):
        prompt = build_system_prompt("NQ")
        assert "percentage" in prompt.lower()
        assert "TWO queries" in prompt

    def test_has_session_instruction(self):
        prompt = build_system_prompt("NQ")
        assert "session" in prompt.lower()
        assert "daily" in prompt.lower()

    def test_has_follow_up_example(self):
        prompt = build_system_prompt("NQ")
        assert "Example 5" in prompt
        assert "2023" in prompt

    def test_has_barb_script_fields(self):
        prompt = build_system_prompt("NQ")
        assert "session" in prompt
        assert "map" in prompt
