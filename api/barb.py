"""Barb — trading data analyst agent."""

import json
import logging
import time
from datetime import date, datetime
from functools import lru_cache

from pydantic import BaseModel
from google import genai
from google.genai import types

from api.config import get_settings
from api.prompts import SYSTEM_PROMPT
from config.models import get_model, calculate_cost
from config.market import get_instrument, get_holidays_for_year
from config.market.events import EVENT_GROUPS

log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


class BarbError(Exception):
    """Barb agent error."""
    pass


class Cost(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cached_tokens: int = 0
    total_cost: float = 0.0


class Response(BaseModel):
    answer: str
    cost: Cost = Cost()


@lru_cache
def _get_client() -> genai.Client:
    """Get cached Gemini client."""
    return genai.Client(api_key=get_settings().gemini_api_key)


class Barb:
    """Trading data analyst."""

    def __init__(self, instrument: str = "NQ"):
        self.instrument = instrument
        self.model = get_model()
        self.client = _get_client()

    def ask(self, question: str) -> Response:
        config = types.GenerateContentConfig(system_instruction=self._system_prompt())
        if self.model.thinking_budget is not None:
            config.thinking_config = types.ThinkingConfig(thinking_budget=self.model.thinking_budget)
        else:
            config.thinking_config = types.ThinkingConfig(thinking_level="minimal")

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.model.id,
                    contents=question,
                    config=config,
                )
                return Response(answer=response.text, cost=self._cost(response))
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    log.warning(f"Gemini API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                    time.sleep(RETRY_DELAY * (attempt + 1))  # exponential backoff
                else:
                    log.error(f"Gemini API error after {MAX_RETRIES} attempts: {e}")

        raise BarbError(f"Failed after {MAX_RETRIES} attempts: {last_error}") from last_error

    def _cost(self, response) -> Cost:
        usage = getattr(response, 'usage_metadata', None)
        if not usage:
            return Cost()

        inp = getattr(usage, 'prompt_token_count', 0) or 0
        out = getattr(usage, 'candidates_token_count', 0) or 0
        think = getattr(usage, 'thoughts_token_count', 0) or 0
        cache = getattr(usage, 'cached_content_token_count', 0) or 0

        total = calculate_cost(inp, out, think, cache)["total_cost"]
        return Cost(input_tokens=inp, output_tokens=out, thinking_tokens=think, cached_tokens=cache, total_cost=total)

    def _system_prompt(self) -> str:
        cfg = get_instrument(self.instrument)
        if not cfg:
            return "Unknown instrument"

        now = datetime.now()
        return SYSTEM_PROMPT.format(
            instrument=self.instrument,
            instrument_config=json.dumps(cfg, indent=2, default=str),
            now=now.strftime("%Y-%m-%d %H:%M ET (%A)"),
            year=now.year,
            holidays=self._holidays(),
            events=self._events(cfg),
        )

    def _holidays(self) -> str:
        h = get_holidays_for_year(self.instrument, date.today().year)
        lines = [f"  {d} closed" for d in sorted(h.get("full_close", []))]
        lines += [f"  {d} early" for d in sorted(h.get("early_close", []))]
        return "\n".join(lines) or "  None"

    def _events(self, cfg: dict) -> str:
        lines = []
        for cat in cfg.get("events", []):
            for e in EVENT_GROUPS.get(cat, {}).values():
                tag = " [HIGH]" if e.impact.value == "high" else ""
                lines.append(f"  {e.name}: {e.schedule}{tag}")
        return "\n".join(lines) or "  None"
