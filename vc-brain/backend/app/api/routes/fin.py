"""POST /api/fin/chat — Conversational sourcing agent endpoint.

Fin is a conversational agent that:
1. Greets the investor and asks open-ended questions
2. Extracts thesis fields from natural language
3. Actively grills for missing/ambiguous fields
4. Shows a live-synced thesis summary
5. Confirms before executing
6. Narrates pipeline progress in real time
7. Hands off to the Dashboard with results

Uses the z-ai LLM SDK for conversation + thesis extraction.
Does NOT auto-execute without explicit confirmation.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class FinMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class FinChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    thesis_state: Optional[dict] = None  # current parsed thesis fields
    conversation_history: list[FinMessage] = Field(default_factory=list)
    confirmed: bool = False  # whether the investor confirmed the thesis


class FinChatResponse(BaseModel):
    reply: str
    thesis_state: dict  # updated thesis fields
    conversation_id: str
    pipeline_started: bool = False
    pipeline_status: Optional[str] = None
    dashboard_url: Optional[str] = None  # link to results when done


# Thesis field extraction prompt
EXTRACTION_SYSTEM = """You are Fin, a sharp, efficient junior partner at a VC firm doing intake for a senior investor. You're helping the investor articulate their investment thesis through natural conversation.

Your job:
1. Listen to what the investor says and extract thesis fields: sectors, stage, geography, check_size_usd, ownership_target_pct, risk_appetite
2. Track which required fields are still missing or ambiguous
3. Ask natural, specific follow-up questions for missing fields — one or two at a time, not a checklist dump
4. Once all fields are filled, show the complete parsed thesis back and ask for confirmation
5. Never silently apply a thesis or start a pipeline without explicit confirmation

Tone: direct, warm, no corporate filler. Sound like a competent junior partner, not a customer-support bot. Ask good questions instead of generic ones.

Required thesis fields (all must be filled before confirmation):
- sectors: list of sectors (e.g. ["AI infra", "DevTools"])
- stage: list of stages (e.g. ["pre-seed", "seed"])
- geography: list of ISO-2 country codes (e.g. ["DE", "US"])
- check_size_usd: integer (e.g. 100000)
- ownership_target_pct: float (e.g. 7.5)
- risk_appetite: object with accepts_cold_start, accepts_no_github, min_conviction_score, allow_neutral_market

When responding, ALWAYS include a JSON block at the end of your message in this exact format:
```json
{"thesis_state": {"sectors": [...], "stage": [...], "geography": [...], "check_size_usd": null, "ownership_target_pct": null, "risk_appetite": null, "all_filled": false}}
```

Set all_filled to true ONLY when all 6 fields are populated. Leave fields as null if not yet discussed.

If the investor confirms ("looks right", "yes", "go ahead", "confirmed"), set all_filled=true and add "confirmed": true to the JSON.

Never start the pipeline yourself — just set confirmed=true and the backend will handle execution."""


@router.post("/fin/chat", response_model=FinChatResponse)
async def fin_chat(req: FinChatRequest) -> FinChatResponse:
    """Handle a conversational turn with Fin.

    Flow:
    1. Send the investor's message + conversation history + current thesis state to the LLM
    2. LLM extracts thesis fields and generates a reply
    3. If thesis is confirmed, start the pipeline
    4. Return the reply + updated thesis state
    """
    import asyncio

    conversation_id = req.conversation_id or str(uuid.uuid4())
    current_thesis = req.thesis_state or {}

    # Build the conversation for the LLM
    messages = [{"role": "assistant", "content": EXTRACTION_SYSTEM}]

    # Add conversation history
    for msg in req.conversation_history:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current thesis state context
    thesis_context = f"\n[Current thesis state: {json.dumps(current_thesis)}]"
    messages.append({"role": "user", "content": req.message + thesis_context})

    # Call the LLM
    try:
        reply_text, extracted_thesis = await _call_fin_llm(messages)
    except Exception as e:
        logger.error("Fin LLM call failed: %s", e)
        reply_text = "I'm having trouble processing that. Could you rephrase?"
        extracted_thesis = current_thesis

    # Check if confirmed — start pipeline
    pipeline_started = False
    pipeline_status = None
    dashboard_url = None

    if extracted_thesis.get("confirmed") and extracted_thesis.get("all_filled"):
        pipeline_started = True
        pipeline_status = "starting"
        # The pipeline will be triggered by the frontend calling POST /applications
        # or POST /outbound/scan with the new thesis — Fin just narrates
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


async def _call_fin_llm(messages: list[dict]) -> tuple[str, dict]:
    """Call the z-ai LLM for Fin's conversation + thesis extraction.

    Returns (reply_text, extracted_thesis_state).
    """
    try:
        # Use the z-ai CLI for the LLM call
        import subprocess

        # Build the prompt as JSON
        prompt_data = json.dumps(messages[-1]["content"])  # last user message
        system_prompt = messages[0]["content"]

        # Call z-ai chat CLI
        result = subprocess.run(
            ["z-ai", "chat", "-p", prompt_data, "-s", system_prompt, "--thinking"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"z-ai CLI failed: {result.stderr[:200]}")

        # Parse the response
        raw = result.stdout
        idx = raw.find("{")
        if idx >= 0:
            data = json.loads(raw[idx:])
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            reply = raw.strip()

        # Extract thesis state from the reply
        thesis_state = _extract_thesis_from_reply(reply)

        # Clean the reply — remove the JSON block from the visible text
        clean_reply = _strip_json_block(reply)

        return clean_reply, thesis_state

    except subprocess.TimeoutError:
        raise RuntimeError("LLM call timed out")
    except Exception as e:
        logger.error("Fin LLM error: %s", e)
        raise


def _extract_thesis_from_reply(reply: str) -> dict:
    """Extract the thesis_state JSON block from the LLM reply."""
    import re

    # Find JSON block
    match = re.search(r'```json\s*(\{[^}]+\})\s*```', reply)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding raw JSON object
    match = re.search(r'\{"thesis_state":\s*(\{[^}]+\})\}', reply)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return {"all_filled": False}


def _strip_json_block(reply: str) -> str:
    """Remove the JSON thesis_state block from the visible reply text."""
    import re
    # Remove ```json ... ``` blocks
    cleaned = re.sub(r'```json\s*\{[^}]+\}\s*```', '', reply).strip()
    # Remove raw {"thesis_state": ...} blocks
    cleaned = re.sub(r'\{"thesis_state":\s*\{[^}]+\}\}', '', cleaned).strip()
    return cleaned
