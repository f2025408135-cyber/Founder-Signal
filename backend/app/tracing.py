"""Langfuse tracing utilities — wraps LLM client + graph nodes with span tracking.

Per spec §10 C1 + §5.2:
- @observe() decorator on every node function
- langfuse.openai wrapper for LLM calls (auto-traced)
- trace_id written to Application.trace_id for cross-linking
"""
from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from typing import Any, AsyncIterator, Callable, Optional, TypeVar

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def is_langfuse_enabled() -> bool:
    """Whether Langfuse tracing is active."""
    return settings.langfuse_is_configured


def get_langfuse_client():
    """Return the Langfuse client instance (or None if unconfigured)."""
    if not settings.langfuse_is_configured:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as e:
        logger.warning("Failed to construct Langfuse client: %s", e)
        return None


def get_langfuse_openai():
    """Return the langfuse-wrapped OpenAI module (or plain openai if unconfigured).

    Used by app/llm/client.py to wrap the AsyncOpenAI client.
    """
    if not settings.langfuse_is_configured:
        return None
    try:
        from langfuse.openai import openai as langfuse_openai

        return langfuse_openai
    except Exception as e:
        logger.warning("Failed to load langfuse.openai wrapper: %s", e)
        return None


def observe(name: Optional[str] = None):
    """Drop-in replacement for langfuse.observe.

    If Langfuse is configured, delegates to langfuse.observe.
    Otherwise returns a no-op decorator that preserves the function signature.

    Usage:
        from app.tracing import observe

        @observe("ingestion_node")
        async def ingestion_node(state: PipelineState) -> dict:
            ...
    """
    if not settings.langfuse_is_configured:
        # No-op decorator
        def _decorator(func):
            return func
        return _decorator

    try:
        from langfuse import observe as _lf_observe

        return _lf_observe(name=name) if name else _lf_observe()
    except Exception as e:
        logger.warning("Failed to import langfuse.observe: %s — using no-op", e)
        def _decorator(func):
            return func
        return _decorator


def new_trace_id() -> str:
    """Generate a new trace ID (UUID hex, 32 chars)."""
    return uuid.uuid4().hex


@contextmanager
def trace_context(trace_id: str, name: str = "pipeline"):
    """Context manager that starts a Langfuse trace (or no-ops if unconfigured).

    Yields a trace object that can be used to add spans manually.
    """
    if not settings.langfuse_is_configured:
        yield None
        return
    try:
        lf = get_langfuse_client()
        if lf is None:
            yield None
            return
        trace = lf.trace(id=trace_id, name=name)
        yield trace
    except Exception as e:
        logger.warning("trace_context failed: %s — continuing without trace", e)
        yield None


async def flush_langfuse() -> None:
    """Flush pending Langfuse events. Call at the end of a pipeline run."""
    if not settings.langfuse_is_configured:
        return
    try:
        lf = get_langfuse_client()
        if lf is not None:
            await _async_flush(lf)
    except Exception as e:
        logger.debug("Langfuse flush failed: %s", e)


async def _async_flush(lf) -> None:
    """Langfuse flush — handles both sync and async clients."""
    flush = getattr(lf, "flush", None)
    if flush is None:
        return
    import asyncio
    if asyncio.iscoroutinefunction(flush):
        await flush()
    else:
        # sync flush — run in thread to avoid blocking
        await asyncio.to_thread(flush)
