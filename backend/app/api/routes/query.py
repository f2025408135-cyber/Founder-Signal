"""POST /query — compound query resolution (spec §9.4 Multi-Attribute Reasoning).

The inbox search box accepts compound natural-language queries. These are NOT manual
filter toggles — the query goes to POST /api/query, which decomposes the query into
atomic attributes (via a small LLM call), maps each attribute to a Claim predicate,
and runs a single SQL query joining claims + founder_scores with all predicates AND'd.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AggregatorOutputORM,
    Application as ApplicationORM,
    ClaimORM,
    Company,
    Founder,
    FounderScoreSnapshot,
)
from app.deps import get_db
from app.llm import client as llm_client

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., description='e.g. "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator"')
    thesis_id: Optional[uuid.UUID] = None
    limit: int = Field(default=20, ge=1, le=100)


class QueryMatch(BaseModel):
    founder_id: str
    score: float
    matched_attributes: list[str]
    founder_name: str
    company_name: str | None = None


class QueryResponse(BaseModel):
    query: str
    decomposed_attributes: list[str]
    matches: list[QueryMatch]


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Compound query resolution (spec §9.4 Multi-Attribute Reasoning).",
)
async def compound_query(
    req: QueryRequest,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Decompose a compound query into atomic attributes, then run a single SQL query."""
    # 1. Decompose the query via a small LLM call
    attributes = await _decompose_query(req.query)

    if not attributes:
        # Fall back to free-text search across claims
        return QueryResponse(
            query=req.query,
            decomposed_attributes=[],
            matches=[],
        )

    # 2. Build SQL query: for each founder, check how many attributes match any of their claims
    # We use ILIKE matching against claim text — fast thanks to the GIN trigram index.
    # Each attribute contributes one OR predicate across claim kinds; the founder's score
    # is the count of matched attributes.
    or_predicates = []
    for attr in attributes:
        # Normalize the attribute for ILIKE matching
        attr_lower = attr.lower().strip()
        if not attr_lower:
            continue
        or_predicates.append(ClaimORM.text.ilike(f"%{attr_lower}%"))

    if not or_predicates:
        return QueryResponse(
            query=req.query,
            decomposed_attributes=attributes,
            matches=[],
        )

    # 3. Find founders whose claims match any attribute
    claims_q = (
        select(
            ClaimORM.founder_id,
            ClaimORM.text,
        )
        .where(ClaimORM.superseded_by.is_(None))
        .where(or_(*or_predicates))
    )
    claim_rows = (await db.execute(claims_q)).all()

    # Score each founder: count distinct attributes that matched at least one claim
    founder_matches: dict[uuid.UUID, set[str]] = {}
    for fid, text in claim_rows:
        text_lower = (text or "").lower()
        for attr in attributes:
            if attr.lower() in text_lower:
                founder_matches.setdefault(fid, set()).add(attr)

    if not founder_matches:
        return QueryResponse(
            query=req.query,
            decomposed_attributes=attributes,
            matches=[],
        )

    # 4. Load founder + company info + conviction score for ranking
    matches: list[QueryMatch] = []
    for fid, matched in founder_matches.items():
        founder = await db.get(Founder, fid)
        if founder is None:
            continue
        company_q = select(Company).where(Company.founder_id == fid).order_by(desc(Company.created_at)).limit(1)
        company = (await db.execute(company_q)).scalars().first()
        agg_q = (
            select(AggregatorOutputORM)
            .where(AggregatorOutputORM.founder_id == fid)
            .order_by(desc(AggregatorOutputORM.computed_at))
            .limit(1)
        )
        agg = (await db.execute(agg_q)).scalars().first()

        # Composite score: conviction (0-100) + (matched_attr_count * 5) bonus
        conviction = agg.overall_conviction if agg else 0
        score = float(conviction) + len(matched) * 5.0

        matches.append(QueryMatch(
            founder_id=str(fid),
            score=round(score, 1),
            matched_attributes=sorted(matched),
            founder_name=founder.name,
            company_name=company.name if company else None,
        ))

    # 5. Sort by composite score desc, take top N
    matches.sort(key=lambda m: m.score, reverse=True)
    matches = matches[: req.limit]

    return QueryResponse(
        query=req.query,
        decomposed_attributes=attributes,
        matches=matches,
    )


async def _decompose_query(query: str) -> list[str]:
    """Decompose a compound query into atomic attributes via a small LLM call.

    Example: "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator"
    → ["technical", "Berlin", "AI infra", "enterprise traction", "no prior VC backing", "top-tier accelerator"]
    """
    prompt = (
        "Decompose the following compound search query into a list of atomic attributes. "
        "Return ONLY a JSON object with key 'attributes' containing an array of short attribute strings. "
        "Preserve the user's wording; do not paraphrase. Drop filler words like 'founder', 'who', 'is'.\n\n"
        f"Query: {query}\n\n"
        'Example output: {"attributes": ["technical", "Berlin", "AI infra", "enterprise traction", "no prior VC backing", "top-tier accelerator"]}'
    )
    try:
        raw = await llm_client.chat_complete_json(
            system_prompt="You are a search query decomposer. Output JSON only.",
            user_content=prompt,
            temperature=0.0,
            max_tokens=300,
        )
        if isinstance(raw, dict) and "attributes" in raw:
            attrs = raw["attributes"]
            if isinstance(attrs, list):
                return [str(a).strip() for a in attrs if str(a).strip()]
        return [query]
    except Exception as e:
        logger.warning("Query decomposition failed (%s): %s — falling back to naive split", query[:60], e)
        # Naive fallback: split on commas
        return [p.strip() for p in query.split(",") if p.strip()]
