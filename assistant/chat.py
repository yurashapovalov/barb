"""Gemini chat with tool calling."""

import logging

import pandas as pd
from google import genai
from google.genai import types

from assistant.prompt import build_system_prompt
from assistant.tools import TOOL_DECLARATIONS, run_tool
from config.models import get_model, calculate_cost, DEFAULT_MODEL

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


class Assistant:
    """Stateless chat assistant. Client sends full history each request."""

    def __init__(self, api_key: str, instrument: str, df: pd.DataFrame, sessions: dict):
        self.client = genai.Client(api_key=api_key)
        self.instrument = instrument
        self.df = df
        self.sessions = sessions
        self.system_prompt = build_system_prompt(instrument)
        self.model_config = get_model()

    def chat(self, message: str, history: list[dict] | None = None) -> dict:
        """Process a chat message and return response.

        Args:
            message: User message text
            history: Previous messages [{"role": "user"|"model", "text": "..."}]

        Returns:
            {"answer": str, "cost": dict}
        """
        contents = _build_contents(history or [], message)

        tools = types.Tool(function_declarations=TOOL_DECLARATIONS)
        config = types.GenerateContentConfig(
            tools=[tools],
            system_instruction=self.system_prompt,
        )

        total_input_tokens = 0
        total_output_tokens = 0

        for _ in range(MAX_TOOL_ROUNDS):
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
                log.info(f"Tool call: {call.name}({call.args})")
                result = run_tool(call.name, dict(call.args), self.df, self.sessions)
                tool_response_parts.append(
                    types.Part.from_function_response(name=call.name, response={"result": result})
                )

            contents.append(types.Content(role="user", parts=tool_response_parts))

        answer = response.text or ""
        if not answer:
            log.warning("No text response after %d tool rounds", MAX_TOOL_ROUNDS)

        cost = calculate_cost(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            model=DEFAULT_MODEL,
        )

        return {"answer": answer, "cost": cost}


def _build_contents(history: list[dict], message: str) -> list[types.Content]:
    """Convert chat history + new message to Gemini contents format."""
    contents = []
    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


def _extract_tool_calls(response) -> list:
    """Extract function calls from response, if any."""
    if not response.candidates:
        return []
    parts = response.candidates[0].content.parts
    return [p.function_call for p in parts if p.function_call]
