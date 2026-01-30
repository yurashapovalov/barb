"""Tests for assistant/chat.py — helper functions."""

import json

from assistant.chat import _build_contents, _collect_query_data


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


class TestCollectQueryData:
    def test_valid_result(self):
        data = []
        args = {"query": {"select": "close", "session": "RTH"}}
        tool_result = json.dumps({
            "result": 18500.50,
            "metadata": {"rows": 1, "session": "RTH", "from": "daily"},
        })
        _collect_query_data(data, args, tool_result)

        assert len(data) == 1
        assert data[0]["query"] == {"select": "close", "session": "RTH"}
        assert data[0]["result"] == 18500.50
        assert data[0]["rows"] == 1
        assert data[0]["session"] == "RTH"
        assert data[0]["timeframe"] == "daily"

    def test_error_result_ignored(self):
        data = []
        _collect_query_data(data, {}, json.dumps({"error": "bad query"}))
        assert data == []

    def test_invalid_json_ignored(self):
        data = []
        _collect_query_data(data, {}, "not json")
        assert data == []

    def test_none_ignored(self):
        data = []
        _collect_query_data(data, {}, None)
        assert data == []

    def test_multiple_calls_accumulate(self):
        data = []
        for i in range(3):
            args = {"query": {"select": f"col_{i}"}}
            result = json.dumps({"result": i, "metadata": {"rows": 1}})
            _collect_query_data(data, args, result)
        assert len(data) == 3
