"""Tests for assistant/chat.py — helper functions."""

import json

from assistant.chat import _build_contents, _collect_query_data_block


class TestBuildContents:
    def test_empty_history(self):
        contents = _build_contents([], "hello")
        assert len(contents) == 1
        assert contents[0].role == "user"
        assert contents[0].parts[0].text == "hello"

    def test_with_history(self):
        history = [
            {"role": "user", "text": "first question"},
            {"role": "model", "text": "first answer"},
        ]
        contents = _build_contents(history, "follow up")
        assert len(contents) == 3
        assert contents[0].role == "user"
        assert contents[0].parts[0].text == "first question"
        assert contents[1].role == "model"
        assert contents[1].parts[0].text == "first answer"
        assert contents[2].role == "user"
        assert contents[2].parts[0].text == "follow up"

    def test_missing_text_key(self):
        # History item without "text" key should default to ""
        history = [{"role": "user"}]
        contents = _build_contents(history, "next")
        assert contents[0].parts[0].text == ""


class TestCollectQueryDataBlock:
    def test_valid_result(self):
        args = {"query": {"select": "close", "session": "RTH"}}
        tool_result = json.dumps({
            "result": 18500.50,
            "metadata": {"rows": 1, "session": "RTH", "from": "daily"},
        })
        block = _collect_query_data_block(args, tool_result)

        assert block is not None
        assert block["query"] == {"select": "close", "session": "RTH"}
        assert block["result"] == 18500.50
        assert block["rows"] == 1
        assert block["session"] == "RTH"
        assert block["timeframe"] == "daily"

    def test_error_result_returns_none(self):
        assert _collect_query_data_block({}, json.dumps({"error": "bad query"})) is None

    def test_invalid_json_returns_none(self):
        assert _collect_query_data_block({}, "not json") is None

    def test_none_returns_none(self):
        assert _collect_query_data_block({}, None) is None

    def test_missing_metadata_fields(self):
        args = {"query": {"select": "close"}}
        tool_result = json.dumps({"result": 42, "metadata": {}})
        block = _collect_query_data_block(args, tool_result)

        assert block is not None
        assert block["rows"] is None
        assert block["session"] is None
        assert block["timeframe"] is None
