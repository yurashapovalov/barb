"""Barb API."""

import json
import logging
import os
import time
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from api.auth import get_current_user
from api.config import get_settings
from api.db import get_db
from api.errors import register_error_handlers
from api.request_id import RequestIdFilter, RequestIdMiddleware
from assistant.chat import Assistant
from barb.data import DATA_DIR, load_data
from config.market.instruments import get_instrument

if os.getenv("ENV") == "production":
    class _JSONFormatter(logging.Formatter):
        def format(self, record):
            return json.dumps({
                "ts": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
                "request_id": getattr(record, "request_id", ""),
            })

    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s",
    )

logging.root.addFilter(RequestIdFilter())

log = logging.getLogger(__name__)

app = FastAPI(title="Barb", version="0.1.0")

_cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)
app.add_middleware(RequestIdMiddleware)

register_error_handlers(app)


# --- Request/Response models ---

class CreateConversationRequest(BaseModel):
    instrument: str = "NQ"


class ConversationResponse(BaseModel):
    id: str
    title: str
    instrument: str
    usage: dict
    created_at: str
    updated_at: str


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=10000)


class UsageBlock(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cached_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    thinking_cost: float = 0.0
    total_cost: float = 0.0


class DataBlock(BaseModel):
    query: dict
    result: object = None
    rows: int | None = None
    session: str | None = None
    timeframe: str | None = None


class ToolCallBlock(BaseModel):
    tool_name: str
    input: dict | None = None
    output: object = None
    error: str | None = None
    duration_ms: int | None = None


class ChatResponse(BaseModel):
    message_id: str
    conversation_id: str
    answer: str
    data: list[DataBlock]
    usage: UsageBlock
    tool_calls: list[ToolCallBlock] = Field(default_factory=list)
    persisted: bool = True


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


def _parse_tool_output(output):
    """Parse tool output string to dict for JSONB storage."""
    if output is None:
        return None
    if isinstance(output, (dict, list)):
        return output
    try:
        return json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return {"raw": str(output)}


# --- Endpoints ---

@app.get("/health")
def health():
    checks = {}

    # Supabase
    try:
        get_db().table("conversations").select("id").limit(1).execute()
        checks["supabase"] = "ok"
    except Exception:
        checks["supabase"] = "fail"

    # Gemini API key
    checks["gemini"] = "ok" if get_settings().gemini_api_key else "fail"

    # Data file
    checks["data"] = "ok" if (DATA_DIR / "NQ.parquet").exists() else "fail"

    failed = any(v == "fail" for v in checks.values())
    status = "fail" if failed else "ok"

    return JSONResponse(
        status_code=503 if failed else 200,
        content={"status": status, "checks": checks},
    )


@app.post("/api/conversations")
def create_conversation(
    request: CreateConversationRequest,
    user: dict = Depends(get_current_user),
) -> ConversationResponse:
    if not get_instrument(request.instrument):
        raise HTTPException(400, f"Unknown instrument: {request.instrument}")

    db = get_db()
    try:
        result = db.table("conversations").insert({
            "user_id": user["sub"],
            "instrument": request.instrument,
        }).execute()
    except Exception:
        log.exception("Failed to create conversation")
        raise HTTPException(503, "Failed to create conversation")

    row = result.data[0]
    return ConversationResponse(
        id=row["id"],
        title=row["title"],
        instrument=row["instrument"],
        usage=row["usage"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.get("/api/conversations")
def list_conversations(
    user: dict = Depends(get_current_user),
) -> list[ConversationResponse]:
    db = get_db()
    try:
        result = (
            db.table("conversations")
            .select("*")
            .eq("user_id", user["sub"])
            .order("updated_at", desc=True)
            .execute()
        )
    except Exception:
        log.exception("Failed to list conversations")
        raise HTTPException(503, "Failed to list conversations")

    return [
        ConversationResponse(
            id=r["id"],
            title=r["title"],
            instrument=r["instrument"],
            usage=r["usage"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in result.data
    ]


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    try:
        check = (
            db.table("conversations")
            .select("id")
            .eq("id", conversation_id)
            .eq("user_id", user["sub"])
            .execute()
        )
    except Exception:
        log.exception("Failed to check conversation ownership")
        raise HTTPException(503, "Failed to delete conversation")

    if not check.data:
        raise HTTPException(404, "Conversation not found")

    try:
        db.table("conversations").delete().eq("id", conversation_id).execute()
    except Exception:
        log.exception("Failed to delete conversation: %s", conversation_id)
        raise HTTPException(503, "Failed to delete conversation")

    return {"ok": True}


@app.post("/api/chat")
def chat(request: ChatRequest, user: dict = Depends(get_current_user)) -> ChatResponse:
    db = get_db()

    # Load conversation, verify ownership
    try:
        conv_result = (
            db.table("conversations")
            .select("*")
            .eq("id", request.conversation_id)
            .eq("user_id", user["sub"])
            .execute()
        )
    except Exception:
        log.exception("Failed to load conversation")
        raise HTTPException(503, "Service temporarily unavailable")

    if not conv_result.data:
        raise HTTPException(404, "Conversation not found")

    conversation = conv_result.data[0]
    instrument = conversation["instrument"]

    # Get assistant
    try:
        assistant = _get_assistant(instrument)
    except RuntimeError:
        raise HTTPException(500, "GEMINI_API_KEY not configured")
    except ValueError:
        raise HTTPException(400, f"Unknown instrument: {instrument}")

    # Load message history from DB
    try:
        msg_result = (
            db.table("messages")
            .select("role, content")
            .eq("conversation_id", request.conversation_id)
            .order("created_at", desc=False)
            .execute()
        )
    except Exception:
        log.exception("Failed to load messages")
        raise HTTPException(503, "Service temporarily unavailable")

    history = [{"role": m["role"], "text": m["content"]} for m in msg_result.data]

    # Call Gemini
    start = time.time()
    try:
        result = assistant.chat(request.message, history)
    except Exception:
        log.exception("Chat error")
        raise HTTPException(503, "Service temporarily unavailable")

    latency = time.time() - start
    log.info(
        "Chat user=%s conv=%s: %.2fs, $%.6f",
        user["sub"], request.conversation_id, latency, result["usage"]["total_cost"],
    )

    # Persist to database
    persisted = True
    message_id = ""
    try:
        # Write user message
        db.table("messages").insert({
            "conversation_id": request.conversation_id,
            "role": "user",
            "content": request.message,
        }).execute()

        # Write model message
        model_msg = db.table("messages").insert({
            "conversation_id": request.conversation_id,
            "role": "model",
            "content": result["answer"],
            "data": result["data"] or None,
            "usage": result["usage"],
        }).execute()
        message_id = model_msg.data[0]["id"]

        # Write tool calls
        if result["tool_calls"]:
            tool_rows = [
                {
                    "message_id": message_id,
                    "tool_name": tc["tool_name"],
                    "input": tc["input"],
                    "output": _parse_tool_output(tc["output"]),
                    "error": tc["error"],
                    "duration_ms": tc["duration_ms"],
                }
                for tc in result["tool_calls"]
            ]
            db.table("tool_calls").insert(tool_rows).execute()

        # Accumulate usage on conversation
        old_usage = conversation["usage"]
        new_usage = result["usage"]
        accumulated = {
            "input_tokens": old_usage["input_tokens"] + new_usage["input_tokens"],
            "output_tokens": old_usage["output_tokens"] + new_usage["output_tokens"],
            "thinking_tokens": old_usage["thinking_tokens"] + new_usage["thinking_tokens"],
            "cached_tokens": old_usage["cached_tokens"] + new_usage["cached_tokens"],
            "input_cost": old_usage["input_cost"] + new_usage["input_cost"],
            "output_cost": old_usage["output_cost"] + new_usage["output_cost"],
            "thinking_cost": old_usage["thinking_cost"] + new_usage["thinking_cost"],
            "total_cost": old_usage["total_cost"] + new_usage["total_cost"],
            "message_count": old_usage["message_count"] + 1,
        }

        update_fields: dict = {"usage": accumulated}

        # Set title from first user message
        if conversation["title"] == "New conversation":
            title = request.message[:80]
            if len(request.message) > 80:
                title += "..."
            update_fields["title"] = title

        db.table("conversations").update(update_fields).eq(
            "id", request.conversation_id
        ).execute()

    except Exception:
        log.exception("Failed to persist chat: conv=%s", request.conversation_id)
        persisted = False

    return ChatResponse(
        message_id=message_id,
        conversation_id=request.conversation_id,
        answer=result["answer"],
        data=result["data"],
        usage=result["usage"],
        tool_calls=result["tool_calls"],
        persisted=persisted,
    )
