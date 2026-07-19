"""Async engine + sessionmaker."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Create the async engine once. Pool pre-ping keeps connections fresh
# across the long-running FastAPI process.
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Sessionmaker bound to the engine. Use `async_session()` context manager
# everywhere — never construct sessions directly.
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def async_session() -> AsyncIterator[AsyncSession]:
    """Context manager that yields an AsyncSession and auto-commits on exit.

    Usage:
        async with async_session() as s:
            s.add(obj)
            await s.commit()
    """
    async with async_session_factory() as s:
        try:
            yield s
            await s.commit()
        except Exception:
            await s.rollback()
            raise


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — yields a session per request."""
    async with async_session_factory() as s:
        try:
            yield s
        finally:
            await s.close()
