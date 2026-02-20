"""Tests for system prompt and tool description.

System prompt: identity, data-flow, instrument context, response rules, limits.
Tool description: query syntax, patterns, examples, data protocol, function reference.
"""

import pytest

from assistant.prompt import build_system_prompt
from assistant.tools import BARB_TOOL
from assistant.tools.backtest import BACKTEST_TOOL


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

    def test_has_structured_sections(self):
        prompt = build_system_prompt("NQ")
        assert "<instrument>" in prompt
        assert "<data-flow>" in prompt
        assert "<response>" in prompt
        assert "<limits>" in prompt

    def test_unknown_instrument_raises(self):
        with pytest.raises(ValueError, match="Unknown instrument"):
            build_system_prompt("BOGUS")

    def test_has_data_flow_explanation(self):
        """System prompt explains that model sees summary, user sees full table."""
        prompt = build_system_prompt("NQ")
        assert "summary" in prompt.lower()
        assert "user sees the full table" in prompt.lower()

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

    def test_has_columns_example(self):
        desc = BARB_TOOL["description"]
        assert '"columns"' in desc
        assert "last week" in desc.lower()

    def test_has_function_reference(self):
        desc = BARB_TOOL["description"]
        assert "rsi" in desc
        assert "atr" in desc
        assert "sma" in desc

    def test_has_output_format_rules(self):
        desc = BARB_TOOL["description"]
        assert '"columns"' in desc
        assert "Available columns:" in desc or "Available:" in desc
        assert "date" in desc

    def test_tool_has_data_protocol(self):
        """run_query description contains <data-protocol> explaining summaries."""
        desc = BARB_TOOL["description"]
        assert "<data-protocol>" in desc
        assert "SUMMARIES" in desc
        assert "run another query" in desc.lower()

    def test_tool_has_query_rules(self):
        """run_query description contains percentage/session/period rules."""
        desc = BARB_TOOL["description"]
        assert "<query-rules>" in desc
        assert "pct(" in desc
        assert "settlement" in desc.lower()
        assert "ALL data" in desc

    def test_tool_has_steps(self):
        """run_query description and schema contain steps for multi-step queries."""
        desc = BARB_TOOL["description"]
        assert "steps" in desc
        assert "Step 1" in desc
        schema = BARB_TOOL["input_schema"]
        assert "steps" in schema["properties"]["query"]["properties"]


class TestBacktestTool:
    def test_backtest_has_analysis_rules(self):
        """Backtest description contains <analysis-rules> for strategy quality."""
        desc = BACKTEST_TOOL["description"]
        assert "<analysis-rules>" in desc
        assert "Yearly stability" in desc
        assert "Exit analysis" in desc
        assert "Concentration" in desc
        assert "skepticism" in desc
