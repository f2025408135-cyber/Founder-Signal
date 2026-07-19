"""POST /api/fin/chat — Conversational sourcing agent endpoint.

Fin Agent is a conversational agent that:
1. Greets the investor and asks open-ended questions
2. Extracts thesis fields from natural language
3. Actively grills for missing/ambiguous fields
4. Shows a live-synced thesis summary
5. Confirms before executing
6. Narrates pipeline progress in real time
7. Hands off to the Dashboard with results

Uses the z-ai LLM SDK for conversation + thesis extraction.
Does NOT auto-execute without explicit confirmation.

Supports multiple LLM backends:
- z-ai CLI (default, works in-region)
- Gemini API (set GEMINI_API_KEY env var)
- OpenAI API (set OPENAI_API_KEY env var, may be region-blocked)
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class FinMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class FinChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    thesis_state: Optional[dict] = None
    conversation_history: list[FinMessage] = Field(default_factory=list)
    confirmed: bool = False


class FinChatResponse(BaseModel):
    reply: str
    thesis_state: dict
    conversation_id: str
    pipeline_started: bool = False
    pipeline_status: Optional[str] = None
    dashboard_url: Optional[str] = None


EXTRACTION_SYSTEM = """You are Fin Agent, a sharp, efficient junior partner at a VC firm doing intake for a senior investor. You're helping the investor articulate their investment thesis through natural conversation.

Your job:
1. Listen to what the investor says and extract thesis fields: sectors, stage, geography, check_size_usd, ownership_target_pct, risk_appetite
2. Track which required fields are still missing or ambiguous
3. Ask ONE natural, specific follow-up question for a missing field — not a checklist dump
4. Once all fields are filled, show the complete parsed thesis back and ask for confirmation
5. Never silently apply a thesis or start a pipeline without explicit confirmation

Tone: direct, warm, no corporate filler. Sound like a competent junior partner, not a customer-support bot.

Required thesis fields:
- sectors: list of strings (e.g. ["AI infra", "DevTools"])
- stage: list of strings (e.g. ["pre-seed", "seed"])
- geography: list of ISO-2 country codes (e.g. ["DE", "US"])
- check_size_usd: integer (e.g. 100000)
- ownership_target_pct: float (e.g. 7.5)
- risk_appetite: object with accepts_cold_start (bool), accepts_no_github (bool), min_conviction_score (number), allow_neutral_market (bool)

CRITICAL: You MUST ALWAYS end your reply with a JSON code block in EXACTLY this format:

```json
{"thesis_state": {"sectors": ["AI infra"], "stage": ["pre-seed"], "geography": ["DE"], "check_size_usd": null, "ownership_target_pct": null, "risk_appetite": null, "all_filled": false}}
```

Set all_filled to true ONLY when all 6 fields are populated. Leave fields as null if not yet discussed.

If the investor confirms ("looks right", "yes", "go ahead", "confirmed"), set all_filled=true and add "confirmed": true to the JSON.

Never start the pipeline yourself — just set confirmed=true."""


@router.post("/fin/chat", response_model=FinChatResponse)
async def fin_chat(req: FinChatRequest) -> FinChatResponse:
    """Handle a conversational turn with Fin Agent."""
    conversation_id = req.conversation_id or str(uuid.uuid4())
    current_thesis = req.thesis_state or {}

    # Build the conversation for the LLM
    messages = [{"role": "assistant", "content": EXTRACTION_SYSTEM}]
    for msg in req.conversation_history:
        messages.append({"role": msg.role, "content": msg.content})
    thesis_context = f"\n[Current thesis state: {json.dumps(current_thesis)}]"
    messages.append({"role": "user", "content": req.message + thesis_context})

    # Call the LLM (tries multiple backends)
    try:
        reply_text, extracted_thesis = await _call_llm(messages)
    except Exception as e:
        logger.error("Fin Agent LLM call failed: %s", e)
        reply_text = "I'm having trouble connecting right now. Give me a sec and try again."
        extracted_thesis = current_thesis

    # Check if confirmed — start pipeline
    pipeline_started = False
    pipeline_status = None
    dashboard_url = None

    if extracted_thesis.get("confirmed") and extracted_thesis.get("all_filled"):
        pipeline_started = True
        pipeline_status = "starting"
        dashboard_url = f"/inbox?fin={conversation_id}"
        reply_text += "\n\n▶ Starting the pipeline now — I'll narrate progress as it happens."

    return FinChatResponse(
        reply=reply_text,
        thesis_state=extracted_thesis,
        conversation_id=conversation_id,
        pipeline_started=pipeline_started,
        pipeline_status=pipeline_status,
        dashboard_url=dashboard_url,
    )


async def _call_llm(messages: list[dict]) -> tuple[str, dict]:
    """Call the best available LLM backend.

    Tries in order:
    1. Gemini API (if GEMINI_API_KEY is set)
    2. OpenAI API (if OPENAI_API_KEY is set and not region-blocked)
    3. z-ai CLI (fallback, works in-region)
    """
    # Try Gemini first (user-provided keys)
    if settings.gemini_api_key:
        try:
            return await _call_gemini(messages, settings.gemini_api_key)
        except Exception as e:
            logger.warning("Gemini API failed, falling back: %s", e)

    # Try OpenAI (may be region-blocked)
    if settings.openai_api_key:
        try:
            return await _call_openai(messages)
        except Exception as e:
            logger.warning("OpenAI API failed, falling back to z-ai: %s", e)

    # Fallback: z-ai CLI (always works in this environment)
    return await _call_zai_cli(messages)


async def _call_gemini(messages: list[dict], api_key: str) -> tuple[str, dict]:
    """Call Google Gemini API."""
    # Convert messages to Gemini format
    system_prompt = messages[0]["content"] if messages else ""
    conversation_text = ""
    for msg in messages[1:]:
        prefix = "Human:" if msg["role"] == "user" else "Assistant:"
        conversation_text += f"{prefix} {msg['content']}\n"

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    r = await httpx.AsyncClient(timeout=30).apost(
        f"{url}?key={api_key}",
        json={
            "contents": [{"parts": [{"text": system_prompt + "\n\n" + conversation_text}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1000},
        },
    )
    r.raise_for_status()
    data = r.json()
    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    thesis_state = _extract_thesis_from_reply(reply)
    clean_reply = _strip_json_block(reply)
    return clean_reply, thesis_state


async def _call_openai(messages: list[dict]) -> tuple[str, dict]:
    """Call OpenAI API (may be region-blocked)."""
    from app.llm.client import chat_complete

    system_prompt = messages[0]["content"]
    user_content = "\n".join(m["content"] for m in messages[1:])
    reply = await chat_complete(
        system_prompt=system_prompt,
        user_content=user_content,
        model=settings.synthesizer_model,
        temperature=0.3,
    )
    thesis_state = _extract_thesis_from_reply(reply)
    clean_reply = _strip_json_block(reply)
    return clean_reply, thesis_state


async def _call_zai_cli(messages: list[dict]) -> tuple[str, dict]:
    """Call z-ai CLI via subprocess (fallback — always works in this environment)."""
    import asyncio
    import subprocess

    system_prompt = messages[0]["content"]
    user_content = "\n".join(m["content"] for m in messages[1:])

    proc = await asyncio.create_subprocess_exec(
        "z-ai", "chat",
        "-p", user_content,
        "-s", system_prompt,
        "--thinking",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=45)
    raw = stdout.decode("utf-8", errors="replace")

    # Parse JSON response
    idx = raw.find("{")
    if idx >= 0:
        data = json.loads(raw[idx:])
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        reply = raw.strip()

    thesis_state = _extract_thesis_from_reply(reply)
    clean_reply = _strip_json_block(reply)
    return clean_reply, thesis_state


def _extract_thesis_from_reply(reply: str) -> dict:
    """Extract the thesis_state JSON block from the LLM reply.

    Tries multiple patterns since LLMs don't always format JSON consistently.
    """
    import re

    # Pattern 1: Fenced JSON block with thesis_state key
    match = re.search(r'```json\s*(\{.*?"thesis_state".*?\})\s*```', reply, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return data.get("thesis_state", data)
        except json.JSONDecodeError:
            pass

    # Pattern 2: Raw JSON object with thesis_state key
    match = re.search(r'\{"thesis_state":\s*(\{.*?\})\}', reply, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Pattern 3: Fenced JSON block without thesis_state key (direct fields)
    match = re.search(r'```json\s*(\{.*?"sectors".*?\})\s*```', reply, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Pattern 4: Any JSON block at the end of the reply
    match = re.search(r'```json\s*(\{[^`]+\})\s*```', reply, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if "thesis_state" in data:
                return data["thesis_state"]
            return data
        except json.JSONDecodeError:
            pass

    # Fallback: infer from reply text (basic keyword matching)
    fallback = {"all_filled": False}
    reply_lower = reply.lower()
    
    # Extract sectors
    sector_keywords = ["ai infra", "devtools", "climate", "robotics", "fintech", "healthtech", "consumer", "edtech"]
    found_sectors = [s for s in sector_keywords if s in reply_lower]
    if found_sectors:
        fallback["sectors"] = found_sectors
    
    # Extract stage
    stage_keywords = ["pre-seed", "seed", "series-a", "series a"]
    found_stages = [s for s in stage_keywords if s in reply_lower]
    if found_stages:
        fallback["stage"] = found_stages
    
    # Extract geography (ISO-2 codes) — only match standalone 2-letter codes
    geo_match = re.search(r'\b(DE|US|GB|SG|IN|FR|PK)\b', reply, re.IGNORECASE)
    if geo_match:
        fallback["geography"] = [geo_match.group(1).upper()]
    
    # Extract check size
    check_match = re.search(r'\$?(\d{4,})\s*k?\s*(?:usd|dollars)?', reply_lower)
    if check_match:
        fallback["check_size_usd"] = int(check_match.group(1))
    
    return fallback


def _strip_json_block(reply: str) -> str:
    """Remove the JSON thesis_state block from the visible reply text."""
    import re
    cleaned = re.sub(r'```json\s*\{[^}]+\}\s*```', '', reply).strip()
    cleaned = re.sub(r'\{"thesis_state":\s*\{[^}]+\}\}', '', cleaned).strip()
    return cleaned
