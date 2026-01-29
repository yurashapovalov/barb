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

    def test_contains_rules(self):
        prompt = build_system_prompt("NQ")
        assert "get_query_reference" in prompt
        assert "error" in prompt.lower()

    def test_has_few_shot_examples(self):
        prompt = build_system_prompt("NQ")
        assert "<examples>" in prompt
        assert "execute_query" in prompt
        assert "inside day" in prompt.lower()

    def test_has_structured_sections(self):
        prompt = build_system_prompt("NQ")
        assert "<role>" in prompt
        assert "<context>" in prompt
        assert "<instructions>" in prompt
        assert "<constraints>" in prompt

    def test_unknown_instrument_raises(self):
        with pytest.raises(ValueError, match="Unknown instrument"):
            build_system_prompt("BOGUS")
