"""Anthropic Claude chat with Barb Script tool."""

import json
import logging
import time
from collections.abc import Generator

import anthropic
import pandas as pd

from assistant.prompt import build_system_prompt
from assistant.tools import BARB_TOOL, run_query

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5
MODEL = "claude-sonnet-4-5-20250929"


class Assistant:
    """Chat assistant using Anthropic Claude with prompt caching."""

    model = MODEL  # expose for summarization

    def __init__(self, api_key: str, instrument: str, df: pd.DataFrame, sessions: dict):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.instrument = instrument
        self.df = df
        self.sessions = sessions
        self.system_prompt = build_system_prompt(instrument)

    def chat_stream(self, message: str, history: list[dict] | None = None) -> Generator[dict]:
        """Process chat message, yielding SSE events.

        Yields dicts with "event" and "data" keys:
            tool_start, tool_end, data_block, text_delta, done.
        """
        messages = _build_messages(history or [], message)

        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_read = 0
        total_cache_write = 0
        tool_call_log = []
        data_blocks = []
        answer = ""

        for round_num in range(MAX_TOOL_ROUNDS):
            # Stream response with prompt caching
            with self.client.messages.stream(
                model=MODEL,
                max_tokens=4096,
                temperature=0,
                system=[{
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }],
                tools=[BARB_TOOL],
                messages=messages,
            ) as stream:
                # Collect response
                tool_uses = []
                text_parts = []

                for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            tool_uses.append({
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": "",
                            })
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
            messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # Execute tools and collect results
            tool_results = []
            for tu in tool_uses:
                query = tu["input"].get("query", {})
                log.info("Tool call: %s(%s)", tu["name"], query)

                yield {"event": "tool_start", "data": {
                    "tool_name": tu["name"],
                    "input": {"query": query},
                }}

                call_start = time.time()
                call_error = None
                model_response = ""
                table_data = None
                source_rows = None

                try:
                    result = run_query(query, self.df, self.sessions)
                    model_response = result.get("model_response", "")
                    table_data = result.get("table")
                    source_rows = result.get("source_rows")

                    if model_response.startswith("Error:"):
                        call_error = model_response[7:].strip()
                except Exception as exc:
                    call_error = str(exc)
                    model_response = f"Error: {call_error}"
                    log.exception("Tool call failed")

                duration_ms = int((time.time() - call_start) * 1000)

                yield {"event": "tool_end", "data": {
                    "tool_name": tu["name"],
                    "duration_ms": duration_ms,
                    "error": call_error,
                }}

                tool_call_log.append({
                    "tool_name": tu["name"],
                    "input": {"query": query},
                    "output": model_response,
                    "error": call_error,
                    "duration_ms": duration_ms,
                })

                # Send data block to UI (table or source_rows as evidence)
                ui_data = table_data or source_rows
                chart_hint = result.get("chart")
                if not call_error and ui_data:
                    title = tu["input"].get("title", "")
                    block = {
                        "tool": tu["name"],
                        "input": {"query": query},
                        "result": ui_data,
                        "rows": len(ui_data) if isinstance(ui_data, list) else None,
                        "title": title,
                        "chart": chart_hint,
                    }
                    # Insert marker into answer for proper positioning
                    block_index = len(data_blocks)
                    answer += f"\n\n{{{{data:{block_index}}}}}\n\n"
                    data_blocks.append(block)
                    yield {"event": "data_block", "data": block}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": model_response,
                    "is_error": bool(call_error),
                })

            # Add tool results (must be in user message)
            messages.append({
                "role": "user",
                "content": tool_results,
            })

        # Calculate costs
        # Sonnet 4.5: $3/MTok input, $0.30/MTok cached read, $3.75/MTok cache write, $15/MTok output
        # API returns: input_tokens = tokens AFTER cache breakpoint (uncached)
        #              cache_read_input_tokens = tokens read from cache
        #              cache_creation_input_tokens = tokens written to cache
        input_cost = total_input_tokens * 3.0 / 1_000_000
        cache_read_cost = total_cache_read * 0.30 / 1_000_000
        cache_write_cost = total_cache_write * 3.75 / 1_000_000
        output_cost = total_output_tokens * 15.0 / 1_000_000
        total_cost = input_cost + cache_read_cost + cache_write_cost + output_cost

        usage = {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "cache_read_tokens": total_cache_read,
            "cache_write_tokens": total_cache_write,
            "input_cost": input_cost,
            "cache_read_cost": cache_read_cost,
            "cache_write_cost": cache_write_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }

        yield {"event": "done", "data": {
            "answer": answer,
            "usage": usage,
            "tool_calls": tool_call_log,
            "data": data_blocks,
        }}


def _build_messages(history: list[dict], message: str) -> list[dict]:
    """Convert chat history to Anthropic messages format."""
    messages = []

    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        tool_calls = msg.get("tool_calls", [])

        if role == "assistant" and tool_calls:
            # Assistant message with tool calls
            content = []
            for i, tc in enumerate(tool_calls):
                # Generate consistent ID for both tool_use and tool_result
                tool_id = tc.get("id", f"toolu_hist_{i}")
                content.append({
                    "type": "tool_use",
                    "id": tool_id,
                    "name": tc["tool_name"],
                    "input": tc.get("input", {}),
                })
            if text:
                content.insert(0, {"type": "text", "text": text})
            messages.append({"role": "assistant", "content": content})

            # Tool results (user message)
            tool_results = []
            for i, tc in enumerate(tool_calls):
                tool_id = tc.get("id", f"toolu_hist_{i}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": _compact_output(tc.get("output", "done")),
                })
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
