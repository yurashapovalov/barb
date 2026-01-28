"""Chat endpoints for the trading assistant."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.agent.analyst import TradingAnalyst

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request from frontend."""
    message: str
    conversation_id: str | None = None
    user_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response to frontend."""
    answer: str
    code: str | None = None
    data: dict | list | None = None
    conversation_id: str | None = None


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return analysis."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    analyst = TradingAnalyst()

    try:
        result = await analyst.analyze(request.message)
        return ChatResponse(
            answer=result.answer,
            code=result.code,
            data=result.data,
            conversation_id=request.conversation_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
