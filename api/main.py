"""Barb API."""

import json
import logging
import os
import time
from contextlib import asynccontextmanager
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
from config.market.instruments import get_instrument, register_instrument

if os.getenv("ENV") == "production":

    class _JSONFormatter(logging.Formatter):
        def format(self, record):
            return json.dumps(
                {
                    "ts": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "msg": record.getMessage(),
                    "request_id": getattr(record, "request_id", ""),
                }
            )

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


def _load_instruments():
    """Load all instruments from Supabase instrument_full view into cache."""
    db = get_db()
    result = db.table("instrument_full").select("*").execute()
    for row in result.data:
        register_instrument(row)
    log.info("Loaded %d instruments from Supabase", len(result.data))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_instruments()
    yield


app = FastAPI(title="Barb", version="0.1.0", lifespan=lifespan)

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


class AddUserInstrumentRequest(BaseModel):
    instrument: str


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


class BacktestRequest(BaseModel):
    instrument: str = "NQ"
    strategy: dict
    session: str | None = None
    period: str | None = None
    title: str = "Backtest"


class ContinueRequest(BaseModel):
    conversation_id: str = Field(..., min_length=1)
    tool_use_id: str = Field(..., min_length=1)
    tool_input: dict
    model_response: str
    data_card: dict


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
        df_daily=load_data(instrument, "1d"),
        df_minute=load_data(instrument, "1m"),
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


def _sse(event: str, data) -> str:
    """Format Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def _load_history(db, conversation: dict) -> tuple[list[dict], list[dict]]:
    """Load message history with tool calls from DB.

    Returns (raw_history, history_with_context).
    """
    conv_id = conversation["id"]

    try:
        msg_result = (
            db.table("messages")
            .select("id, role, content")
            .eq("conversation_id", conv_id)
            .order("created_at", desc=False)
            .execute()
        )
    except Exception:
        log.exception("Failed to load messages")
        raise HTTPException(503, "Service temporarily unavailable")

    model_ids = [m["id"] for m in msg_result.data if m["role"] == "assistant"]
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
        if m["role"] == "assistant" and m["id"] in tc_by_msg:
            entry["tool_calls"] = tc_by_msg[m["id"]]
        raw_history.append(entry)

    history = build_history_with_context(conversation.get("context"), raw_history)
    return raw_history, history


def _persist_chat(
    db,
    conversation: dict,
    user_message: str,
    result: dict,
) -> tuple[str, bool]:
    """Persist user message, model response, tool calls, and update usage.

    Returns (message_id, persisted).
    """
    conv_id = conversation["id"]
    message_id = ""
    try:
        log.info("Persisting chat: conv=%s, user_msg_len=%d", conv_id, len(user_message))

        db.table("messages").insert(
            {
                "conversation_id": conv_id,
                "role": "user",
                "content": user_message,
            }
        ).execute()
        log.info("User message saved: conv=%s", conv_id)

        data_to_save = result["data"] or None
        log.info(
            "Saving model message: conv=%s, answer_len=%d, data_blocks=%d",
            conv_id,
            len(result["answer"]),
            len(result["data"]) if result["data"] else 0,
        )

        model_msg = (
            db.table("messages")
            .insert(
                {
                    "conversation_id": conv_id,
                    "role": "assistant",
                    "content": result["answer"],
                    "data": data_to_save,
                    "usage": result["usage"],
                }
            )
            .execute()
        )
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

        # Save pending tool call if present (not yet executed)
        pending = result.get("pending_tool")
        if pending:
            db.table("tool_calls").insert(
                {
                    "message_id": message_id,
                    "tool_name": "run_backtest",
                    "input": pending["input"],
                    "output": None,
                    "error": None,
                    "duration_ms": 0,
                }
            ).execute()
            log.info("Pending tool call saved: conv=%s", conv_id)

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
            "id",
            conv_id,
        ).execute()

        log.info("Chat persisted successfully: conv=%s, msg_id=%s", conv_id, message_id)

    except Exception as e:
        log.exception("Failed to persist chat: conv=%s, error=%s", conv_id, str(e))
        return message_id, False

    return message_id, True


def _maybe_summarize(
    db,
    assistant,
    conversation: dict,
    raw_history: list[dict],
    msg_count: int,
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
            assistant.client,
            assistant.model,
            old_summary,
            msgs_to_summarize,
        )
        db.table("conversations").update(
            {
                "context": {"summary": summary_text, "summary_up_to": cutoff},
            }
        ).eq("id", conversation["id"]).execute()

        log.info(
            "Summarized conv=%s: %d exchanges -> summary_up_to=%d",
            conversation["id"],
            msg_count,
            cutoff,
        )
    except Exception:
        log.exception("Failed to summarize: conv=%s", conversation["id"])


def _persist_continuation(
    db,
    conversation: dict,
    done_data: dict,
    tool_result: str,
    tool_input: dict | None = None,
) -> tuple[str, bool]:
    """Persist continuation — update existing assistant message with backtest results.

    The initial stream saved a partial message with pending tool_call (output=None).
    Now we combine the initial text with the analysis and fill in the tool output.
    """
    conv_id = conversation["id"]
    message_id = ""
    try:
        # Find the last assistant message (the one with pending tool_call)
        last_msg = (
            db.table("messages")
            .select("id, content, usage")
            .eq("conversation_id", conv_id)
            .eq("role", "assistant")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not last_msg.data:
            log.error("No assistant message to update: conv=%s", conv_id)
            return "", False

        message_id = last_msg.data[0]["id"]
        existing_content = last_msg.data[0]["content"] or ""
        combined_content = existing_content + done_data["answer"]
        data_to_save = done_data["data"] or None

        # Update the message with combined content + data
        db.table("messages").update(
            {
                "content": combined_content,
                "data": data_to_save,
                "usage": done_data["usage"],
            }
        ).eq("id", message_id).execute()

        # Fill in the pending tool_call (output was NULL)
        update_fields = {"output": _parse_tool_output(tool_result)}
        if tool_input is not None:
            update_fields["input"] = tool_input
        db.table("tool_calls").update(update_fields).eq(
            "message_id",
            message_id,
        ).is_("output", "null").execute()

        # Additional tool calls from continuation (if model called more tools)
        if done_data.get("tool_calls"):
            tool_rows = [
                {
                    "message_id": message_id,
                    "tool_name": tc["tool_name"],
                    "input": tc["input"],
                    "output": _parse_tool_output(tc["output"]),
                    "error": tc["error"],
                    "duration_ms": tc["duration_ms"],
                }
                for tc in done_data["tool_calls"]
            ]
            db.table("tool_calls").insert(tool_rows).execute()

        old_usage = conversation["usage"]
        new_usage = done_data["usage"]
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
            "message_count": old_usage["message_count"],
        }
        db.table("conversations").update({"usage": accumulated}).eq("id", conv_id).execute()

        log.info("Continuation persisted: conv=%s, msg_id=%s", conv_id, message_id)
    except Exception as e:
        log.exception("Failed to persist continuation: conv=%s, error=%s", conv_id, str(e))
        return message_id, False

    return message_id, True


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
    checks["data"] = "ok" if (DATA_DIR / "1d" / "futures" / "NQ.parquet").exists() else "fail"

    failed = any(v == "fail" for v in checks.values())
    status = "fail" if failed else "ok"

    return JSONResponse(
        status_code=503 if failed else 200,
        content={"status": status, "checks": checks},
    )


@app.get("/api/instruments")
def list_instruments(search: str | None = None, category: str | None = None):
    """List available instruments with optional search and category filter."""
    db = get_db()
    try:
        query = (
            db.table("instruments")
            .select("symbol, name, exchange, category, image_url, notes")
            .eq("active", True)
        )
        if category:
            query = query.eq("category", category)
        if search:
            query = query.or_(f"symbol.ilike.%{search}%,name.ilike.%{search}%")
        result = query.order("category").order("symbol").execute()
    except Exception:
        log.exception("Failed to list instruments")
        raise HTTPException(503, "Failed to list instruments")

    return result.data


@app.get("/api/instruments/{symbol}/ohlc")
def get_ohlc(symbol: str):
    """Return all daily OHLC bars for an instrument."""
    try:
        df = load_data(symbol, "1d")
    except FileNotFoundError:
        raise HTTPException(404, f"Instrument not found: {symbol}")

    records = []
    for ts, row in df.iterrows():
        records.append(
            {
                "time": str(ts)[:10],
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": int(row["volume"]),
            }
        )
    return records


@app.post("/api/admin/reload-data")
def reload_data(token: str = ""):
    """Clear load_data LRU cache so next request picks up fresh parquet files."""
    settings = get_settings()
    if not settings.admin_token or token != settings.admin_token:
        raise HTTPException(403, "Invalid admin token")
    load_data.cache_clear()
    _get_assistant.cache_clear()
    log.info("Data and assistant caches cleared")
    return {"status": "ok"}


@app.post("/api/backtest")
def run_backtest_endpoint(request: BacktestRequest, user: dict = Depends(get_current_user)):
    """Run backtest directly — no LLM, returns DataCard."""
    from assistant.tools.backtest import _build_backtest_card, run_backtest_tool

    config = get_instrument(request.instrument)
    if not config:
        raise HTTPException(400, f"Unknown instrument: {request.instrument}")

    df_minute = load_data(request.instrument, "1m")

    try:
        bt = run_backtest_tool(
            {
                "strategy": request.strategy,
                "session": request.session,
                "period": request.period,
            },
            df_minute,
            config["sessions"],
        )
    except Exception as e:
        raise HTTPException(400, str(e))

    card = _build_backtest_card(bt["result"], request.title)
    return {
        "model_response": bt["model_response"],
        "card": card,
    }


@app.get("/api/user-instruments")
def list_user_instruments(user: dict = Depends(get_current_user)):
    """List instruments the user has added to their workspace."""
    db = get_db()
    try:
        result = (
            db.table("user_instruments")
            .select("instrument, added_at, instruments(name, exchange, image_url)")
            .eq("user_id", user["sub"])
            .order("added_at")
            .execute()
        )
    except Exception:
        log.exception("Failed to list user instruments")
        raise HTTPException(503, "Failed to list user instruments")

    return [
        {
            "instrument": row["instrument"],
            "name": row["instruments"]["name"],
            "exchange": row["instruments"]["exchange"],
            "image_url": row["instruments"]["image_url"],
            "added_at": row["added_at"],
        }
        for row in result.data
    ]


@app.post("/api/user-instruments", status_code=201)
def add_user_instrument(
    request: AddUserInstrumentRequest,
    user: dict = Depends(get_current_user),
):
    """Add an instrument to the user's workspace."""
    if not get_instrument(request.instrument):
        raise HTTPException(400, f"Unknown instrument: {request.instrument}")

    db = get_db()
    try:
        result = (
            db.table("user_instruments")
            .insert({"user_id": user["sub"], "instrument": request.instrument})
            .execute()
        )
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(409, "Instrument already added")
        log.exception("Failed to add user instrument")
        raise HTTPException(503, "Failed to add user instrument")

    return result.data[0]


@app.delete("/api/user-instruments/{symbol}")
def remove_user_instrument(
    symbol: str,
    user: dict = Depends(get_current_user),
):
    """Remove an instrument from the user's workspace."""
    db = get_db()
    try:
        result = (
            db.table("user_instruments")
            .delete()
            .eq("user_id", user["sub"])
            .eq("instrument", symbol)
            .execute()
        )
    except Exception:
        log.exception("Failed to remove user instrument")
        raise HTTPException(503, "Failed to remove user instrument")

    if not result.data:
        raise HTTPException(404, "Instrument not in your workspace")

    return {"ok": True}


@app.post("/api/conversations")
def create_conversation(
    request: CreateConversationRequest,
    user: dict = Depends(get_current_user),
) -> ConversationResponse:
    if not get_instrument(request.instrument):
        raise HTTPException(400, f"Unknown instrument: {request.instrument}")

    db = get_db()
    try:
        result = (
            db.table("conversations")
            .insert(
                {
                    "user_id": user["sub"],
                    "instrument": request.instrument,
                }
            )
            .execute()
        )
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
    instrument: str | None = None,
    user: dict = Depends(get_current_user),
) -> list[ConversationResponse]:
    db = get_db()
    try:
        query = (
            db.table("conversations").select("*").eq("user_id", user["sub"]).eq("status", "active")
        )
        if instrument:
            query = query.eq("instrument", instrument)
        result = query.order("updated_at", desc=True).execute()
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

    raw_history, history = _load_history(db, conversation)

    def generate():
        # Update title immediately so sidebar reflects it before model responds
        if conversation["title"] == "New conversation":
            title = request.message[:80]
            if len(request.message) > 80:
                title += "..."
            try:
                db.table("conversations").update({"title": title}).eq(
                    "id",
                    conversation["id"],
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
            user["sub"],
            request.conversation_id,
            latency,
            done_data["usage"]["total_cost"],
        )

        message_id, persisted = _persist_chat(
            db,
            conversation,
            request.message,
            done_data,
        )

        yield _sse("persist", {"message_id": message_id, "persisted": persisted})

        # Summarize context (best effort, skip for pending — conversation not complete)
        if persisted and not done_data.get("pending_tool"):
            msg_count = conversation["usage"]["message_count"] + 1
            _maybe_summarize(
                db,
                assistant,
                conversation,
                raw_history,
                msg_count,
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chat/continue")
def chat_continue(request: ContinueRequest, user: dict = Depends(get_current_user)):
    """Continue chat after backtest card approval — model analyzes results."""
    db = get_db()

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

    _, history = _load_history(db, conversation)

    def generate():
        start = time.time()
        done_data = None

        try:
            for event in assistant.continue_stream(
                history,
                request.tool_use_id,
                request.model_response,
                request.data_card,
            ):
                yield _sse(event["event"], event["data"])
                if event["event"] == "done":
                    done_data = event["data"]
        except Exception:
            log.exception("Continue stream error: conv=%s", request.conversation_id)
            yield _sse("error", {"error": "Service temporarily unavailable"})
            return

        latency = time.time() - start

        if not done_data:
            return

        log.info(
            "Continue stream user=%s conv=%s: %.2fs, $%.6f",
            user["sub"],
            request.conversation_id,
            latency,
            done_data["usage"]["total_cost"],
        )

        message_id, persisted = _persist_continuation(
            db,
            conversation,
            done_data,
            tool_result=request.model_response,
            tool_input=request.tool_input,
        )
        yield _sse("persist", {"message_id": message_id, "persisted": persisted})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
