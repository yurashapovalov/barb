"""Barb API."""

import logging
import os
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(500, "GEMINI_API_KEY not configured")

    instrument_config = get_instrument(request.instrument)
    if not instrument_config:
        raise HTTPException(400, f"Unknown instrument: {request.instrument}")

    df = load_data(request.instrument)
    sessions = instrument_config["sessions"]

    assistant = Assistant(
        api_key=settings.gemini_api_key,
        instrument=request.instrument,
        df=df,
        sessions=sessions,
    )

    start = time.time()
    try:
        result = assistant.chat(request.message, request.history)
    except Exception:
        log.exception("Chat error")
        raise HTTPException(503, "Service temporarily unavailable")

    latency = time.time() - start
    log.info(f"Chat completed: {latency:.2f}s, ${result['cost']['total_cost']:.6f}")

    return ChatResponse(answer=result["answer"], data=result["data"], cost=result["cost"])
