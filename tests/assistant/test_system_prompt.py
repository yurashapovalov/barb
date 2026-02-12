"""Tests for assistant/prompt/system.py — full system prompt builder."""

import pytest

from assistant.prompt.system import build_system_prompt


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

    def test_trading_knowledge(self):
        result = build_system_prompt("NQ")
        assert "<trading_knowledge>" in result
        assert "rsi(close, 14)" in result
        assert "atr(14)" in result
        assert "adx(14)" in result
        assert "crossover" in result

    def test_instructions(self):
        result = build_system_prompt("NQ")
        assert "<instructions>" in result
        assert "built-in functions" in result
        assert "holiday" in result

    def test_session_instruction(self):
        result = build_system_prompt("NQ")
        assert "settlement" in result
        assert "session" in result.lower()

    def test_examples(self):
        result = build_system_prompt("NQ")
        assert "<examples>" in result
        assert "change_pct" in result
        assert "rsi(close,14)" in result
        assert "range()" in result
        # Holiday example
        assert "Christmas" in result

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
            "<trading_knowledge>",
            "<instructions>",
            "<acknowledgment>",
            "<data_titles>",
            "<examples>",
        ]:
            assert result.count(tag) == 1, f"Duplicate tag: {tag}"
