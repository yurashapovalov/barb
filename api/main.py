"""Barb API."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.barb import Barb, BarbError, Cost
from api.config import get_settings

import json as json_lib
import os

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json_lib.dumps({
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        })

# JSON logging in production, human-readable in dev
if os.getenv("ENV") == "production":
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

log = logging.getLogger(__name__)


# Simple metrics (in-memory)
class Metrics:
    def __init__(self):
        self.requests = 0
        self.errors = 0
        self.total_cost = 0.0
        self.total_latency = 0.0

metrics = Metrics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Startup: validate config
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")
    log.info("Barb API starting")
    yield
    # Shutdown
    log.info(f"Shutting down. Stats: requests={metrics.requests}, errors={metrics.errors}, cost=${metrics.total_cost:.4f}")


app = FastAPI(title="Barb", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Question(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)


class Answer(BaseModel):
    answer: str
    cost: Cost


class HealthResponse(BaseModel):
    status: str
    requests: int
    errors: int
    total_cost: float


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        requests=metrics.requests,
        errors=metrics.errors,
        total_cost=metrics.total_cost,
    )


@app.post("/api/chat")
def chat(q: Question) -> Answer:
    start = time.time()
    metrics.requests += 1

    try:
        result = Barb().ask(q.message)
    except BarbError as e:
        metrics.errors += 1
        log.error(f"Chat error: {e}")
        raise HTTPException(503, "Service temporarily unavailable")

    latency = time.time() - start
    metrics.total_cost += result.cost.total_cost
    metrics.total_latency += latency

    log.info(f"Request completed: {latency:.2f}s, ${result.cost.total_cost:.6f}")
    return Answer(answer=result.answer, cost=result.cost)
