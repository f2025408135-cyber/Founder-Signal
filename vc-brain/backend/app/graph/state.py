"""Shared pipeline state — TypedDict with custom reducers for parallel writes.

Per spec §5.1:
- claims and validator_outputs use append_list reducer so parallel nodes can
  each contribute without overwriting each other.
- Single-writer fields (founder_output, market_output, etc.) have no reducer.
"""
from __future__ import annotations

from typing import Annotated, Any, Optional, TypedDict
from uuid import UUID

from app.schemas.agent_outputs import (
    AggregatorOutput,
    FounderAgentOutput,
    IdeaVsMarketAgentOutput,
    MarketAgentOutput,
    ValidatorAgentOutput,
)
from app.schemas.claim import Claim
from app.schemas.founder_score import FounderScore
from app.schemas.thesis import Thesis


def append_list(left: list | None, right: list | None) -> list:
    """Reducer that concatenates two lists (None → [])."""
    return (left or []) + (right or [])


def merge_dicts(left: dict | None, right: dict | None) -> dict:
    """Reducer that merges two dicts (right wins on key collision)."""
    out = dict(left or {})
    out.update(right or {})
    return out


class PipelineState(TypedDict, total=False):
    """LangGraph state — passed between nodes.

    `total=False` because not all keys are populated at every node.
    """

    # ---- inputs (set by API handler before invoke) ----
    founder_id: UUID
    company_id: UUID
    application_id: Optional[UUID]
    thesis: Thesis
    raw_inputs: list[dict]  # pre-fetched source payloads (GitHub/arxiv/HN/PH/deck)

    # ---- memory (read from Postgres at entry) ----
    prior_founder_score: Optional[FounderScore]
    market_descriptors: list[str]  # expanded from thesis.sectors

    # ---- shared concurrent-write state ----
    # claims and validator_outputs use the append_list reducer so parallel nodes
    # can each contribute without overwriting each other.
    claims: Annotated[list[Claim], append_list]
    validator_outputs: Annotated[list[ValidatorAgentOutput], append_list]
    errors: Annotated[list[str], append_list]

    # ---- per-agent outputs (single writer each) ----
    founder_output: Optional[FounderAgentOutput]
    market_output: Optional[MarketAgentOutput]
    idea_vs_market_output: Optional[IdeaVsMarketAgentOutput]

    # ---- precomputed inputs to aggregator ----
    thesis_fit_score: float  # written by thesis_fit node
    market_fit_similarity: float  # written by thesis_fit node (used by founder node)
    external_evidence: dict  # written by fetch_external_evidence node

    # ---- final ----
    aggregator_output: Optional[AggregatorOutput]

    # ---- tracing ----
    trace_id: Optional[str]
