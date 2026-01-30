"""Gemini chat with tool calling."""

import json
import logging
import time
from collections.abc import Generator

import pandas as pd
from google import genai
from google.genai import types

from assistant.prompt import build_system_prompt
from assistant.tools import TOOL_DECLARATIONS, run_tool
from config.models import DEFAULT_MODEL, calculate_cost, get_model

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


class Assistant:
    """Stateless chat assistant. Client sends full history each request."""

    def __init__(self, api_key: str, instrument: str, df: pd.DataFrame, sessions: dict,
                 model: str = DEFAULT_MODEL):
        self.client = genai.Client(api_key=api_key)
        self.instrument = instrument
        self.df = df
        self.sessions = sessions
        self.system_prompt = build_system_prompt(instrument)
        self.model_name = model
        self.model_config = get_model(model)

    def chat_stream(self, message: str, history: list[dict] | None = None) -> Generator[dict]:
        """Process chat message, yielding SSE events as dicts.

        Yields dicts with "event" and "data" keys:
            tool_start, tool_end, data_block, text_delta, done.
        """
        contents = _build_contents(history or [], message)

        tools = types.Tool(function_declarations=TOOL_DECLARATIONS)
        config = types.GenerateContentConfig(
            tools=[tools],
            system_instruction=self.system_prompt,
        )

        total_input_tokens = 0
        total_output_tokens = 0
        data = []
        tool_call_log = []
        answer = ""

        for round_num in range(MAX_TOOL_ROUNDS):
            stream = self.client.models.generate_content_stream(
                model=self.model_config.id,
                contents=contents,
                config=config,
            )

            # Consume stream: yield text deltas in real-time, collect tool call parts
            all_parts = []
            has_fn_calls = False
            last_usage = None

            for chunk in stream:
                if chunk.usage_metadata:
                    last_usage = chunk.usage_metadata

                if not chunk.candidates:
                    continue

                for part in chunk.candidates[0].content.parts:
                    all_parts.append(part)
                    if part.function_call:
                        has_fn_calls = True
                    elif part.text:
                        answer += part.text
                        yield {"event": "text_delta", "data": {"delta": part.text}}

            if last_usage:
                total_input_tokens += last_usage.prompt_token_count or 0
                total_output_tokens += last_usage.candidates_token_count or 0

            if not has_fn_calls:
                break

            contents.append(types.Content(role="model", parts=all_parts))

            fn_calls = [p.function_call for p in all_parts if p.function_call]

            tool_response_parts = []
            for call in fn_calls:
                call_args = dict(call.args)
                log.info("Tool call: %s(%s)", call.name, call.args)

                yield {"event": "tool_start", "data": {
                    "tool_name": call.name, "input": call_args,
                }}

                call_start = time.time()
                call_error = None

                try:
                    tool_result = run_tool(call.name, call_args, self.df, self.sessions)
                except Exception as exc:
                    call_error = str(exc)
                    tool_result = json.dumps({"error": call_error})
                    log.exception("Tool call failed: %s", call.name)

                duration_ms = int((time.time() - call_start) * 1000)

                yield {"event": "tool_end", "data": {
                    "tool_name": call.name,
                    "duration_ms": duration_ms,
                    "error": call_error,
                }}

                tool_call_log.append({
                    "tool_name": call.name,
                    "input": call_args,
                    "output": tool_result,
                    "error": call_error,
                    "duration_ms": duration_ms,
                })

                if call.name == "execute_query" and not call_error:
                    block = _collect_query_data_block(call_args, tool_result)
                    if block:
                        data.append(block)
                        yield {"event": "data_block", "data": block}

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=call.name, response={"result": tool_result},
                    )
                )

            contents.append(types.Content(role="user", parts=tool_response_parts))

        if not answer:
            log.warning("No text response after %d tool rounds", round_num + 1)

        usage = calculate_cost(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            model=self.model_name,
        )

        yield {"event": "done", "data": {
            "answer": answer,
            "usage": usage,
            "tool_calls": tool_call_log,
            "data": data,
        }}


def _build_contents(history: list[dict], message: str) -> list[types.Content]:
    """Convert chat history + new message to Gemini contents format."""
    contents = []
    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


def _collect_query_data_block(args: dict, tool_result: str) -> dict | None:
    """Parse execute_query result into a data block, or None."""
    try:
        parsed = json.loads(tool_result)
    except (json.JSONDecodeError, TypeError):
        return None

    if "error" in parsed:
        return None

    return {
        "query": args["query"] if "query" in args else args,
        "result": parsed.get("result"),
        "rows": parsed.get("metadata", {}).get("rows"),
        "session": parsed.get("metadata", {}).get("session"),
        "timeframe": parsed.get("metadata", {}).get("from"),
    }
