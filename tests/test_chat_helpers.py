"""Tests for assistant/chat.py — helper functions."""

from assistant.chat import _build_messages, _compact_output


class TestBuildMessages:
    def test_empty_history(self):
        messages = _build_messages([], "hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "hello"

    def test_with_history(self):
        history = [
            {"role": "user", "text": "first question"},
            {"role": "assistant", "text": "first answer"},
        ]
        messages = _build_messages(history, "follow up")
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "first question"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "first answer"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "follow up"

    def test_missing_text_key(self):
        history = [{"role": "user"}]
        messages = _build_messages(history, "next")
        assert messages[0]["content"] == ""

    def test_assistant_with_tool_calls(self):
        history = [
            {"role": "user", "text": "question"},
            {
                "role": "assistant",
                "text": "thinking...",
                "tool_calls": [
                    {"tool_name": "run_query", "input": {"query": {}}, "output": "Result: 42"},
                ],
            },
        ]
        messages = _build_messages(history, "follow up")
        # user + assistant (with tool_use) + user (tool_result) + user
        assert len(messages) == 4
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"][0]["type"] == "text"
        assert messages[1]["content"][1]["type"] == "tool_use"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"][0]["type"] == "tool_result"


class TestCompactOutput:
    def test_short_output_kept(self):
        assert _compact_output("42") == "42"

    def test_status_message_kept(self):
        msg = "Session RTH (09:30-16:00). 2,345,678 rows."
        assert _compact_output(msg) == msg

    def test_long_output_truncated(self):
        long = "x" * 600
        result = _compact_output(long)
        assert len(result) < 450
        assert result.endswith("...")

    def test_empty_output(self):
        assert _compact_output("") == ""

    def test_none_output(self):
        # Should handle None gracefully
        assert _compact_output(None) == None
