"""Anthropic Claude chat with Barb Script tool."""

import json
import logging
import time
from collections.abc import Generator

import anthropic
import pandas as pd

from assistant.prompt import build_system_prompt
from assistant.tools import BARB_TOOL, run_query
from assistant.tools.backtest import BACKTEST_TOOL, run_backtest_tool
from barb.ops import INTRADAY_TIMEFRAMES as _INTRADAY
from config.models import DEFAULT_MODEL, get_model

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5
MODEL = DEFAULT_MODEL


class Assistant:
    """Chat assistant using Anthropic Claude with prompt caching."""

    model = MODEL  # expose for summarization

    def __init__(
        self,
        api_key: str,
        instrument: str,
        df_daily: pd.DataFrame,
        df_minute: pd.DataFrame,
        sessions: dict,
        model: str | None = None,
    ):
        if model:
            self.model = model  # override class-level default
        self.client = anthropic.Anthropic(api_key=api_key)
        self.instrument = instrument
        self.df_daily = df_daily
        self.df_minute = df_minute
        self.sessions = sessions
        self.system_prompt = build_system_prompt(instrument)

    def chat_stream(
        self,
        message: str,
        history: list[dict] | None = None,
        auto_execute: bool = False,
    ) -> Generator[dict]:
        """Process chat message, yielding SSE events.

        Yields dicts with "event" and "data" keys:
            tool_start, tool_end, data_block, text_delta, tool_pending, done.

        For run_backtest: yields tool_pending (with params) instead of executing.
        Frontend shows StrategyCard, user confirms, then calls continue_stream().

        Set auto_execute=True to skip the pause (for scripts/e2e).
        """
        messages = _build_messages(history or [], message)
        yield from self._run_stream(messages, auto_execute=auto_execute)

    def continue_stream(
        self,
        history: list[dict],
        tool_use_id: str,
        model_response: str,
        data_card: dict,
    ) -> Generator[dict]:
        """Continue after tool_pending — inject tool result and let Claude analyze.

        Called after frontend runs backtest via POST /api/backtest.
        """
        messages = _build_messages_from_history(history)

        # Patch the pending tool_use ID so it matches the tool_result we'll add.
        # DB history generates synthetic IDs (toolu_hist_N), but Anthropic needs
        # tool_use.id == tool_result.tool_use_id within the same messages array.
        for msg in reversed(messages):
            if msg["role"] == "assistant" and isinstance(msg["content"], list):
                for block in msg["content"]:
                    if block.get("type") == "tool_use" and block.get("name") == "run_backtest":
                        block["id"] = tool_use_id
                        break
                break

        # Yield the data block so frontend gets it
        yield {"event": "data_block", "data": data_card}

        # Add tool result and continue
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": model_response,
                    }
                ],
            }
        )

        yield from self._run_stream(messages, is_continuation=True, initial_data=[data_card])

    def _run_stream(
        self,
        messages: list[dict],
        is_continuation: bool = False,
        auto_execute: bool = False,
        initial_data: list[dict] | None = None,
    ) -> Generator[dict]:
        """Core streaming loop — shared by chat_stream and continue_stream."""
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_read = 0
        total_cache_write = 0
        tool_call_log = []
        data_blocks = list(initial_data) if initial_data else []
        answer = ""
        # Pre-populate answer with placeholders for initial data blocks
        for i in range(len(data_blocks)):
            answer += f"\n\n{{{{data:{i}}}}}\n\n"

        for round_num in range(MAX_TOOL_ROUNDS):
            # Stream response with prompt caching
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[BARB_TOOL, BACKTEST_TOOL],
                messages=messages,
            ) as stream:
                # Collect response
                tool_uses = []
                text_parts = []

                for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            tool_uses.append(
                                {
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": "",
                                }
                            )
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            text_parts.append(event.delta.text)
                            answer += event.delta.text
                            yield {"event": "text_delta", "data": {"delta": event.delta.text}}
                        elif event.delta.type == "input_json_delta":
                            if tool_uses:
                                tool_uses[-1]["input"] += event.delta.partial_json

                # Get final message for usage stats
                response = stream.get_final_message()

            # Update token counts
            if response.usage:
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
                total_cache_read += getattr(response.usage, "cache_read_input_tokens", 0) or 0
                total_cache_write += getattr(response.usage, "cache_creation_input_tokens", 0) or 0

            # No tool calls — done
            if response.stop_reason != "tool_use":
                break

            # Parse tool inputs
            for tu in tool_uses:
                try:
                    tu["input"] = json.loads(tu["input"]) if tu["input"] else {}
                except json.JSONDecodeError:
                    tu["input"] = {}

            # Add assistant message with tool uses
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                }
            )

            # Check for run_backtest — pause for user approval
            backtest_tu = next((tu for tu in tool_uses if tu["name"] == "run_backtest"), None)
            if backtest_tu and not is_continuation and not auto_execute:
                yield {
                    "event": "tool_pending",
                    "data": {
                        "tool_name": "run_backtest",
                        "tool_use_id": backtest_tu["id"],
                        "input": backtest_tu["input"],
                    },
                }
                # Yield partial done — frontend needs usage + answer so far
                yield {
                    "event": "done",
                    "data": {
                        "answer": answer,
                        "usage": _calc_usage(
                            total_input_tokens,
                            total_output_tokens,
                            total_cache_read,
                            total_cache_write,
                        ),
                        "tool_calls": tool_call_log,
                        "data": data_blocks,
                        "pending_tool": {
                            "tool_use_id": backtest_tu["id"],
                            "input": backtest_tu["input"],
                        },
                    },
                }
                return  # Stop — frontend will call continue_stream

            # Execute tools and collect results
            tool_results = []
            for tu in tool_uses:
                title = tu["input"].get("title", "")
                log.info("Tool call: %s (title=%s)", tu["name"], title)

                yield {
                    "event": "tool_start",
                    "data": {
                        "tool_name": tu["name"],
                        "input": tu["input"],
                    },
                }

                call_start = time.time()
                call_error = None
                model_response = ""
                block = None

                try:
                    if tu["name"] == "run_backtest":
                        model_response, block = self._exec_backtest(tu["input"], title)
                    else:
                        model_response, block = self._exec_query(tu["input"], title)

                    if model_response.startswith("Error:"):
                        call_error = model_response[7:].strip()
                except Exception as exc:
                    call_error = str(exc)
                    model_response = f"Error: {call_error}"
                    log.exception("Tool call failed")

                duration_ms = int((time.time() - call_start) * 1000)

                yield {
                    "event": "tool_end",
                    "data": {
                        "tool_name": tu["name"],
                        "duration_ms": duration_ms,
                        "error": call_error,
                    },
                }

                tool_call_log.append(
                    {
                        "tool_name": tu["name"],
                        "input": tu["input"],
                        "output": model_response,
                        "error": call_error,
                        "duration_ms": duration_ms,
                    }
                )

                # Send data block to UI
                if not call_error and block:
                    block_index = len(data_blocks)
                    answer += f"\n\n{{{{data:{block_index}}}}}\n\n"
                    data_blocks.append(block)
                    yield {"event": "data_block", "data": block}

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu["id"],
                        "content": model_response,
                        "is_error": bool(call_error),
                    }
                )

            # Add tool results (must be in user message)
            messages.append(
                {
                    "role": "user",
                    "content": tool_results,
                }
            )

        yield {
            "event": "done",
            "data": {
                "answer": answer,
                "usage": _calc_usage(
                    total_input_tokens,
                    total_output_tokens,
                    total_cache_read,
                    total_cache_write,
                ),
                "tool_calls": tool_call_log,
                "data": data_blocks,
            },
        }

    def _exec_query(self, input_data: dict, title: str) -> tuple[str, dict | None]:
        """Execute run_query tool. Returns (model_response, data_card)."""
        query = input_data.get("query", {})

        # For steps queries, from/session are inside steps[0]
        step0 = query["steps"][0] if query.get("steps") else query
        timeframe = step0.get("from", "daily")
        session_name = step0.get("session")

        if timeframe in _INTRADAY:
            df = self.df_minute
        elif session_name:
            # RTH-like sessions (within one day) need minute data
            # ETH-like sessions (wrap midnight) ≈ settlement, use daily
            times = self.sessions.get(session_name.upper())
            if times and pd.Timestamp(times[0]).time() < pd.Timestamp(times[1]).time():
                df = self.df_minute
            else:
                df = self.df_daily
        else:
            df = self.df_daily

        result = run_query(query, df, self.sessions)
        model_response = result.get("model_response", "")
        card = _build_query_card(result, title)
        return model_response, card

    def _exec_backtest(self, input_data: dict, title: str) -> tuple[str, dict | None]:
        """Execute run_backtest tool. Returns (model_response, data_block)."""
        from assistant.tools.backtest import _build_backtest_card

        tool_result = run_backtest_tool(input_data, self.df_minute, self.sessions)
        model_response = tool_result.get("model_response", "")
        bt_result = tool_result.get("result")

        if not bt_result:
            return model_response, None

        card = _build_backtest_card(bt_result, title)
        return model_response, card


def _build_query_card(result: dict, title: str) -> dict | None:
    """Build typed DataCard from run_query result.

    Returns {title, blocks: [{type, ...}, ...]} or None if no data to show.
    """
    table_data = result.get("table")
    source_rows = result.get("source_rows")
    ui_data = table_data or source_rows

    if not ui_data:
        return None

    columns = list(ui_data[0].keys()) if isinstance(ui_data, list) and ui_data else []

    blocks = []

    # Bar chart for grouped results
    chart = result.get("chart")
    if chart:
        blocks.append(
            {
                "type": "bar-chart",
                "category_key": chart["category"],
                "value_key": chart["value"],
                "rows": ui_data,
            }
        )

    blocks.append(
        {
            "type": "table",
            "columns": columns,
            "rows": ui_data,
        }
    )

    return {"title": title, "blocks": blocks}


def _build_messages(history: list[dict], message: str) -> list[dict]:
    """Convert chat history to Anthropic messages format."""
    messages = []

    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        tool_calls = msg.get("tool_calls", [])

        if role == "assistant" and tool_calls:
            # Assistant message — only tool_use blocks, skip verbose answer text.
            # Model's previous commentary pollutes context and causes hallucinations.
            content = []
            for i, tc in enumerate(tool_calls):
                tool_id = tc.get("id", f"toolu_hist_{i}")
                content.append(
                    {
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tc["tool_name"],
                        "input": tc.get("input", {}),
                    }
                )
            messages.append({"role": "assistant", "content": content})

            # Tool results (user message)
            tool_results = []
            for i, tc in enumerate(tool_calls):
                tool_id = tc.get("id", f"toolu_hist_{i}")
                output = tc.get("output")
                # Pending tool_call (output=None) means user cancelled
                content = "Cancelled by user" if output is None else _compact_output(output)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": content,
                    }
                )
            messages.append({"role": "user", "content": tool_results})
        else:
            messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": message})
    return messages


def _compact_output(*_args) -> str:
    """Return minimal acknowledgment for history.

    Model should re-query for fresh data, not reference old results.
    """
    return "done"


def _calc_usage(input_tokens: int, output_tokens: int, cache_read: int, cache_write: int) -> dict:
    """Calculate token costs from model config."""
    p = get_model(MODEL).pricing
    input_cost = input_tokens * p.input / 1_000_000
    cache_read_cost = cache_read * p.cache_read / 1_000_000
    cache_write_cost = cache_write * p.cache_write / 1_000_000
    output_cost = output_tokens * p.output / 1_000_000
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "input_cost": input_cost,
        "cache_read_cost": cache_read_cost,
        "cache_write_cost": cache_write_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + cache_read_cost + cache_write_cost + output_cost,
    }


def _build_messages_from_history(history: list[dict]) -> list[dict]:
    """Build Anthropic messages from DB history (for continue_stream).

    Same as _build_messages but without appending a new user message.
    The last entry should be the assistant message with tool_use.
    """
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        tool_calls = msg.get("tool_calls", [])

        if role == "assistant" and tool_calls:
            # Only tool_use blocks — skip answer text (same as _build_messages)
            content = []
            for i, tc in enumerate(tool_calls):
                tool_id = tc.get("id", f"toolu_hist_{i}")
                content.append(
                    {
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tc["tool_name"],
                        "input": tc.get("input", {}),
                    }
                )
            messages.append({"role": "assistant", "content": content})

            # Add tool results for completed tool calls (not pending ones)
            completed = [tc for tc in tool_calls if tc.get("output") is not None]
            if completed:
                tool_results = []
                for i, tc in enumerate(tool_calls):
                    tool_id = tc.get("id", f"toolu_hist_{i}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": _compact_output(tc.get("output", "done")),
                        }
                    )
                messages.append({"role": "user", "content": tool_results})
        else:
            messages.append({"role": role, "content": text})

    return messages
