"""LLM client — OpenAI + Langfuse wrapper.

Per spec §1 + §5.2 + §10 C1:
- WORKER_MODEL = gpt-5.6-luna for the three parallel scoring agents (cheap tier)
- SYNTHESIZER_MODEL = gpt-5.6-sol for Validator + Aggregator (frontier reasoning)
- Langfuse tracing: prefer langfuse.openai.AsyncOpenAI when configured (auto-traces
  every LLM call). Falls back to plain openai.AsyncOpenAI otherwise.

The Validator and Aggregator are TOOL-LESS: no `bind_tools()` call, no `tools=` argument.
This file exposes simple `chat_complete()` and `llm_complete()` helpers that never bind tools.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


def _get_openai_client():
    """Lazy OpenAI client — avoids import at module load when running tests without OPENAI_API_KEY."""
    from openai import AsyncOpenAI

    return AsyncOpenAI(api_key=settings.openai_api_key)


def _maybe_langfuse_client():
    """Return a langfuse-openai wrapped client if Langfuse is configured, else None.

    Per spec §10 C1: every LLM call should be auto-traced. The langfuse.openai wrapper
    monkey-patches the OpenAI client to emit a span per chat.completions.create() call.
    """
    if not settings.langfuse_is_configured:
        return None
    try:
        from langfuse.openai import openai as langfuse_openai

        # Configure with our credentials — the wrapper handles span creation.
        langfuse_openai_client = langfuse_openai.AsyncOpenAI(api_key=settings.openai_api_key)
        return langfuse_openai_client
    except Exception as e:
        logger.warning("Langfuse wrapper unavailable, falling back to plain OpenAI: %s", e)
        return None


async def chat_complete(
    system_prompt: str,
    user_content: str | dict | list,
    *,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    response_format: Optional[dict] = None,
    trace_id: Optional[str] = None,
    span_name: Optional[str] = None,
) -> str:
    """Single-turn chat completion. Returns the assistant message content as a string.

    - system_prompt: pasted verbatim into the system message
    - user_content: JSON-stringified if dict/list, else passed as-is
    - model: defaults to settings.worker_model
    - response_format: pass {"type": "json_object"} to force JSON mode

    NOTE: this helper NEVER binds tools. The Validator and Aggregator use this
    for tool-less synthesis (spec §5.4).

    Langfuse tracing (spec §10 C1): when configured, every call is auto-traced via
    the langfuse.openai wrapper. The `trace_id` and `span_name` parameters are
    surfaced as Langfuse metadata for cross-referencing in the UI.
    """
    model = model or settings.worker_model
    if isinstance(user_content, (dict, list)):
        user_text = json.dumps(user_content, default=str)
    else:
        user_text = str(user_content)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    # Prefer Langfuse-wrapped client for tracing; fall back to plain OpenAI.
    client = _maybe_langfuse_client() or _get_openai_client()

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if response_format is not None:
        kwargs["response_format"] = response_format
    # Langfuse metadata — surfaced in the trace UI for filtering.
    if trace_id or span_name:
        metadata = {}
        if trace_id:
            metadata["trace_id"] = trace_id
        if span_name:
            metadata["span_name"] = span_name
        kwargs["metadata"] = metadata

    try:
        resp = await client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
    except Exception as e:
        logger.error("LLM call failed (model=%s): %s", model, e)
        raise


async def chat_complete_json(
    system_prompt: str,
    user_content: str | dict | list,
    *,
    model: Optional[str] = None,
    temperature: float = 0.1,
    trace_id: Optional[str] = None,
    span_name: Optional[str] = None,
) -> Any:
    """Like chat_complete but parses the response as JSON.

    Falls back to extracting the first {...} or [...] block if JSON mode unsupported.
    """
    raw = await chat_complete(
        system_prompt,
        user_content,
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        trace_id=trace_id,
        span_name=span_name,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _extract_json(raw)


def _extract_json(text: str) -> Any:
    """Best-effort JSON extraction from LLM output."""
    import re

    # Try fenced code block first
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Then first { ... } or [ ... ]
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}...")


async def llm_complete(
    prompt: str,
    *,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
) -> str:
    """Plain text completion (no system message). Used by dedupe escalation."""
    model = model or settings.worker_model
    client = _maybe_langfuse_client() or _get_openai_client()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""
