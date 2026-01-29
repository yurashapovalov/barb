"""Tests for assistant tools — no LLM, just direct execution."""

import json

from assistant.tools import run_tool, TOOL_DECLARATIONS


class TestToolDeclarations:
    def test_declarations_have_required_fields(self):
        for decl in TOOL_DECLARATIONS:
            assert "name" in decl
            assert "description" in decl
            assert "parameters" in decl

    def test_execute_query_declaration(self):
        decl = TOOL_DECLARATIONS[0]
        assert decl["name"] == "execute_query"
        props = decl["parameters"]["properties"]["query"]["properties"]
        assert "session" in props
        assert "from" in props
        assert "map" in props
        assert "where" in props
        assert "select" in props


class TestExecuteQuery:
    def test_simple_count(self, nq_minute_slice, sessions):
        result = run_tool("execute_query", {
            "query": {"session": "RTH", "from": "daily", "select": "count()"},
        }, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "result" in data
        assert data["result"] > 0
        assert data["has_table"] is False

    def test_table_result(self, nq_minute_slice, sessions):
        result = run_tool("execute_query", {
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

    def test_error_returns_hint(self, nq_minute_slice, sessions):
        result = run_tool("execute_query", {
            "query": {"from": "daily", "map": {"bad": "nonexistent + 1"}},
        }, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "error" in data
        assert "hint" in data
        assert data["step"] == "map"

    def test_empty_query(self, nq_minute_slice, sessions):
        result = run_tool("execute_query", {"query": {}}, nq_minute_slice, sessions)
        data = json.loads(result)
        assert data["result"] > 0


class TestGetQueryReference:
    def test_returns_reference_text(self, nq_minute_slice, sessions):
        result = run_tool("get_query_reference", {}, nq_minute_slice, sessions)
        assert "Barb Script Query Reference" in result
        assert "session" in result
        assert "rolling_mean" in result
        assert "Examples" in result

    def test_reference_has_all_function_categories(self, nq_minute_slice, sessions):
        result = run_tool("get_query_reference", {}, nq_minute_slice, sessions)
        assert "Scalar:" in result
        assert "Lag:" in result
        assert "Window:" in result
        assert "Aggregate:" in result
        assert "Time:" in result


class TestUnknownTool:
    def test_unknown_tool_returns_error(self, nq_minute_slice, sessions):
        result = run_tool("bogus_tool", {}, nq_minute_slice, sessions)
        data = json.loads(result)
        assert "error" in data
