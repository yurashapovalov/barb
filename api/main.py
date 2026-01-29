"""Barb API."""

import logging
import os
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from functools import lru_cache

from api.config import get_settings
from assistant.chat import Assistant
from barb.data import load_data
from config.market.instruments import get_instrument

if os.getenv("ENV") == "production":
    import json as json_lib

    class _JSONFormatter(logging.Formatter):
        def format(self, record):
            return json_lib.dumps({
                "ts": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
            })

    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

log = logging.getLogger(__name__)

app = FastAPI(title="Barb", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# --- Request/Response models ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    history: list[dict] = Field(default_factory=list)
    instrument: str = "NQ"


class ChatResponse(BaseModel):
    answer: str
    data: list
    cost: dict


# --- Assistant cache ---

@lru_cache
def _get_assistant(instrument: str) -> Assistant:
    """One Assistant (and genai.Client) per instrument, reused across requests."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    instrument_config = get_instrument(instrument)
    if not instrument_config:
        raise ValueError(f"Unknown instrument: {instrument}")

    return Assistant(
        api_key=settings.gemini_api_key,
        instrument=instrument,
        df=load_data(instrument),
        sessions=instrument_config["sessions"],
    )


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    try:
        assistant = _get_assistant(request.instrument)
    except RuntimeError:
        raise HTTPException(500, "GEMINI_API_KEY not configured")
    except ValueError:
        raise HTTPException(400, f"Unknown instrument: {request.instrument}")

    start = time.time()
    try:
        result = assistant.chat(request.message, request.history)
    except Exception:
        log.exception("Chat error")
        raise HTTPException(503, "Service temporarily unavailable")

    latency = time.time() - start
    log.info("Chat completed: %.2fs, $%.6f", latency, result["cost"]["total_cost"])

    return ChatResponse(answer=result["answer"], data=result["data"], cost=result["cost"])
