"""LangGraph pipeline wiring — compile() entrypoint.

Per spec §5.3:
- 8 nodes: ingestion → (fetch_external_evidence || thesis_fit) → validator →
  (founder || market) → idea_vs_market (after market) → aggregator
- AsyncPostgresSaver checkpointer with thread_id = founder_id

Per spec §10 A6 + B7: production paths MUST use the checkpointer so that
interrupted pipelines can resume and `langgraph_checkpoints` rows are written.
"""
from __future__ import annotations

import logging
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph

from app.config import settings
from app.graph.nodes import (
    aggregator_node,
    fetch_external_evidence_node,
    founder_node,
    idea_vs_market_node,
    ingestion_node,
    market_node,
    thesis_fit_node,
    validator_node,
)
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def build_pipeline(checkpointer: Optional[AsyncPostgresSaver] = None) -> "CompiledGraph":
    """Build the LangGraph pipeline. If no checkpointer is provided, runs without
    checkpointing (used in tests).
    """
    g = StateGraph(PipelineState)

    g.add_node("ingestion", ingestion_node)
    g.add_node("fetch_external_evidence", fetch_external_evidence_node)
    g.add_node("thesis_fit", thesis_fit_node)
    g.add_node("validator", validator_node)
    g.add_node("founder", founder_node)
    g.add_node("market", market_node)
    g.add_node("idea_vs_market", idea_vs_market_node)
    g.add_node("aggregator", aggregator_node)

    # Entry: ingestion only
    g.set_entry_point("ingestion")

    # After ingestion: parallel fan-out of (fetch_external_evidence, thesis_fit)
    g.add_edge("ingestion", "fetch_external_evidence")
    g.add_edge("ingestion", "thesis_fit")

    # Evidence fetch must complete before validator
    g.add_edge("fetch_external_evidence", "validator")

    # Validator must complete before the three scoring agents — they read flags
    g.add_edge("validator", "founder")
    g.add_edge("validator", "market")

    # NOTE: idea_vs_market depends on market_output.reasoning, so it runs AFTER market
    g.add_edge("market", "idea_vs_market")

    # thesis_fit is parallel and feeds aggregator directly
    g.add_edge("thesis_fit", "aggregator")

    # founder + idea_vs_market fan-in to aggregator
    g.add_edge("founder", "aggregator")
    g.add_edge("idea_vs_market", "aggregator")

    # aggregator is the synthesizer — terminal node
    g.add_edge("aggregator", END)

    if checkpointer is not None:
        return g.compile(checkpointer=checkpointer)
    return g.compile()


async def build_pipeline_with_postgres_saver():
    """Build the pipeline with AsyncPostgresSaver checkpointer.

    Per spec §10 A6: `pipeline.ainvoke({...})` runs end-to-end on a fixture founder
    and writes a checkpoint row to Postgres `langgraph_checkpoints` table.

    Per spec §8 + B7: thread_id = founder_id so LangGraph resumes from checkpoint
    if interrupted.
    """
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.database_sync_url)
    await checkpointer.setup()  # creates langgraph_checkpoints + langgraph_writes tables
    return build_pipeline(checkpointer=checkpointer)


def get_thread_config(founder_id) -> dict:
    """Return the LangGraph config dict with thread_id = founder_id.

    Per spec §8: "thread_id = founder_id so LangGraph resumes from checkpoint
    if interrupted."
    """
    return {"configurable": {"thread_id": str(founder_id)}}


# Convenience singleton — built lazily on first use
_pipeline_singleton = None


async def get_pipeline():
    """Returns the singleton pipeline instance, building it on first call.

    Per spec §10 A6 + B7: production paths MUST use the checkpointer.
    Falls back to no-checkpointer if Postgres is unavailable (test env).
    """
    global _pipeline_singleton
    if _pipeline_singleton is None:
        try:
            _pipeline_singleton = await build_pipeline_with_postgres_saver()
            logger.info("Pipeline built with AsyncPostgresSaver checkpointer")
        except Exception as e:
            logger.warning(
                "Failed to build pipeline with Postgres checkpointer (%s) — "
                "falling back to no-checkpointer (interrupted pipelines cannot resume)",
                e,
            )
            _pipeline_singleton = build_pipeline(checkpointer=None)
    return _pipeline_singleton
