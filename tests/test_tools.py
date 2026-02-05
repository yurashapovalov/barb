"""Tests for assistant tools — no LLM, just direct execution."""

import json

from assistant.tools import TOOL_DECLARATIONS, run_tool


class TestToolDeclarations:
    def test_declarations_have_required_fields(self):
        for decl in TOOL_DECLARATIONS:
            assert "name" in decl
            assert "description" in decl
            assert "parameters" in decl

    def test_execute_query_declaration(self):
        decl = next(d for d in TOOL_DECLARATIONS if d["name"] == "execute_query")
        props = decl["parameters"]["properties"]["query"]["properties"]
        assert "session" in props
        assert "from" in props
        assert "map" in props
        assert "where" in props
        assert "select" in props


class TestExecuteQuery:
    def test_simple_count(self, nq_minute_slice, sessions):
        result, raw = run_tool("execute_query", {
            "query": {"session": "RTH", "from": "daily", "select": "count()"},
        }, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "result" in data
        assert data["result"] > 0
        assert data["has_table"] is False
        assert raw is not None

    def test_table_result(self, nq_minute_slice, sessions):
        result, raw = run_tool("execute_query", {
            "query": {
                "session": "RTH",
                "from": "daily",
                "map": {"weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "count()",
            },
        }, nq_minute_slice, sessions)
        data = json.loads(result)
        assert data["has_table"] is True
        assert data["row_count"] == 5
        assert raw is not None

    def test_error_returns_hint(self, nq_minute_slice, sessions):
        result, raw = run_tool("execute_query", {
            "query": {"from": "daily", "map": {"bad": "nonexistent + 1"}},
        }, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "error" in data
        assert "hint" in data
        assert data["step"] == "map"
        assert raw is None

    def test_empty_query(self, nq_minute_slice, sessions):
        result, raw = run_tool("execute_query", {"query": {}}, nq_minute_slice, sessions)
        data = json.loads(result)
        assert data["has_table"] is True
        assert data["row_count"] > 0


class TestGetQueryReference:
    def test_returns_reference_text(self, nq_minute_slice, sessions):
        result, raw = run_tool("get_query_reference", {}, nq_minute_slice, sessions)
        assert "Barb Script Query Reference" in result
        assert "session" in result
        assert "rolling_mean" in result
        assert "Examples" in result
        assert raw is None

    def test_reference_has_all_function_categories(self, nq_minute_slice, sessions):
        result, _ = run_tool("get_query_reference", {}, nq_minute_slice, sessions)
        assert "Scalar:" in result
        assert "Lag:" in result
        assert "Window:" in result
        assert "Aggregate:" in result
        assert "Time:" in result


class TestUnderstandQuestion:
    def test_declaration_exists(self):
        names = [d["name"] for d in TOOL_DECLARATIONS]
        assert "understand_question" in names

    def test_returns_capabilities(self, nq_minute_slice, sessions):
        result, raw = run_tool("understand_question", {"question": "test"}, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "capabilities" in data
        assert "single_timeframe" in data["capabilities"]
        assert "aggregation" in data["capabilities"]
        assert raw is None

    def test_returns_limitations(self, nq_minute_slice, sessions):
        result, _ = run_tool("understand_question", {"question": "test"}, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "limitations" in data
        assert any("Cross-timeframe" in lim for lim in data["limitations"])

    def test_returns_instructions(self, nq_minute_slice, sessions):
        result, _ = run_tool("understand_question", {"question": "test"}, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "instructions" in data
        assert "honestly" in data["instructions"]


class TestUnknownTool:
    def test_unknown_tool_returns_error(self, nq_minute_slice, sessions):
        result, raw = run_tool("bogus_tool", {}, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "error" in data
        assert raw is None
