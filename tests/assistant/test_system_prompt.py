"""Tests for assistant/prompt/system.py — full system prompt builder.

System prompt has: identity, instrument context, behavioral rules.
Query knowledge (patterns, examples) lives in tool description — tested in test_prompt.py.
"""

import pytest

from assistant.prompt.system import build_system_prompt
from assistant.tools import BARB_TOOL


class TestBuildSystemPrompt:
    def test_returns_string(self):
        result = build_system_prompt("NQ")
        assert isinstance(result, str)
        assert len(result) > 100

    def test_identity(self):
        result = build_system_prompt("NQ")
        assert "You are Barb" in result
        assert "NQ" in result
        assert "Nasdaq 100 E-mini" in result

    def test_instrument_context(self):
        result = build_system_prompt("NQ")
        assert "<instrument>" in result
        assert "</instrument>" in result
        assert "CME" in result
        assert "RTH" in result

    def test_holiday_context(self):
        result = build_system_prompt("NQ")
        assert "<holidays>" in result
        assert "</holidays>" in result
        assert "Christmas" in result
        assert "13:15" in result

    def test_event_context(self):
        result = build_system_prompt("NQ")
        assert "<events>" in result
        assert "</events>" in result
        assert "FOMC" in result
        assert "NFP" in result

    def test_instructions(self):
        result = build_system_prompt("NQ")
        assert "<instructions>" in result
        assert "built-in functions" in result
        assert "holiday" in result

    def test_session_instruction(self):
        result = build_system_prompt("NQ")
        assert "settlement" in result
        assert "session" in result.lower()

    def test_transparency(self):
        result = build_system_prompt("NQ")
        assert "<transparency>" in result
        assert "alternative" in result

    def test_acknowledgment(self):
        result = build_system_prompt("NQ")
        assert "<acknowledgment>" in result

    def test_data_titles(self):
        result = build_system_prompt("NQ")
        assert "<data_titles>" in result

    def test_unknown_instrument_raises(self):
        with pytest.raises(ValueError, match="Unknown instrument"):
            build_system_prompt("NONEXISTENT")

    def test_no_duplicate_xml_tags(self):
        """Each XML section should appear exactly once."""
        result = build_system_prompt("NQ")
        for tag in [
            "<instrument>",
            "<holidays>",
            "<events>",
            "<instructions>",
            "<transparency>",
            "<acknowledgment>",
            "<data_titles>",
        ]:
            assert result.count(tag) == 1, f"Duplicate tag: {tag}"

    def test_no_query_knowledge_in_system_prompt(self):
        """Patterns and examples belong in tool description, not system prompt."""
        result = build_system_prompt("NQ")
        assert "<recipes>" not in result
        assert "<patterns>" not in result
        assert "<examples>" not in result


class TestToolDescriptionContent:
    """Query-specific knowledge lives in tool description."""

    def test_has_patterns(self):
        desc = BARB_TOOL["description"]
        assert "<patterns>" in desc
        assert "MACD cross" in desc
        assert "crossover" in desc
        assert "breakout" in desc
        assert "NFP" in desc

    def test_has_examples(self):
        desc = BARB_TOOL["description"]
        assert "<examples>" in desc
        assert "change_pct" in desc
        assert "rsi(close,14)" in desc
        assert "range()" in desc
