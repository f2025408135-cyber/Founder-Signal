"""Fin - a structured thesis-intake agent backed by the configured LLM client."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.llm.client import chat_complete_json

router = APIRouter()


class FinMessage(BaseModel):
    role: str
    content: str


class FinChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    thesis_state: dict[str, Any] = Field(default_factory=dict)
    conversation_history: list[FinMessage] = Field(default_factory=list)
    confirmed: bool = False


class FinChatResponse(BaseModel):
    reply: str
    thesis_state: dict[str, Any]
    conversation_id: str
    pipeline_started: bool = False
    pipeline_status: Optional[str] = None
    dashboard_url: Optional[str] = None


SYSTEM_PROMPT = """You are Fin, an incisive junior investing partner helping an investor define a screening thesis.
Extract only what the investor has actually stated. Ask one focused follow-up for the most important missing field.
Required fields are sectors, stage, geography (ISO-2 codes), check_size_usd, ownership_target_pct, and risk_appetite.
Return JSON only with this schema:
{"reply": "short useful reply", "thesis_state": {"sectors": [], "stage": [], "geography": [], "check_size_usd": null, "ownership_target_pct": null, "risk_appetite": null, "all_filled": false, "confirmed": false}}
Never claim that a pipeline was started. Mark confirmed true only when the investor explicitly confirms a complete thesis."""


@router.post("/fin/chat", response_model=FinChatResponse)
async def fin_chat(request: FinChatRequest) -> FinChatResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())
    context = {
        "current_thesis": request.thesis_state,
        "history": [message.model_dump() for message in request.conversation_history[-8:]],
        "latest_message": request.message,
        "confirmed": request.confirmed,
    }
    try:
        result = await chat_complete_json(SYSTEM_PROMPT, context, temperature=0.2, span_name="fin.thesis_intake")
        thesis_state = result.get("thesis_state", {}) if isinstance(result, dict) else {}
        reply = result.get("reply", "I captured that. What should the next thesis constraint be?") if isinstance(result, dict) else "I captured that. What should the next thesis constraint be?"
    except Exception:
        thesis_state = request.thesis_state
        reply = "Fin is unavailable right now. Your existing thesis draft remains intact; try again once the AI service reconnects."
    return FinChatResponse(reply=reply, thesis_state=thesis_state, conversation_id=conversation_id)
