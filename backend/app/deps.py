"""FastAPI dependencies — DB session, LLM client, etc."""
from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yields a DB session per request."""
    async with async_session_factory() as s:
        try:
            yield s
        finally:
            await s.close()
