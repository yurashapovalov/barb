"""Barb API."""

import json
import logging
import os
import time
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse, StreamingResponse

from api.auth import get_current_user
from api.config import get_settings
from api.db import get_db
from api.errors import register_error_handlers
from api.request_id import RequestIdFilter, RequestIdMiddleware
from assistant.chat import Assistant
from assistant.context import (
    WINDOW_SIZE,
    build_history_with_context,
    should_summarize,
    summarize,
)
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


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    data: list[dict] | None = None
    usage: dict | None = None
    created_at: str


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=10000)


# --- Assistant cache ---

@lru_cache
def _get_assistant(instrument: str) -> Assistant:
    """One Assistant per instrument, reused across requests."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    instrument_config = get_instrument(instrument)
    if not instrument_config:
        raise ValueError(f"Unknown instrument: {instrument}")

    return Assistant(
        api_key=settings.anthropic_api_key,
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


def _persist_chat(
    db, conversation: dict, user_message: str, result: dict,
) -> tuple[str, bool]:
    """Persist user message, model response, tool calls, and update usage.

    Returns (message_id, persisted).
    """
    conv_id = conversation["id"]
    message_id = ""
    try:
        log.info("Persisting chat: conv=%s, user_msg_len=%d", conv_id, len(user_message))

        db.table("messages").insert({
            "conversation_id": conv_id,
            "role": "user",
            "content": user_message,
        }).execute()
        log.info("User message saved: conv=%s", conv_id)

        data_to_save = result["data"] or None
        log.info(
            "Saving model message: conv=%s, answer_len=%d, data_blocks=%d",
            conv_id, len(result["answer"]), len(result["data"]) if result["data"] else 0,
        )

        model_msg = db.table("messages").insert({
            "conversation_id": conv_id,
            "role": "model",
            "content": result["answer"],
            "data": data_to_save,
            "usage": result["usage"],
        }).execute()
        message_id = model_msg.data[0]["id"]
        log.info("Model message saved: conv=%s, msg_id=%s", conv_id, message_id)

        if result["tool_calls"]:
            log.info("Saving tool calls: conv=%s, count=%d", conv_id, len(result["tool_calls"]))
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
            log.info("Tool calls saved: conv=%s", conv_id)

        old_usage = conversation["usage"]
        new_usage = result["usage"]
        old_cr_tokens = old_usage.get("cache_read_tokens", 0)
        old_cw_tokens = old_usage.get("cache_write_tokens", 0)
        old_cr_cost = old_usage.get("cache_read_cost", 0)
        old_cw_cost = old_usage.get("cache_write_cost", 0)
        accumulated = {
            "input_tokens": old_usage["input_tokens"] + new_usage["input_tokens"],
            "output_tokens": old_usage["output_tokens"] + new_usage["output_tokens"],
            "cache_read_tokens": old_cr_tokens + new_usage.get("cache_read_tokens", 0),
            "cache_write_tokens": old_cw_tokens + new_usage.get("cache_write_tokens", 0),
            "input_cost": old_usage["input_cost"] + new_usage["input_cost"],
            "output_cost": old_usage["output_cost"] + new_usage["output_cost"],
            "cache_read_cost": old_cr_cost + new_usage.get("cache_read_cost", 0),
            "cache_write_cost": old_cw_cost + new_usage.get("cache_write_cost", 0),
            "total_cost": old_usage["total_cost"] + new_usage["total_cost"],
            "message_count": old_usage["message_count"] + 1,
        }

        db.table("conversations").update({"usage": accumulated}).eq(
            "id", conv_id,
        ).execute()

        log.info("Chat persisted successfully: conv=%s, msg_id=%s", conv_id, message_id)

    except Exception as e:
        log.exception("Failed to persist chat: conv=%s, error=%s", conv_id, str(e))
        return message_id, False

    return message_id, True


def _maybe_summarize(
    db, assistant, conversation: dict, raw_history: list[dict], msg_count: int,
):
    """Summarize context if threshold reached. Best effort, never raises."""
    if not should_summarize(msg_count, conversation.get("context")):
        return

    try:
        old_context = conversation.get("context") or {}
        old_summary = old_context.get("summary")
        summary_up_to = old_context.get("summary_up_to", 0)
        cutoff = msg_count - WINDOW_SIZE
        msgs_to_summarize = raw_history[summary_up_to * 2 : cutoff * 2]

        summary_text = summarize(
            assistant.client, assistant.model,
            old_summary, msgs_to_summarize,
        )
        db.table("conversations").update({
            "context": {"summary": summary_text, "summary_up_to": cutoff},
        }).eq("id", conversation["id"]).execute()

        log.info(
            "Summarized conv=%s: %d exchanges -> summary_up_to=%d",
            conversation["id"], msg_count, cutoff,
        )
    except Exception:
        log.exception("Failed to summarize: conv=%s", conversation["id"])


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

    # Anthropic API key
    checks["anthropic"] = "ok" if get_settings().anthropic_api_key else "fail"

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
            .eq("status", "active")
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


@app.get("/api/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user),
) -> list[MessageResponse]:
    db = get_db()

    # Verify ownership
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
        raise HTTPException(503, "Service temporarily unavailable")

    if not check.data:
        raise HTTPException(404, "Conversation not found")

    try:
        result = (
            db.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )
    except Exception:
        log.exception("Failed to load messages: conv=%s", conversation_id)
        raise HTTPException(503, "Service temporarily unavailable")

    return [
        MessageResponse(
            id=m["id"],
            conversation_id=m["conversation_id"],
            role=m["role"],
            content=m["content"],
            data=m["data"],
            usage=m["usage"],
            created_at=m["created_at"],
        )
        for m in result.data
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
        db.table("conversations").update({"status": "removed"}).eq("id", conversation_id).execute()
    except Exception:
        log.exception("Failed to remove conversation: %s", conversation_id)
        raise HTTPException(503, "Failed to remove conversation")

    return {"ok": True}


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest, user: dict = Depends(get_current_user)):
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

    try:
        assistant = _get_assistant(instrument)
    except RuntimeError:
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured")
    except ValueError:
        raise HTTPException(400, f"Unknown instrument: {instrument}")

    # Load message history from DB (including tool calls for context)
    try:
        msg_result = (
            db.table("messages")
            .select("id, role, content")
            .eq("conversation_id", request.conversation_id)
            .order("created_at", desc=False)
            .execute()
        )
    except Exception:
        log.exception("Failed to load messages")
        raise HTTPException(503, "Service temporarily unavailable")

    model_ids = [m["id"] for m in msg_result.data if m["role"] == "model"]
    tc_by_msg = {}
    if model_ids:
        try:
            tc_result = (
                db.table("tool_calls")
                .select("message_id, tool_name, input, output")
                .in_("message_id", model_ids)
                .order("created_at", desc=False)
                .execute()
            )
            for tc in tc_result.data:
                tc_by_msg.setdefault(tc["message_id"], []).append(tc)
        except Exception:
            log.warning("Failed to load tool calls for history, continuing without")

    raw_history = []
    for m in msg_result.data:
        entry = {"role": m["role"], "text": m["content"]}
        if m["role"] == "model" and m["id"] in tc_by_msg:
            entry["tool_calls"] = tc_by_msg[m["id"]]
        raw_history.append(entry)
    history = build_history_with_context(conversation.get("context"), raw_history)

    def _sse(event: str, data) -> str:
        return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

    def generate():
        # Update title immediately so sidebar reflects it before model responds
        if conversation["title"] == "New conversation":
            title = request.message[:80]
            if len(request.message) > 80:
                title += "..."
            try:
                db.table("conversations").update({"title": title}).eq(
                    "id", conversation["id"],
                ).execute()
                conversation["title"] = title
                yield _sse("title_update", {"title": title})
            except Exception:
                log.exception("Failed to update title early")

        start = time.time()
        done_data = None

        try:
            for event in assistant.chat_stream(request.message, history):
                yield _sse(event["event"], event["data"])

                if event["event"] == "done":
                    done_data = event["data"]
        except Exception:
            log.exception("Stream error: conv=%s", request.conversation_id)
            yield _sse("error", {"error": "Service temporarily unavailable"})
            return

        latency = time.time() - start

        if not done_data:
            return

        log.info(
            "Chat stream user=%s conv=%s: %.2fs, $%.6f",
            user["sub"], request.conversation_id, latency,
            done_data["usage"]["total_cost"],
        )

        message_id, persisted = _persist_chat(
            db, conversation, request.message, done_data,
        )

        yield _sse("persist", {"message_id": message_id, "persisted": persisted})

        # Summarize context (best effort)
        if persisted:
            msg_count = conversation["usage"]["message_count"] + 1
            _maybe_summarize(
                db, assistant, conversation, raw_history, msg_count,
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
