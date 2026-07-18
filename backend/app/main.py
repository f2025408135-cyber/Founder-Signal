"""FastAPI app factory + lifespan.

Minimal for Tier A — full route wiring in Tier B B8.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown hooks."""
    logger.info("VC Brain backend starting (env=%s)", settings.app_env)
    # Pre-warm the embeddings model in a background thread
    try:
        from app.utils.embeddings import embed_text

        await embed_text("warmup")
    except Exception as e:
        logger.warning("Embedding warmup failed (will retry lazily): %s", e)
    yield
    logger.info("VC Brain backend shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="VC Brain",
        description="Agentic investment screening OS",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow the Vite dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "env": settings.app_env}

    # API routes — wired in Tier B
    try:
        from app.api.router import router as api_router

        app.include_router(api_router, prefix="/api")
    except ImportError:
        logger.warning("API router not yet available — Tier B will add it")

    return app


app = create_app()
