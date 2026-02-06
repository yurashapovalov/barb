"""Tests for assistant/context.py — context memory management."""

from unittest.mock import MagicMock

from assistant.context import (
    SUMMARY_THRESHOLD,
    build_history_with_context,
    should_summarize,
    summarize,
)


def _make_history(n_exchanges: int) -> list[dict]:
    """Create n exchanges (2 messages each)."""
    history = []
    for i in range(n_exchanges):
        history.append({"role": "user", "text": f"Question {i + 1}"})
        history.append({"role": "assistant", "text": f"Answer {i + 1}"})
    return history


class TestShouldSummarize:
    def test_below_threshold(self):
        assert not should_summarize(SUMMARY_THRESHOLD - 1, None)

    def test_at_threshold(self):
        assert should_summarize(SUMMARY_THRESHOLD, None)

    def test_above_threshold(self):
        assert should_summarize(SUMMARY_THRESHOLD + 5, None)

    def test_already_summarized_not_enough_new(self):
        context = {"summary": "...", "summary_up_to": 10}
        # 25 exchanges, summarized up to 10, only 15 new — not enough
        assert not should_summarize(25, context)

    def test_already_summarized_enough_new(self):
        context = {"summary": "...", "summary_up_to": 10}
        # 30 exchanges, summarized up to 10, 20 new — triggers
        assert should_summarize(30, context)

    def test_empty_context(self):
        assert should_summarize(SUMMARY_THRESHOLD, {})

    def test_context_without_summary_up_to(self):
        context = {"summary": "..."}
        assert should_summarize(SUMMARY_THRESHOLD, context)


class TestBuildHistoryWithContext:
    def test_no_context_returns_all(self):
        history = _make_history(5)
        result = build_history_with_context(None, history)
        assert result == history

    def test_empty_context_returns_all(self):
        history = _make_history(5)
        result = build_history_with_context({}, history)
        assert result == history

    def test_context_without_summary_returns_all(self):
        history = _make_history(5)
        result = build_history_with_context({"summary_up_to": 3}, history)
        assert result == history

    def test_with_context(self):
        history = _make_history(25)  # 50 messages total
        context = {"summary": "We discussed ranges.", "summary_up_to": 15}

        result = build_history_with_context(context, history)

        # First message is summary
        assert result[0]["role"] == "assistant"
        assert "[Previous context]" in result[0]["text"]
        assert "We discussed ranges." in result[0]["text"]

        # Rest are messages after summary_up_to (exchanges 16-25 = 20 messages)
        assert len(result) == 1 + (25 - 15) * 2  # 1 summary + 20 recent
        assert result[1] == {"role": "user", "text": "Question 16"}

    def test_summary_up_to_zero(self):
        history = _make_history(5)
        context = {"summary": "Old context.", "summary_up_to": 0}

        result = build_history_with_context(context, history)

        # Summary + all messages
        assert len(result) == 1 + 10
        assert result[0]["role"] == "assistant"


class TestSummarize:
    def test_calls_anthropic_without_tools(self):
        mock_client = MagicMock()
        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "User asked about daily ranges and volume patterns."
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        messages = _make_history(10)
        result = summarize(mock_client, "claude-sonnet-4-5-20250514", None, messages)

        assert result == "User asked about daily ranges and volume patterns."
        mock_client.messages.create.assert_called_once()

        # Verify no tools in the call
        call_kwargs = mock_client.messages.create.call_args
        assert "tools" not in (call_kwargs.kwargs or {})

    def test_includes_old_summary(self):
        mock_client = MagicMock()
        mock_content = MagicMock()
        mock_content.type = "text"
        mock_content.text = "Extended summary."
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        messages = _make_history(5)
        result = summarize(
            mock_client, "claude-sonnet-4-5-20250514", "Old summary.", messages,
        )

        assert result == "Extended summary."
        # Verify old summary was included in the prompt
        call_kwargs = mock_client.messages.create.call_args
        prompt_messages = call_kwargs.kwargs.get("messages", [])
        assert any("Old summary." in msg.get("content", "") for msg in prompt_messages)

    def test_empty_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        result = summarize(mock_client, "claude-sonnet-4-5-20250514", None, [])
        assert result == ""
