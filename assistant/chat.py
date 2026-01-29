"""Gemini chat with tool calling."""

import json
import logging

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

    def chat(self, message: str, history: list[dict] | None = None,
             trace: bool = False) -> dict:
        """Process a chat message and return response.

        Args:
            message: User message text
            history: Previous messages [{"role": "user"|"model", "text": "..."}]
            trace: If True, include intermediate steps in the result

        Returns:
            {"answer": str, "cost": dict}
            With trace=True, also includes "steps", "model" keys.
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
        steps = []

        for round_num in range(MAX_TOOL_ROUNDS):
            response = self.client.models.generate_content(
                model=self.model_config.id,
                contents=contents,
                config=config,
            )

            if response.usage_metadata:
                total_input_tokens += response.usage_metadata.prompt_token_count or 0
                total_output_tokens += response.usage_metadata.candidates_token_count or 0

            # Check if model wants to call tools
            tool_calls = _extract_tool_calls(response)
            if not tool_calls:
                break

            # Execute tools and feed results back
            contents.append(response.candidates[0].content)

            tool_response_parts = []
            for call in tool_calls:
                log.info("Tool call: %s(%s)", call.name, call.args)
                tool_result = run_tool(call.name, dict(call.args), self.df, self.sessions)

                # Collect query results for direct user display
                if call.name == "execute_query":
                    _collect_query_data(data, dict(call.args), tool_result)

                if trace:
                    steps.append({
                        "round": round_num + 1,
                        "tool": call.name,
                        "args": dict(call.args),
                        "result": tool_result,
                    })

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=call.name, response={"result": tool_result},
                    )
                )

            contents.append(types.Content(role="user", parts=tool_response_parts))

        try:
            answer = response.text or ""
        except (ValueError, AttributeError):
            answer = ""

        if not answer:
            log.warning("No text response after %d tool rounds", MAX_TOOL_ROUNDS)

        cost = calculate_cost(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            model=self.model_name,
        )

        out = {"answer": answer, "data": data, "cost": cost}
        if trace:
            out["steps"] = steps
            out["model"] = self.model_config.id
        return out


def _build_contents(history: list[dict], message: str) -> list[types.Content]:
    """Convert chat history + new message to Gemini contents format."""
    contents = []
    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


def _collect_query_data(data: list, args: dict, tool_result: str):
    """Parse execute_query result and collect for direct user display."""
    try:
        parsed = json.loads(tool_result)
    except (json.JSONDecodeError, TypeError):
        return

    if "error" in parsed:
        return

    data.append({
        "query": args.get("query", {}),
        "result": parsed.get("result"),
        "rows": parsed.get("metadata", {}).get("rows"),
        "session": parsed.get("metadata", {}).get("session"),
        "timeframe": parsed.get("metadata", {}).get("from"),
    })


def _extract_tool_calls(response) -> list:
    """Extract function calls from response, if any."""
    if not response.candidates:
        return []
    parts = response.candidates[0].content.parts
    return [p.function_call for p in parts if p.function_call]
