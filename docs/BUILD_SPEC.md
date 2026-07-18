# VC Brain — Build Specification

> **Handoff target:** autonomous coding agent. Every decision below is resolved — no placeholders, no "choose one of the following." If a coding agent encounters ambiguity, treat it as a bug in this spec, not an invitation to ask the human.

---

## 0. Verification Audit — 2026-07-19

Every version pin, API endpoint, rate limit, and third-party repo referenced in this spec was verified against primary sources (official docs, PyPI, GitHub releases, OpenAI help center, vendor blogs) during a web-research pass completed on **19 July 2026**. Findings below; all updates are reflected in the body of the spec.

| Item | Pre-audit claim | Verified value (2026-07-19) | Source | Action |
|---|---|---|---|---|
| LangGraph | "0.2+" | **1.2.8** (released Jul 9, 2026 on PyPI) | pypi.org/project/langgraph, langchain.com changelog | Updated to `LangGraph 1.2+` |
| FastAPI | "0.115+" | **0.139.2** (released Jul 16, 2026 on PyPI) | pypi.org/project/fastapi, fastapi.tiangolo.com/release-notes | Updated to `FastAPI 0.139+` |
| Python | "3.11" | **3.13.14** stable (released Jun 10, 2026); 3.14 still in development | python.org/downloads/source | Updated to `Python 3.13` |
| React | "18" | **React 19 stable** (shadcn/ui components updated for React 19) | ui.shadcn.com/docs/tailwind-v4 | Updated to `React 19` |
| Vite | "5" | **Vite 7.0** (released Jul 15, 2026 — Rolldown/Oxc pipeline) | vite.dev/blog/announcing-vite7, sitepoint.com Vite 7 migration | Updated to `Vite 7` |
| Tailwind CSS | "3" | **Tailwind CSS v4** (shadcn/ui components updated) | ui.shadcn.com/docs/tailwind-v4 | Updated to `Tailwind 4` |
| TanStack Query | "5" | **v5 still current** in 2026 frontend stacks | usedatabrain.com, thetshaped.dev | No change |
| PostgreSQL | "16" | **PostgreSQL 18** (pgvector 0.8.x for PG 18.x available Jul 16, 2026) | hub.docker.com hardened-images catalog, techcommunity.microsoft.com Postgres 2026 | Updated to `PostgreSQL 18` |
| pgvector | unspecified | **0.8.0–0.8.2** (0.8.2 stabilizes parallel HNSW builds) | postgresql.org/about/news/pgvector-080-released-2952, github.com/pgvector/pgvector | Pinned to `pgvector 0.8.x` |
| Langfuse | "v3" | **v3 still current** (active releases through Jul 18, 2026) | langfuse.com/changelog, github.com/langfuse/langfuse/releases | No change |
| OpenAI models | `gpt-4o-mini` + `gpt-4o` | **GPT-5.6 Sol** ($5/$30 per 1M — flagship, released Jul 9, 2026, knowledge cutoff Feb 2026); **GPT-5.6 Terra** ($2.50/$15 per 1M — 1M context); **GPT-5.6 Luna** ($1/$6 per 1M — fast, cost-efficient). **GPT-5.1 was retired Mar 11, 2026. GPT-5.5 was released Apr 24, 2026 but is now superseded by 5.6. There is NO "mini" variant for GPT-5.6 — Luna is the cheap tier.** | openai.com/index/gpt-5-6, openrouter.ai/openai/gpt-5.6-terra, finout.io, eesel.ai/blog/gpt-5-6-pricing, help.openai.com model release notes | Updated to `GPT-5.6 Luna` for worker agents, `GPT-5.6 Sol` for Validator/Aggregator |
| Sentence-BERT model | `paraphrase-multilingual-MiniLM-L12-v2` | **`all-MiniLM-L6-v2`** is the most-recommended sentence-transformers model in 2026 (384-dim, 5x faster than mpnet-base-v2, top-1 on Hugging Face popularity lists) | huggingface.co/sentence-transformers/all-MiniLM-L6-v2, sbert.net docs, bentoml.com 2026 guide | Updated to `all-MiniLM-L6-v2` |
| GitHub REST API rate limit | 5,000/hr auth, 60/hr unauth | **Confirmed current** | docs.github.com/en/rest/using-the-rest-api/rate-limits | No change |
| GitHub GraphQL API rate limit | 5,000 points/hr | **Confirmed current** | docs.github.com/en/graphql/overview/rate-limits-and-query-limits | No change |
| arXiv API rate limit | 1 req / 3 sec | **Confirmed current** — Terms of Use explicitly state "no more than one request every three seconds" | info.arxiv.org/help/api/tou.html | No change |
| Hacker News API | "undocumented limit" | **Confirmed** — neither Firebase nor Algolia specifies a hard rate limit for read-only access | agent37.com/blog/hacker-news-api, dev.to agenthustler 2026 HN scraping | No change |
| Product Hunt API v2 | "OAuth PAT, dynamic caps" | **More specific:** ~900 requests per 15 minutes, complexity limit of 1000 per query, GraphQL-based, OAuth Bearer token | api.producthunt.com/v2/docs/rate_limits/headers, lobehub.com producthunt skill | Updated §6.4 with specific limits |
| Pydantic AI V2 | "V2" | **V2 shipped stable Jun 23, 2026** (harness-first redesign) | institutepm.com 2026 agentic framework update, alicelabs.ai 2026 framework comparison | No change (V2 confirmed current) |
| Microsoft Agent Framework (MAF) | "1.0" | **MAF 1.0 GA on Apr 2, 2026** (AutoGen + Semantic Kernel convergence) | devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce | No change (1.0 confirmed) |
| CrewAI | "1.14" | Still listed as a leading 2026 framework; specific version not re-pinned in 2026 sources | langchain.com/resources/ai-agent-frameworks, agentmail.to/blog/best-ai-agent-frameworks-2026 | No change |
| Mastra | "1.0" | Still listed as a leading 2026 framework | mastra.ai/articles/ai-agent-framework | No change |
| AgentOracle x402 Research Skill | referenced as a verification pattern | **Confirmed real and active** — per-claim verification via 4 independent sources (Sonar, scanning, Gemma 4), $0.01 per claim, github.com/TKCollective/x402-research-skill, agentoracle.co | github.com/TKCollective/x402-research-skill, agentoracle.co | No change (referenced pattern still valid) |
| KeeLead | referenced as founder-sourcing engine | **GitHub org exists** (github.com/KEELEAD) but has no public repos as of Jul 2026 — keep as architectural reference, do not depend on running their code | github.com/KEELEAD | No change to reference; flagged for implementer |
| GitTalent | referenced as technical-scoring reference | **Confirmed active** at gittalent.dev (recruit developers by GitHub work) | gittalent.dev | No change |
| Splink / Dedupe / RapidFuzz | referenced as dedupe options | **All confirmed still maintained in 2026**; RapidFuzz remains the right default for hackathon volumes | moj-analytical-services.github.io/splink, github.com/moj-analytical-services/splink, tilores.io entity-resolution libraries review | No change |
| langchain-vc-memo-agent pattern | referenced as Perplexity-style memo pattern | Still the canonical "parallel research graph + tool-less synthesizer" pattern in 2026 | (original brief reference, not re-verified) | No change |

**Net effect on the spec:** every version pin in §1 has been updated to the current stable release as of 19 July 2026. The model choice in §5.2 (node functions) and §6 (API integrations, Product Hunt section) has been updated. All API endpoints and rate limits in §6 remain valid. Schemas, agent prompts, dedupe logic, re-scoring triggers, UX spec, build order, and non-goals are unchanged — they were framework-version-agnostic by design.

---

## 1. Tech Stack Decision Log

| Layer | Final choice | One-sentence justification |
|---|---|---|
| Orchestration framework | **LangGraph 1.2+** (latest stable: 1.2.8, released Jul 9, 2026) | Native `StateGraph` with `Annotated[list, add]` custom reducers lets three independent scoring agents (Founder, Market, Idea-vs-Market) write to shared state in true parallel, and `AsyncPostgresSaver` gives us checkpoint/resume for the re-scoring trigger logic. CrewAI is too declarative for fine-grained parallel writes; Mastra is TS-only; Pydantic AI V2 (stable Jun 23, 2026) lacks reducers; MAF 1.0 (GA Apr 2, 2026) is enterprise overhead we don't need in 24h. |
| Backend | **Python 3.13 + FastAPI 0.139+** (latest stable: 0.139.2, released Jul 16, 2026) | Same language as LangGraph — zero serialization boundary between graph nodes and HTTP handlers, async-native for parallel agent I/O. Python 3.13.14 is the current stable release (3.14 still in development as of Jul 2026). |
| Frontend | **React 19 + Vite 7 + Tailwind CSS 4 + shadcn/ui (Tailwind v4 branch) + TanStack Query 5** | shadcn/ui is fully updated for React 19 + Tailwind v4 (removed forwardRefs, added `data-slot` attributes); Vite 7 ships the Rolldown/Oxc Rust-based pipeline for sub-second HMR; TanStack Query 5 handles memo cache invalidation against the re-score trigger logic. Create React App is officially deprecated since Feb 2025 — do not use it. |
| Database | **PostgreSQL 18 + pgvector 0.8.x** | Relational core for Claim/FounderScore/Application tables; pgvector 0.8.x (0.8.2 stabilizes parallel HNSW builds) stores 384-dim Sentence-BERT embeddings for founder-market cosine similarity. SQLite was rejected — vector search + concurrent agent writes exceed its happy path. |
| Observability | **Langfuse v3 (self-hosted, Docker Compose)** | MIT-licensed, step-level tracing maps 1:1 to LangGraph nodes, gives per-claim confidence dashboards out of the box with no vendor lock-in for the demo. v3 is still the current major version with active releases through Jul 18, 2026. |
| LLM provider | **OpenAI GPT-5.6 series**: `gpt-5.6-luna` for the three parallel scoring agents ($1/$6 per 1M tokens — fast, cost-efficient); `gpt-5.6-sol` for Validator + Aggregator ($5/$30 per 1M tokens — frontier reasoning, knowledge cutoff Feb 2026). Optional middle tier: `gpt-5.6-terra` ($2.50/$15 per 1M, 1M context) if Validator needs longer context for cross-claim contradiction detection. | Cost/latency split — three parallel worker agents run on Luna to fit the 24h budget; the synthesizer and verifier need Sol's reasoning depth for memo quality and contradiction detection. **GPT-5.1 was retired Mar 11, 2026. GPT-5.5 (Apr 24, 2026) is superseded by 5.6. There is NO "mini" variant for GPT-5.6 — Luna is the cheap tier. Do NOT use `gpt-4o-mini` or `gpt-4o` — they are deprecated.** |
| Embeddings | **`sentence-transformers/all-MiniLM-L6-v2`** via local ONNX runtime | 384-dim, CPU-runnable, no per-call cost, top-1 most-popular sentence-transformers model on Hugging Face as of 2026, 5x faster than `all-mpnet-base-v2` with 90–95% of the quality; powers founder-market cosine similarity and dedupe escalation. |
| Deduplication | **RapidFuzz `WRatio` first-pass (threshold ≥90 auto-merge, 80–89 LLM escalate)** | Python-native, sub-millisecond on the volumes a hackathon demo produces; Splink/Dedupe are overkill below ~10k claims and add infra we don't need for the demo. |
| Traceability | **Langfuse trace IDs injected into every Claim's `source.retrieved_by` field** | Agentic traceability stretch goal (#1) becomes a query problem, not an instrumentation problem. |

---

## 2. Repository Structure

```
vc-brain/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 0001_init_claims_founders.py
│   │       ├── 0002_thesis_applications_signals.py
│   │       └── 0003_pgvector_embeddings.py
│   ├── app/
│   │   ├── main.py                      # FastAPI app factory + lifespan
│   │   ├── config.py                    # pydantic-settings: env-driven
│   │   ├── deps.py                      # DB session, LLM client deps
│   │   ├── db/
│   │   │   ├── base.py                  # SQLAlchemy declarative base
│   │   │   ├── session.py               # async engine + sessionmaker
│   │   │   └── models.py                # ORM models mirroring Pydantic schemas
│   │   ├── schemas/                     # Pydantic v2 models (API contract)
│   │   │   ├── claim.py
│   │   │   ├── founder_score.py
│   │   │   ├── thesis.py
│   │   │   ├── application.py
│   │   │   └── agent_outputs.py
│   │   ├── agents/
│   │   │   ├── prompts/                 # system prompts, one per agent
│   │   │   │   ├── ingestion.txt
│   │   │   │   ├── founder.txt
│   │   │   │   ├── market.txt
│   │   │   │   ├── idea_vs_market.txt
│   │   │   │   ├── validator.txt
│   │   │   │   └── aggregator.txt
│   │   │   ├── ingestion.py
│   │   │   ├── founder.py
│   │   │   ├── market.py
│   │   │   ├── idea_vs_market.py
│   │   │   ├── validator.py
│   │   │   └── aggregator.py
│   │   ├── graph/                       # LangGraph wiring
│   │   │   ├── state.py                 # PipelineState TypedDict + reducers
│   │   │   ├── nodes.py                 # node functions, each wraps one agent
│   │   │   ├── reducers.py              # append_list, merge_dicts
│   │   │   └── pipeline.py              # compile() entrypoint
│   │   ├── ingestion/                   # external API clients
│   │   │   ├── github.py
│   │   │   ├── arxiv.py
│   │   │   ├── hackernews.py
│   │   │   ├── producthunt.py
│   │   │   ├── dedupe.py                # RapidFuzz + LLM escalation
│   │   │   └── website.py               # fetch only founder-provided URLs
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── routes/
│   │   │       ├── applications.py      # POST /applications, GET /applications/inbox
│   │   │       ├── founders.py          # GET /founders/{id}/card, /founders/{id}/memo
│   │   │       ├── thesis.py            # GET/POST /thesis
│   │   │       ├── outbound.py          # POST /outbound/scan, GET /outbound/queue
│   │   │       └── traces.py            # GET /traces/{run_id} (Langfuse proxy)
│   │   ├── llm/
│   │   │   └── client.py                # OpenAI + Langfuse wrapper
│   │   ├── utils/
│   │   │   ├── embeddings.py            # Sentence-BERT singleton
│   │   │   ├── ratelimit.py             # TokenBucket impl
│   │   │   └── hashing.py               # sha256 raw_payload_hash
│   │   └── triggers/
│   │       └── rescore.py               # §8 trigger logic
│   └── tests/
│       ├── conftest.py                  # fixtures: cold-start founder, verified-founder, etc.
│       ├── test_schemas.py
│       ├── test_dedupe.py
│       ├── test_agents.py               # one test per agent's acceptance criteria
│       ├── test_pipeline.py             # end-to-end on fixture
│       └── test_triggers.py             # §8 cache-hit vs re-score
├── frontend/
│   ├── package.json
│   ├── vite.config.ts                      # Vite 7 config (Rolldown/Oxc pipeline)
│   ├── tailwind.config.ts                  # Tailwind v4 config (CSS-first, @theme directive)
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── routes.tsx                      # react-router v7 routes
│       ├── lib/
│       │   ├── api.ts                      # TanStack Query 5 + fetch wrapper
│       │   └── utils.ts                    # cn(), formatting
│       ├── components/
│       │   ├── ui/                         # shadcn primitives (React 19 + Tailwind v4 branch — uses data-slot, no forwardRef)
│       │   ├── FounderCard.tsx
│       │   ├── MemoView.tsx
│       │   ├── EvidenceChip.tsx
│       │   ├── SourceDrawer.tsx
│       │   ├── ThesisEditor.tsx
│       │   ├── PipelineTrace.tsx
│       │   └── ColdStartBanner.tsx
│       └── pages/
│           ├── InboxPage.tsx
│           ├── FounderDetailPage.tsx
│           ├── ThesisPage.tsx
│           └── OutboundPage.tsx
├── infra/
│   ├── docker-compose.yml                  # postgres:18, pgvector/pgvector:0.8-pg18, langfuse, backend, frontend
│   ├── langfuse.env.example
│   └── postgres-init/
│       └── 001-extensions.sql              # CREATE EXTENSION vector;  (pgvector 0.8.x ships with PG 18 image)
├── scripts/
│   ├── seed_thesis.py                  # default Maschmeyer Group thesis
│   ├── seed_fixtures.py                # cold-start founder, verified founder, contradicted founder
│   ├── run_outbound_scan.py            # §10 C5 hourly cron entrypoint
│   └── backfill_embeddings.py          # one-shot for existing claims
├── docs/
│   └── BUILD_SPEC.md                   # this file
└── README.md
```

---

## 3. Data Schemas

All schemas are **Pydantic v2** models. They are the canonical contract — SQLAlchemy ORM models in `app/db/models.py` mirror them 1:1. Every field below is required unless explicitly marked `Optional`.

### 3.1 Claim record

```python
# backend/app/schemas/claim.py
from datetime import datetime
from enum import Enum
from typing import Optional, Literal
import uuid
from pydantic import BaseModel, Field

class ClaimKind(str, Enum):
    FOUNDER_BACKGROUND = "founder_background"
    FOUNDER_NETWORK = "founder_network"
    TECHNICAL_DEPTH = "technical_depth"
    MARKET_SIZE = "market_size"
    MARKET_TREND = "market_trend"
    TRACTION = "traction"
    PRODUCT = "product"
    COMPETITIVE = "competitive"
    FINANCIAL = "financial"
    TEAM = "team"
    COLD_START_INFERRED = "cold_start_inferred"   # mandatory emission when no external signal exists

class SourceKind(str, Enum):
    DECK = "deck"
    APPLICATION_FORM = "application_form"
    GITHUB = "github"
    ARXIV = "arxiv"
    HACKERNEWS = "hackernews"
    PRODUCTHUNT = "producthunt"
    INTERVIEW = "interview"
    ACCELERATOR_COHORT = "accelerator_cohort"
    COMPANY_WEBSITE = "company_website"            # only URLs the founder explicitly provided
    FOUNDER_BIO = "founder_bio"                    # self-reported, pasted by founder
    EXTERNAL_DB = "external_db"                    # Crunchbase API mock for demo

class Source(BaseModel):
    kind: SourceKind
    ref: str                                       # URL, "deck#slide=4", arxiv id, "owner/repo"
    ingested_at: datetime
    raw_payload_hash: str                          # sha256 hex of raw payload — dedupe + re-verification key
    retrieved_by: str                              # agent name + Langfuse span id, e.g. "github.fetch_github_signals@trace_abc/span_123"

class ClaimFlag(BaseModel):
    flag: Literal["verified", "unverifiable", "contradicted", "not_disclosed", "low_evidence", "cold_start_inferred"]
    set_by: str                                    # validator run id (Langfuse trace id)
    set_at: datetime
    reason: str
    counter_evidence_ref: Optional[str] = None     # source.ref of contradicting/confirming evidence

class Claim(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    founder_id: uuid.UUID
    company_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    kind: ClaimKind
    text: str                                      # single declarative sentence — enforced by Ingestion Agent
    source: Source
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)   # set by Validator, never by other agents
    flags: list[ClaimFlag] = Field(default_factory=list)
    embedding: Optional[list[float]] = None        # 384-dim, for similarity + dedupe escalation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    superseded_by: Optional[uuid.UUID] = None      # set when a newer claim contradicts + replaces this one — never hard-delete
```

### 3.2 Founder Score record

```python
# backend/app/schemas/founder_score.py
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid
from pydantic import BaseModel, Field

class Trend(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"

class ScoreSnapshot(BaseModel):
    score: float = Field(ge=0.0, le=100.0)
    confidence_band: tuple[float, float]            # (low, high); wide for cold-start — Founder Agent rule
    trend: Trend
    computed_at: datetime
    trigger: str                                    # "application" | "signal_threshold" | "manual" | "outbound_scan"
    evidence_claim_ids: list[uuid.UUID]
    component_scores: dict[str, float]              # {"technical": 78, "market_fit": 62, "network": 0, "momentum": 45}
    cold_start: bool                                # explicit flag — drives the UX banner

class ApplicationRef(BaseModel):
    application_id: uuid.UUID
    received_at: datetime
    outcome: Optional[str] = None                   # "pending" | "screened" | "invested" | "passed"

class FounderScore(BaseModel):
    founder_id: uuid.UUID
    # CRITICAL: score_history is APPEND-ONLY. It NEVER resets across applications, cohorts, or time.
    # This is the persistent-memory requirement from the brief.
    score_history: list[ScoreSnapshot] = Field(default_factory=list)
    current_score: Optional[ScoreSnapshot] = None
    trend: Trend = Trend.INSUFFICIENT_DATA
    applications: list[ApplicationRef] = Field(default_factory=list)
    first_seen_at: datetime
    last_updated_at: datetime
```

### 3.3 Thesis Engine config

```python
# backend/app/schemas/thesis.py
from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field

class RiskAppetite(BaseModel):
    max_founder_age_years: int = 3                  # years since incorporation
    accepts_no_prior_funding: bool = True
    accepts_no_github: bool = True
    accepts_cold_start: bool = True                 # MUST default True per brief
    min_conviction_score: float = 60.0              # 0-100
    allow_neutral_market: bool = True               # if False, only bullish markets are screenable

class Thesis(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str                                       # e.g. "Maschmeyer Group — AI Infra & DevTools"
    sectors: list[str]                              # e.g. ["AI infra", "DevTools", "Climate", "Robotics"]
    stage: list[str]                                # e.g. ["pre-seed", "seed"]
    geography: list[str]                            # ISO-3166 alpha-2, e.g. ["DE", "US", "PK", "SG"]
    check_size_usd: int                             # 100_000 for this hackathon
    ownership_target_pct: float                     # e.g. 7.5
    risk_appetite: RiskAppetite
    created_at: datetime
    updated_at: datetime
    active: bool = True                             # MVP: only one active thesis at a time
```

### 3.4 Agent output schemas

```python
# backend/app/schemas/agent_outputs.py
from datetime import datetime
from typing import Optional, Literal
import uuid
from pydantic import BaseModel, Field

# ---------- Founder Agent ----------
class FounderAgentOutput(BaseModel):
    founder_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    technical_score: float = Field(ge=0, le=100)
    market_fit_score: float = Field(ge=0, le=100)
    network_score: float = Field(ge=0, le=100)
    momentum_score: float = Field(ge=0, le=100)
    cold_start: bool                                # explicit; drives UX banner + Aggregator callout
    confidence_band: tuple[float, float]            # wide for cold-start (rule: width >= 50)
    supporting_claim_ids: list[uuid.UUID]
    reasoning: str                                  # 3-5 sentences, plain English
    flags: list[str]                                # e.g. ["no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"]
    trend: Literal["improving", "declining", "stable", "insufficient_data"]
    computed_at: datetime

# ---------- Market Agent ----------
class MarketAgentOutput(BaseModel):
    company_id: uuid.UUID
    market_score: Literal["bullish", "neutral", "bear"]   # categorical — NEVER averaged
    market_size_estimate_usd: Optional[float] = None
    growth_rate_pct: Optional[float] = None
    confidence_band: tuple[float, float]
    supporting_claim_ids: list[uuid.UUID]
    reasoning: str
    contradictions: list[str] = []                  # textual list of "Claim A vs Claim B" pairs
    computed_at: datetime

# ---------- Idea-vs-Market Agent ----------
class IdeaVsMarketAgentOutput(BaseModel):
    company_id: uuid.UUID
    fit_score: float = Field(ge=0, le=100)          # how well the idea serves the identified market
    defensibility_score: float = Field(ge=0, le=100)
    differentiation: str                            # 2-4 sentences naming 2 closest competitors + the wedge
    confidence_band: tuple[float, float]
    supporting_claim_ids: list[uuid.UUID]
    reasoning: str
    computed_at: datetime

# ---------- Validator Agent ----------
class ValidatorAgentOutput(BaseModel):
    claim_id: uuid.UUID
    status: Literal["verified", "unverifiable", "contradicted", "not_disclosed"]
    confidence: float = Field(ge=0, le=1)
    counter_evidence: Optional[str] = None          # quoted snippet from contradicting/confirming source
    counter_evidence_source: Optional[str] = None   # source.ref of that evidence
    notes: str

# ---------- Aggregator ----------
class AggregatorOutput(BaseModel):
    application_id: Optional[uuid.UUID] = None
    founder_id: uuid.UUID
    company_id: uuid.UUID
    overall_recommendation: Literal["pass", "deep_dive", "fast_pass", "reject"]
    overall_conviction: float = Field(ge=0, le=100)
    axes: dict[str, float]                          # {"founder": 72, "market": 65, "idea_vs_market": 80} — NEVER averaged
    axes_trends: dict[str, str]                     # {"founder": "improving", "market": "stable", ...}
    thesis_fit_score: float = Field(ge=0, le=100)
    evidence_coverage: float = Field(ge=0, le=1)    # verified_claims / total_claims
    open_contradictions: list[str]
    missing_required_sections: list[str]            # from Appendix 1 required list
    missing_optional_sections: list[str]            # flagged, never fabricated
    memo_markdown: str                              # full memo, every fact cited [^claim_id]
    next_actions: list[str]
    computed_at: datetime
```

### 3.5 Application + signal schemas (supporting)

```python
# backend/app/schemas/application.py
from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, HttpUrl

class ApplicationCreate(BaseModel):
    founder_name: str
    founder_email: str
    founder_bio_text: str                           # founder-pasted, NOT scraped from LinkedIn
    company_name: str
    company_website_url: Optional[HttpUrl] = None   # founder-provided only; never bulk-crawled
    deck_url: Optional[HttpUrl] = None              # PDF or public link
    github_repo_slugs: list[str] = Field(default_factory=list)
    accelerator: Optional[str] = None
    hq_country: str                                 # ISO-3166 alpha-2
    sector_self_reported: str

class Application(BaseModel):
    id: uuid.UUID
    founder_id: uuid.UUID
    company_id: uuid.UUID
    received_at: datetime
    status: str = "pending"                         # "pending" | "screened" | "fast_pass" | "deep_dive" | "passed" | "rejected"
    raw_payload: dict                               # the ApplicationCreate payload, preserved verbatim
    aggregator_output_id: Optional[uuid.UUID] = None

class FounderSignal(BaseModel):
    id: uuid.UUID
    founder_id: uuid.UUID
    signal_type: str                                # "new_github_commit" | "new_arxiv_paper" | "new_ph_launch" | "new_hn_post_above_threshold"
    detected_at: datetime
    conviction_delta: float                         # estimated score delta if re-run
    payload_hash: str
```

---

## 4. Agent Specifications

Each agent below has: (a) full system prompt text — paste verbatim into `ChatOpenAI(...).invoke([{"role":"system","content":PROMPT},{"role":"user","content":json.dumps(input)}])`; (b) input schema; (c) output schema; (d) rule set. Schemas live in §3.4; this section references them by name.

### 4.1 Ingestion Agent

**System prompt:**

```
You are the Ingestion Agent for the VC Brain operating system. Your job is to take raw heterogeneous inputs (application deck PDFs, founder-pasted bios, GitHub API responses, arXiv search results, Hacker News Algolia hits, Product Hunt GraphQL results, accelerator cohort exports, founder-provided company-website HTML) and emit a flat list of atomic Claim records that downstream agents can reason over.

ATOMIC CLAIM RULES:
1. Each claim must express exactly ONE verifiable proposition. "Founder has 8 years of AI infra experience and previously sold a YC company" is TWO claims — split it.
2. Never invent data. If the source does not contain a fact, do not emit a claim for it.
3. Preserve source provenance verbatim: every claim must reference the exact source.kind, source.ref (URL, slide number like "deck#slide=4", arxiv id, "owner/repo"), and the raw_payload_hash provided in your input.
4. If a fact appears in multiple sources, emit one Claim per source — the Validator + dedupe layer will reconcile them later. Do NOT pre-merge.
5. Classify each claim with one ClaimKind from: founder_background, founder_network, technical_depth, market_size, market_trend, traction, product, competitive, financial, team.
6. COLD-START RULE: If the founder provided NO GitHub, NO arxiv, NO Product Hunt launch, NO accelerator cohort, and NO externally verifiable network signals — you MUST still emit at least one claim of kind="cold_start_inferred" derived ONLY from deck content and the application form. A silent empty output is a critical bug and will break downstream agents.
7. Set initial confidence=0.5 for every claim. The Validator will overwrite this. Do not pre-set confidence based on source quality.
8. Text must be a single declarative sentence. No compound clauses joined by "and" / "but" / "while". No bullet lists. No questions. No hedging language ("may", "could", "might").
9. Deck slide references must use the format "deck#slide=N" where N is the 1-indexed slide number. If the deck is a PDF without page labels, treat page number as slide number.

OUTPUT FORMAT: a JSON array of objects conforming to schemas.Claim (Pydantic v2). Emit at least 1 claim, even for cold-start cases. If you cannot parse the input, emit a single claim of kind="cold_start_inferred" with text="Ingestion failed: <reason>" and source.kind="application_form".

DO NOT call any tools. DO NOT search the web. You only transform the inputs you are given.
```

**Input schema:**

```python
class IngestionAgentInput(BaseModel):
    founder_id: uuid.UUID
    company_id: uuid.UUID
    application_id: Optional[uuid.UUID]
    raw_inputs: list[dict]    # each dict: {"source": Source, "content": dict}
```

**Output schema:** `list[Claim]` (§3.1).

**Rule set (machine-checkable):**
- R1: every emitted Claim.source.raw_payload_hash matches an input payload hash.
- R2: at least one Claim is emitted for every input payload, OR the input payload is explicitly empty (`content == {}`).
- R3: if no input payload has `source.kind in {github, arxiv, producthunt, accelerator_cohort}`, at least one emitted Claim has `kind="cold_start_inferred"`.
- R4: Claim.text length is in [10, 400] characters.
- R5: no two emitted Claims share the same `(text, source.kind, source.ref)` triple.

### 4.2 Founder Agent (cold-start rule embedded)

**System prompt:**

```
You are the Founder Agent for the VC Brain operating system. You score the founder across four independent axes: technical capability, market_fit, network, and momentum. You also produce a single composite Founder Score — but you do NOT average the four axes blindly; you reason in your `reasoning` field about which axes are most diagnostic given the available evidence and weight the composite accordingly.

COLD-START RULE (HIGHEST PRIORITY — RE-read BEFORE EVERY RUN):
If the available claims contain no GitHub activity, no arxiv publications, no Product Hunt launches, no accelerator cohort membership, and no externally verifiable network signals — i.e. the founder is a true cold-start case — you MUST:
1. Set cold_start=true.
2. Derive your reasoning ONLY from claims of kind in {founder_background, cold_start_inferred, product, traction}. Do not infer technical depth from a school name; do not infer network from a city.
3. Produce a WIDE confidence band. The band width (high - low) MUST be >= 50 points, clamped to [0, 100]. A narrow band on a cold-start founder is a critical error — it signals false certainty to the investor.
4. Never silently assign a low score. A cold-start founder with a compelling deck narrative and a defensible technical angle MUST be able to score 60+ (with the wide band). The band, not the point estimate, communicates uncertainty.
5. Explicitly enumerate in `flags` every missing signal: ["no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"]. Omit a flag only if the corresponding evidence IS present.
6. In `reasoning`, open with the exact sentence: "Cold-start founder. External signals absent. Score derives from deck content alone. Confidence band widened to reflect unverified self-reported claims." Then add 2-4 sentences of substance.

AXIS DEFINITIONS:
- technical_score (0-100): contribution recency, ownership, depth. From GitHub claims (contribution recency, ownership of non-trivial repos with >10 stars or >5 contributors), arxiv claims (authorship of relevant papers), OR — for cold-start — claims about prior engineering roles extracted verbatim from the deck.
- market_fit_score (0-100): use the precomputed Sentence-BERT cosine similarity value provided in your input as `market_fit_similarity` (a float in [0,1]). Multiply by 100. Do not recompute.
- network_score (0-100): accelerator cohort membership, prior VC backing, co-founder connections from founder_network claims. For cold-start, set to 0.
- momentum_score (0-100): recency-weighted activity signal (commits in last 30 days, recent launches, recent papers). For cold-start, set to 0.

NEVER RESET:
You receive the prior FounderScore (or null) in your input as `prior_score`. The new ScoreSnapshot is APPENDED to score_history; you do not modify or summarize prior snapshots. The `trend` field is computed by comparing your new score to the mean of the last 3 prior snapshots:
- new > prior_mean + 5 → "improving"
- new < prior_mean - 5 → "declining"
- else → "stable"
- if fewer than 3 prior snapshots exist → "insufficient_data"

NEVER FABRICATE:
If a fact is missing, omit it. Do not infer technical depth from "studied CS at MIT" without further evidence. Do not infer network from "based in Berlin". Surface the gap in `flags` instead.

OUTPUT FORMAT: schemas.FounderAgentOutput as a single JSON object. All fields required. `reasoning` must be 3-5 sentences. `supporting_claim_ids` must cite at least one claim per non-zero axis, OR — for cold-start — at least one claim from {deck, application_form}.

DO NOT call any tools. DO NOT search the web.
```

**Input schema:**

```python
class FounderAgentInput(BaseModel):
    founder_id: uuid.UUID
    application_id: Optional[uuid.UUID]
    claims: list[Claim]                       # already Validator-tagged where possible
    prior_score: Optional[FounderScore]
    thesis: Thesis
    market_descriptors: list[str]             # thesis.sectors expanded into descriptor phrases
    market_fit_similarity: float              # precomputed cosine similarity in [0,1]
```

**Output schema:** `FounderAgentOutput` (§3.4).

**Rule set:**
- R1: if no input claim has `source.kind in {github, arxiv, producthunt, accelerator_cohort}`, then `cold_start=true`.
- R2: if `cold_start=true`, then `confidence_band[1] - confidence_band[0] >= 50`.
- R3: if `cold_start=true`, then `flags` contains at least 3 of the 5 cold-start flag strings.
- R4: every non-zero axis score has at least one entry in `supporting_claim_ids`.
- R5: `trend` matches the comparison rule against `prior_score.score_history`.

### 4.3 Market Agent

**System prompt:**

```
You are the Market Agent. You assess the MARKET — not the founder, not the product. Three categorical verdicts only: bullish, neutral, bear. NEVER a numeric average. NEVER a "between" verdict like "neutral-to-bullish".

RULES:
1. Bullish requires at least 2 independent verified claims supporting market growth >15% CAGR OR market size >$1B with a clear expansion path. Both claims must have Validator status="verified" — if only one is verified, default to neutral.
2. Bear requires at least 1 verified claim of market contraction OR a saturated competitive landscape with >5 well-funded direct competitors (verified via competitive claims).
3. Neutral is the default when evidence is mixed, insufficient, or contradictory. Mixed = at least one bullish and one bearish verified claim.
4. If evidence is entirely absent or all claims are status="unverifiable" or "not_disclosed", output neutral with confidence_band [20, 80] and reasoning="Insufficient verified market evidence."
5. Contradictions: for every pair of conflicting claims, append a string to `contradictions` of the form: "Claim {id_A} says X (source: {ref_A}); Claim {id_B} says not-X (source: {ref_B})." Do not resolve them — flag them for the Validator/Aggregator.
6. NEVER use the founder's own deck as the sole source for market_size. If the only market_size claim originates from source.kind=deck, set confidence_band to [score-25, score+25] and add to reasoning: "Market size estimate derived from founder deck only; not externally verified."
7. NEVER call external tools. You receive pre-verified claims and the active Thesis in your input — that is your entire universe.

OUTPUT FORMAT: schemas.MarketAgentOutput as a single JSON object.
```

**Input schema:**

```python
class MarketAgentInput(BaseModel):
    company_id: uuid.UUID
    claims: list[Claim]                       # includes Validator flags where present
    thesis: Thesis
```

**Output schema:** `MarketAgentOutput` (§3.4).

**Rule set:**
- R1: `market_score` is one of {"bullish", "neutral", "bear"} — never a numeric value.
- R2: if no claim has Validator status="verified", then `market_score="neutral"`.
- R3: if both bullish-evidence and bear-evidence verified claims exist, then `market_score="neutral"` and `contradictions` is non-empty.

### 4.4 Idea-vs-Market Agent

**System prompt:**

```
You are the Idea-vs-Market Agent. You assess whether the founder's specific product idea serves the market the Market Agent identified, and how defensible that idea is.

You do NOT score the founder. You do NOT score the market. You score the FIT and DEFENSIBILITY of the IDEA.

RULES:
1. fit_score (0-100): how directly does the product described in the deck/application address the market pain points identified in the Market Agent's reasoning (provided in your input as `market_reasoning`)? Score 80+ only if the product maps to a verified market pain point. Score 50-79 for plausible but unverified fit. Score <50 for unclear fit.
2. defensibility_score (0-100): based on (a) technical moat — algorithmic, data, network effect; (b) IP — patents or arxiv publications by the founder covering the core method; (c) switching costs; (d) founder-IP — founder authored the core research.
3. differentiation: 2-4 sentences naming the closest 2 competitors and the specific wedge. "Differentiation unclear — insufficient competitive evidence" is an acceptable answer if evidence is thin. Do not invent competitors.
4. Confidence band:
   - Wide [score-20, score+20] if defensibility claims are self-reported only (source.kind=deck or founder_bio).
   - Narrow [score-8, score+8] if at least one defensibility claim is Validator status="verified".
5. NEVER infer a patent from "we have proprietary tech" without an actual arxiv/publication/patent claim in your input. Missing evidence = lower defensibility score, never invented evidence.
6. NEVER call external tools.

OUTPUT FORMAT: schemas.IdeaVsMarketAgentOutput as a single JSON object.
```

**Input schema:**

```python
class IdeaVsMarketAgentInput(BaseModel):
    company_id: uuid.UUID
    claims: list[Claim]
    market_reasoning: str                     # MarketAgentOutput.reasoning
    thesis: Thesis
```

**Output schema:** `IdeaVsMarketAgentOutput` (§3.4).

**Rule set:**
- R1: both `fit_score` and `defensibility_score` are in [0, 100].
- R2: `differentiation` is non-empty and at least 2 sentences.
- R3: if no claim has `kind in {competitive, technical_depth}` with Validator status="verified", then `defensibility_score <= 50` and confidence_band width >= 30.

### 4.5 Validator Agent (per-claim, no fabrication)

**System prompt:**

```
You are the Validator Agent. You are the ONLY agent permitted to write claim.flags and claim.confidence. Every other agent reads flags but does not write them.

PER-CLAIM EVALUATION:
For each claim you receive, output one of four statuses:
- "verified": at least one independent external source confirms the claim. Set confidence >= 0.8. Cite the confirming source in `counter_evidence_source` (yes, the field name is awkward — repurpose it as confirmation_source here).
- "unverifiable": no external source confirms OR contradicts. Common for self-reported background claims. Set confidence 0.3-0.5. Do not fabricate a confirmation.
- "contradicted": at least one external source directly disputes the claim. Set confidence <= 0.2. Cite the contradicting source in `counter_evidence_source` and quote the relevant snippet in `counter_evidence`.
- "not_disclosed": the claim is missing entirely (the founder did not provide team info, cap table, financials, etc.). Set confidence 0.0. This status is CRITICAL for the Aggregator's missing_required_sections logic.

ABSOLUTE PROHIBITIONS:
1. NEVER fabricate a value for missing data. If a claim says "market size not disclosed" and no external source provides one, output status="not_disclosed", confidence=0.0. Do not invent a TAM. Do not infer from adjacent claims.
2. NEVER upgrade a self-reported claim (source.kind in {deck, application_form, founder_bio}) to "verified" without an external source (source.kind in {github, arxiv, hackernews, producthunt, accelerator_cohort, external_db, company_website}). Self-reported = "unverifiable" at best.
3. NEVER downgrade a claim without citing the contradicting source in counter_evidence_source.
4. NEVER run web search yourself. You receive `external_evidence` in your input — a dict mapping claim_id to a list of {source_url, snippet, retrieved_at}. If your input has no external_evidence entry for a claim, that claim's status MUST be "unverifiable" (or "not_disclosed" if the claim is missing).

COLD-START HANDLING:
If a claim has kind="cold_start_inferred", you MUST set status="unverifiable" with confidence 0.4 and notes="Cold-start inferred claim; no external corroboration available." Never mark these verified. Never mark these contradicted (you have no external evidence to contradict with).

CONTRADICTION DETECTION (CROSS-CLAIM):
Within the input claim set, if two claims of the same kind assert mutually exclusive propositions (e.g. "market size is $5B" vs "market size is $500M"), mark BOTH as "contradicted", set confidence <= 0.2 on both, and in each one's counter_evidence field quote the text of the other claim and reference its claim_id in counter_evidence_source.

OUTPUT FORMAT: a JSON array of schemas.ValidatorAgentOutput, one per input claim. If a claim in the input has no corresponding output, the Aggregator will treat it as "not_disclosed" — so emit an entry for every input claim.

DO NOT call any tools. You process only the external_evidence provided in your input.
```

**Input schema:**

```python
class ValidatorAgentInput(BaseModel):
    claims: list[Claim]
    external_evidence: dict[uuid.UUID, list[dict]]   # claim_id -> [{source_url, snippet, retrieved_at}]
```

**Output schema:** `list[ValidatorAgentOutput]` (§3.4).

**Rule set:**
- R1: one output per input claim — no missing, no extra.
- R2: if `external_evidence[claim_id]` is missing or empty AND `claim.kind != "cold_start_inferred"`, then `status="unverifiable"`.
- R3: if `claim.kind == "cold_start_inferred"`, then `status="unverifiable"` and `confidence <= 0.5`.
- R4: if `status="verified"`, then `claim.source.kind` is NOT in {deck, application_form, founder_bio}.
- R5: if `status="contradicted"`, then `counter_evidence` is non-empty AND `counter_evidence_source` is non-empty.
- R6: if `status="not_disclosed"`, then `confidence == 0.0`.

### 4.6 Aggregator (tool-less synthesizer)

**System prompt:**

```
You are the Aggregator — the final tool-less synthesizer. You receive ONLY pre-verified structured facts. You have NO tool access. You CANNOT call any API, search any source, or read any URL. If a fact is not in your input, it does not exist for the purposes of this memo. You will not speculate, you will not infer, you will not "fill in" missing sections.

YOUR JOB:
1. Decide overall_recommendation: one of {pass, deep_dive, fast_pass, reject}.
   - "fast_pass" = all three axes >= 70 (with market_score mapped bullish=100, neutral=50, bear=10), thesis_fit_score >= 70, evidence_coverage >= 0.6, no open_contradictions, no missing required sections. Recommend immediate $100K deployment within 24h.
   - "deep_dive" = at least one axis >= 70 but contradictions or missing sections exist, OR evidence_coverage in [0.4, 0.6). Recommend a 2-4 hour human diligence sprint before deployment.
   - "pass" = all axes in [40, 70) and no hard reject signal. Park in pipeline; revisit in 30 days.
   - "reject" = any axis < 30, OR thesis_fit_score < 30, OR a verified contradiction on a core claim (team identity, traction numbers, market size, founder existence).
2. Compute overall_conviction as a WEIGHTED GEOMETRIC MEAN — NOT arithmetic mean — of axes:
   `conviction = (founder_score * market_numeric * idea_vs_market_score * thesis_fit_score) ** 0.25`
   where `market_numeric` maps bullish=100, neutral=50, bear=10.
   This prevents one strong axis from masking a fatal weakness (arithmetic mean of 95/10/95/95 = 73.75 looks investible; geometric mean = 52.5 reveals the weakness).
3. Compute evidence_coverage = verified_claims / total_claims. If < 0.4, downgrade overall_recommendation by one tier (fast_pass → deep_dive, deep_dive → pass). Reject stays reject.
4. List all open_contradictions verbatim from the Validator outputs (claim_id pairs + the contradicting snippets).
5. List all missing_required_sections. Required sections (must all be present): company_snapshot, investment_hypotheses, swot, problem_and_product, traction_and_kpis.
6. List all missing_optional_sections. Optional sections (flag if missing, never fabricate): team_and_history, technology_and_defensibility, market_sizing, competition, financials_and_round_structure, cap_table, due_diligence_log, exit_perspective.
7. Generate `memo_markdown` following the structure below. Length rule: as detailed as the decision requires, as brief as clarity allows. Every factual sentence in the memo MUST cite a claim_id in markdown footnote form [^claim_id]. Uncited facts are forbidden. If you cannot cite a fact, do not write it.

MEMO STRUCTURE (render every heading; mark optional-missing with "(not disclosed — request from founder)"):
# Investment Memo: {company_name}
> [cold-start banner if founder_output.cold_start == true]
## Company Snapshot
## Investment Hypotheses
## SWOT
## Problem & Product
## Traction & KPIs
## Team & History
## Technology & Defensibility
## Market Sizing
## Competition
## Financials & Round Structure
## Cap Table
## Due Diligence Log
## Exit Perspective
## Recommendation

The "Due Diligence Log" section always renders a markdown table:
| Claim | Status | Confidence | Source |
|-------|--------|------------|--------|
with one row per Validator output.

The "Recommendation" section renders:
- Overall: {overall_recommendation}
- Conviction: {overall_conviction}/100
- Evidence coverage: {evidence_coverage}
- Open contradictions: {count}
- Next actions: {next_actions as bulleted list}

COLD-START CASE:
If founder_output.cold_start == true, the memo MUST open with a blockquote banner EXACTLY:
"> ⚠️ Cold-start founder. External signals absent. All scores carry wide confidence bands. Recommend deep_dive, not fast_pass, regardless of headline numbers."
AND overall_recommendation MUST NOT be "fast_pass" — downgrade to "deep_dive" even if numbers would otherwise qualify.

OUTPUT FORMAT: schemas.AggregatorOutput as a single JSON object. The `memo_markdown` field contains the full memo text.

YOU HAVE NO TOOLS. DO NOT ATTEMPT TO CALL ANY FUNCTION.
```

**Input schema:**

```python
class AggregatorAgentInput(BaseModel):
    application_id: Optional[uuid.UUID]
    founder_id: uuid.UUID
    company_id: uuid.UUID
    thesis: Thesis
    founder_agent_output: FounderAgentOutput
    market_agent_output: MarketAgentOutput
    idea_vs_market_agent_output: IdeaVsMarketAgentOutput
    validator_outputs: list[ValidatorAgentOutput]
    claims: list[Claim]                              # post-Validator, with flags applied
    prior_founder_score: Optional[FounderScore]
    thesis_fit_score: float                          # precomputed by thesis_fit_node
    company_name: str
```

**Output schema:** `AggregatorOutput` (§3.4).

**Rule set:**
- R1: `overall_recommendation` is one of {pass, deep_dive, fast_pass, reject}.
- R2: if `founder_agent_output.cold_start == true`, then `overall_recommendation != "fast_pass"`.
- R3: `axes` has exactly 3 keys: founder, market, idea_vs_market. No average of the three appears anywhere in the output.
- R4: every factual sentence in `memo_markdown` has at least one `[^claim_id]` citation OR is structural (heading, table header, recommendation label).
- R5: `evidence_coverage` equals `verified_count / total_claims_count` (computed externally and verified).
- R6: `missing_required_sections` is empty if and only if all 5 required sections have at least one cited claim.

---

## 5. Orchestration Graph Definition

Implemented in LangGraph. The graph has 8 nodes: 1 entry (ingestion), 2 parallel pre-scoring nodes (fetch_external_evidence, thesis_fit), 1 validator fan-in, 3 parallel scoring agents (founder, market, idea_vs_market), 1 synthesizer (aggregator).

### 5.1 Shared state

```python
# backend/app/graph/state.py
from typing import TypedDict, Annotated, Optional
from uuid import UUID
from app.schemas.claim import Claim
from app.schemas.founder_score import FounderScore
from app.schemas.thesis import Thesis
from app.schemas.agent_outputs import (
    FounderAgentOutput, MarketAgentOutput,
    IdeaVsMarketAgentOutput, ValidatorAgentOutput, AggregatorOutput
)

def append_list(left: list | None, right: list | None) -> list:
    return (left or []) + (right or [])

class PipelineState(TypedDict):
    # ---- inputs (set by API handler before invoke) ----
    founder_id: UUID
    company_id: UUID
    application_id: Optional[UUID]
    thesis: Thesis
    raw_inputs: list[dict]                      # pre-fetched source payloads (GitHub/arxiv/HN/PH/deck)

    # ---- memory (read from Postgres at entry) ----
    prior_founder_score: Optional[FounderScore]
    market_descriptors: list[str]              # expanded from thesis.sectors

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
    thesis_fit_score: float                    # written by thesis_fit node
    market_fit_similarity: float               # written by thesis_fit node (used by founder node)
    external_evidence: dict                    # written by fetch_external_evidence node

    # ---- final ----
    aggregator_output: Optional[AggregatorOutput]
```

### 5.2 Node functions

```python
# backend/app/graph/nodes.py
from langfuse.openai import openai as langfuse_openai   # auto-traced client
from app.graph.state import PipelineState
from app.agents.ingestion import run_ingestion_agent
from app.agents.founder import run_founder_agent
from app.agents.market import run_market_agent
from app.agents.idea_vs_market import run_idea_vs_market_agent
from app.agents.validator import run_validator_agent
from app.agents.aggregator import run_aggregator_agent
from app.utils.embeddings import embed_text, cosine_similarity
from app.ingestion.dedupe import dedupe_claims
from app.db.session import async_session
from app.db.models import FounderScore as FounderScoreORM, Application
from sqlalchemy import select
import uuid

# Tool-less synthesizer: NO tools= argument. This is enforced at construction.
# GPT-5.6 Sol = OpenAI's frontier flagship (released Jul 9, 2026; knowledge cutoff Feb 2026).
# $5/$30 per 1M tokens. Used for Validator (contradiction detection) and Aggregator (memo synthesis).
SYNTHESIZER_MODEL = langfuse_openai.ChatOpenAI(model="gpt-5.6-sol", temperature=0.2)

# Worker agents use the cheap tier.
# GPT-5.6 Luna = fast, cost-efficient tier ($1/$6 per 1M tokens). Used for Ingestion,
# Founder, Market, Idea-vs-Market agents — three of which run in parallel.
# Do NOT use gpt-4o-mini or gpt-5.5 — both are deprecated/superseded as of Jul 2026.
WORKER_MODEL = langfuse_openai.ChatOpenAI(model="gpt-5.6-luna", temperature=0.1)


async def ingestion_node(state: PipelineState) -> dict:
    """Fan-in raw_inputs -> atomic Claims. Runs dedupe before writing to state."""
    claims = await run_ingestion_agent(
        founder_id=state["founder_id"],
        company_id=state["company_id"],
        application_id=state["application_id"],
        raw_inputs=state["raw_inputs"],
        model=WORKER_MODEL,
    )
    claims = dedupe_claims(claims)             # RapidFuzz + LLM escalation (§7)
    # Compute embeddings for downstream similarity + dedupe
    for c in claims:
        c.embedding = await embed_text(c.text)
    return {"claims": claims}


async def fetch_external_evidence_node(state: PipelineState) -> dict:
    """For each claim, fetch external evidence (web search, Crunchbase mock).
    Returns dict[claim_id, list[evidence]]. This node MAY call external APIs;
    it is NOT the tool-less synthesizer boundary.
    """
    evidence = await fetch_evidence_for_claims(state["claims"])
    return {"external_evidence": evidence}


async def thesis_fit_node(state: PipelineState) -> dict:
    """Compute founder-market-fit cosine similarity + thesis_fit_score.
    Runs in parallel with fetch_external_evidence; both feed into aggregator.
    """
    # Aggregate founder text from claims
    founder_text = " ".join(
        c.text for c in state["claims"]
        if c.kind.value in {"founder_background", "cold_start_inferred", "product"}
    )
    founder_emb = await embed_text(founder_text)
    market_embs = [await embed_text(d) for d in state["market_descriptors"]]
    sims = [cosine_similarity(founder_emb, m) for m in market_embs]
    market_fit_similarity = max(sims) if sims else 0.0
    thesis_fit_score = market_fit_similarity * 100   # 0-100
    return {
        "thesis_fit_score": thesis_fit_score,
        "market_fit_similarity": market_fit_similarity,
    }


async def validator_node(state: PipelineState) -> dict:
    """Per-claim verification. Runs AFTER fetch_external_evidence."""
    outputs = await run_validator_agent(
        claims=state["claims"],
        external_evidence=state["external_evidence"],
        model=SYNTHESIZER_MODEL,                # Validator uses GPT-5.6 Sol for contradiction detection
    )
    # Apply outputs back onto claim objects in state
    claims = apply_validator_outputs(state["claims"], outputs)
    return {"validator_outputs": outputs, "claims": claims}


async def founder_node(state: PipelineState) -> dict:
    """Reads Validator-flagged claims. Runs in parallel with market + idea_vs_market."""
    out = await run_founder_agent(
        founder_id=state["founder_id"],
        application_id=state["application_id"],
        claims=state["claims"],
        prior_score=state["prior_founder_score"],
        thesis=state["thesis"],
        market_descriptors=state["market_descriptors"],
        market_fit_similarity=state["market_fit_similarity"],
        model=WORKER_MODEL,
    )
    return {"founder_output": out}


async def market_node(state: PipelineState) -> dict:
    out = await run_market_agent(
        company_id=state["company_id"],
        claims=state["claims"],
        thesis=state["thesis"],
        model=WORKER_MODEL,
    )
    return {"market_output": out}


async def idea_vs_market_node(state: PipelineState) -> dict:
    out = await run_idea_vs_market_agent(
        company_id=state["company_id"],
        claims=state["claims"],
        market_reasoning=state["market_output"].reasoning,
        thesis=state["thesis"],
        model=WORKER_MODEL,
    )
    return {"idea_vs_market_output": out}


async def aggregator_node(state: PipelineState) -> dict:
    """TOOL-LESS SYNTHESIZER. Receives only pre-verified structured state.
    No tool access. Cannot introduce new unverified claims.
    """
    # Load company_name from DB (or from application raw_payload)
    async with async_session() as s:
        app = await s.get(Application, state["application_id"]) if state["application_id"] else None
        company_name = app.raw_payload.get("company_name", "Unknown") if app else "Outbound Lead"

    out = await run_aggregator_agent(
        application_id=state["application_id"],
        founder_id=state["founder_id"],
        company_id=state["company_id"],
        company_name=company_name,
        thesis=state["thesis"],
        founder_agent_output=state["founder_output"],
        market_agent_output=state["market_output"],
        idea_vs_market_agent_output=state["idea_vs_market_output"],
        validator_outputs=state["validator_outputs"],
        claims=state["claims"],
        prior_founder_score=state["prior_founder_score"],
        thesis_fit_score=state["thesis_fit_score"],
        model=SYNTHESIZER_MODEL,
    )
    # Persist new ScoreSnapshot to founder_scores (APPEND, never replace)
    await persist_founder_score_snapshot(state["founder_id"], state["founder_output"], trigger="application")
    return {"aggregator_output": out}
```

### 5.3 Graph wiring

```python
# backend/app/graph/pipeline.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.graph.state import PipelineState
from app.graph.nodes import (
    ingestion_node,
    fetch_external_evidence_node,
    thesis_fit_node,
    validator_node,
    founder_node,
    market_node,
    idea_vs_market_node,
    aggregator_node,
)

def build_pipeline(checkpointer: AsyncPostgresSaver):
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
    # Both write to disjoint state keys, so no reducer conflict.
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

    return g.compile(checkpointer=checkpointer)
```

### 5.4 Tool-less synthesizer boundary (enforced)

The synthesizer boundary is enforced at three levels:

1. **Code-level**: `aggregator_node` calls `run_aggregator_agent(...)` which internally invokes `SYNTHESIZER_MODEL.invoke(messages)` with NO `tools=` argument. There is no `bind_tools()` call anywhere in `app/agents/aggregator.py`.
2. **Prompt-level**: the Aggregator system prompt (§4.6) ends with "YOU HAVE NO TOOLS. DO NOT ATTEMPT TO CALL ANY FUNCTION."
3. **Input-level**: the synthesizer receives only `AggregatorAgentInput` — a fully materialized Pydantic object. It does not receive the `raw_inputs` list, the `external_evidence` dict, or any URL. If a fact is not in the input, it cannot appear in the memo.

This implements the Perplexity-style VC memo agent pattern: research/verification agents (Ingestion, fetch_external_evidence, Validator) may call external APIs; the final memo-generation agent receives only pre-verified structured facts and has no tool access, so it cannot introduce new unverified claims.

### 5.5 Concurrency model

- `ingestion` → fan-out to {`fetch_external_evidence`, `thesis_fit`} — these run concurrently.
- `fetch_external_evidence` → `validator` → fan-out to {`founder`, `market`} — these run concurrently.
- `market` → `idea_vs_market` (sequential; idea_vs_market reads market_output.reasoning).
- {`founder`, `idea_vs_market`, `thesis_fit`} → fan-in to `aggregator`.

LangGraph's `StateGraph` executes independent edges concurrently within a superstep. The `claims` and `validator_outputs` fields use `Annotated[list, append_list]` reducers so concurrent writes merge rather than overwrite.

---

## 6. API Integration Code Specs

Each ingestion module returns `list[{"source": Source, "content": dict}]`. The Ingestion Agent receives this list and emits Claim records. All modules use a shared `TokenBucket` for rate limiting and write an ETag entry to the `github_etag_cache` table where applicable.

### 6.1 GitHub (REST + GraphQL)

**Auth:** GitHub PAT in `GITHUB_TOKEN` env var (or GitHub App install token for 15k/hr). Headers: `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`.

**Rate limit:** REST 5,000/hr authenticated; GraphQL 5,000 points/hr. Use ETag conditional requests (`If-None-Match`) to get 304 responses that don't count against quota.

**Endpoints used:**
- `GET /repos/{owner}/{repo}` — repo metadata (stars, forks, language, pushed_at).
- `GET /repos/{owner}/{repo}/contributors?per_page=30` — contributor depth.
- `GET /repos/{owner}/{repo}/commits?per_page=30` — recent commits for momentum.
- `POST /graphql` — bulk query when scanning multiple repos (saves quota).

```python
# backend/app/ingestion/github.py
import httpx
from datetime import datetime, timezone, timedelta
from app.utils.ratelimit import TokenBucket
from app.utils.hashing import hash_json
from app.schemas.claim import Source, SourceKind
from app.config import settings

GITHUB_TOKEN = settings.GITHUB_TOKEN
REST_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

# Authenticated REST: 5000/hr ≈ 1.39 req/s sustained. Bucket of 5000 refilling per hour.
bucket = TokenBucket(capacity=5000, refill_per_second=5000/3600)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "VC-Brain/1.0",
}

async def fetch_github_signals(repo_slug: str) -> list[dict]:
    """Returns list of {source, content} dicts ready for Ingestion Agent.
    Uses ETag conditional requests to conserve quota on repeat fetches.
    """
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as c:
        # 1. repo metadata with ETag
        etag = await get_etag(repo_slug)
        req_headers = {"If-None-Match": etag} if etag else {}
        await bucket.acquire()
        r = await c.get(f"{REST_BASE}/repos/{repo_slug}", headers=req_headers)
        if r.status_code == 304:
            return out                                # cache hit, no new claims
        r.raise_for_status()
        if "ETag" in r.headers:
            await set_etag(repo_slug, r.headers["ETag"])
        data = r.json()
        source = Source(
            kind=SourceKind.GITHUB,
            ref=repo_slug,
            ingested_at=datetime.utcnow(),
            raw_payload_hash=hash_json(data),
            retrieved_by="github.fetch_github_signals",
        )
        out.append({"source": source, "content": {
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "language": data["language"],
            "created_at": data["created_at"],
            "pushed_at": data["pushed_at"],
            "description": data["description"],
            "topics": data.get("topics", []),
        }})

        # 2. contributors (depth signal)
        await bucket.acquire()
        r2 = await c.get(f"{REST_BASE}/repos/{repo_slug}/contributors", params={"per_page": 30})
        if r2.status_code == 200:
            contribs = r2.json()
            out.append({"source": source, "content": {
                "contributors": [{"login": x["login"], "contributions": x["contributions"]} for x in contribs],
                "contributor_count": len(contribs),
            }})

        # 3. recent commits (momentum)
        await bucket.acquire()
        r3 = await c.get(f"{REST_BASE}/repos/{repo_slug}/commits", params={"per_page": 30})
        if r3.status_code == 200:
            commits = r3.json()
            commit_dates = [c["commit"]["author"]["date"] for c in commits]
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            commits_30d = sum(1 for d in commit_dates if datetime.fromisoformat(d.replace("Z", "+00:00")) >= cutoff)
            out.append({"source": source, "content": {
                "recent_commit_dates": commit_dates,
                "commit_count_30d": commits_30d,
            }})
    return out


# GraphQL bulk query — used by outbound scan when fetching many repos
BULK_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    stargazerCount
    forkCount
    primaryLanguage { name }
    pushedAt
    createdAt
    description
    repositoryTopics(first: 10) { nodes { topic { name } } }
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 30) {
            nodes { committedDate author { user { login } } }
          }
        }
      }
    }
  }
}
"""

async def fetch_github_graphql(owner: str, name: str) -> dict:
    """Single GraphQL call replaces 3 REST calls — 1 point vs 3 req from quota."""
    await bucket.acquire()
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as c:
        r = await c.post(GRAPHQL_URL, json={"query": BULK_QUERY, "variables": {"owner": owner, "name": name}})
        r.raise_for_status()
        return r.json()["data"]["repository"]
```

**Claim mapping** (Ingestion Agent does this; documented here for clarity):
- `content["stars"] > 50` → Claim(kind=TECHNICAL_DEPTH, text="Repository {repo_slug} has {stars} stars on GitHub.")
- `content["commit_count_30d"]` → Claim(kind=TECHNICAL_DEPTH, text="Repository {repo_slug} received {n} commits in the last 30 days.")
- `content["contributor_count"]` → Claim(kind=FOUNDER_NETWORK, text="Repository {repo_slug} has {n} contributors.")

### 6.2 arXiv

**Auth:** none (CC0). **Rate limit:** 1 request per 3 seconds. **Pagination:** batch 20-50 records per query.

```python
# backend/app/ingestion/arxiv.py
import httpx
import asyncio
from datetime import datetime
from app.utils.ratelimit import TokenBucket
from app.utils.hashing import hash_json
from app.schemas.claim import Source, SourceKind
from xml.etree import ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
bucket = TokenBucket(capacity=1, refill_per_second=1/3)   # 1 req per 3s

NAMESPACES = {"atom": "http://www.w3.org/2005/Atom"}

async def fetch_arxiv_papers(query: str, max_results: int = 20) -> list[dict]:
    """Search arXiv. Query syntax: 'au:"Jane Doe"' for author, 'ti:transformer' for title,
    'cat:cs.AI' for category. Combine with OR/AND.
    """
    out: list[dict] = []
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    await bucket.acquire()
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(ARXIV_API, params=params)
        r.raise_for_status()
    root = ET.fromstring(r.text)
    for entry in root.findall("atom:entry", NAMESPACES):
        arxiv_id = entry.find("atom:id", NAMESPACES).text.split("/abs/")[-1]
        title = entry.find("atom:title", NAMESPACES).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", NAMESPACES).text.strip().replace("\n", " ")
        published = entry.find("atom:published", NAMESPACES).text
        authors = [a.find("atom:name", NAMESPACES).text for a in entry.findall("atom:author", NAMESPACES)]
        categories = [c.get("term") for c in entry.findall("{http://arxiv.org/schemas/atom}primary_category")]
        entry_data = {
            "arxiv_id": arxiv_id,
            "title": title,
            "summary": summary,
            "published": published,
            "authors": authors,
            "categories": categories,
        }
        source = Source(
            kind=SourceKind.ARXIV,
            ref=arxiv_id,
            ingested_at=datetime.utcnow(),
            raw_payload_hash=hash_json(entry_data),
            retrieved_by="arxiv.fetch_arxiv_papers",
        )
        out.append({"source": source, "content": entry_data})
    return out
```

**Claim mapping:**
- For each paper where founder_name is in `content["authors"]`: Claim(kind=TECHNICAL_DEPTH, text="Founder authored arxiv paper {arxiv_id} titled '{title}' published on {published}.")

### 6.3 Hacker News (Algolia Search API for historical)

**Auth:** none. **Rate limit:** undocumented — use responsibly (~1 req/s). **Pagination:** 1000 hits/call max via Algolia; use `hitsPerPage` for finer control.

```python
# backend/app/ingestion/hackernews.py
import httpx
from datetime import datetime
from app.utils.hashing import hash_json
from app.schemas.claim import Source, SourceKind

ALGOLIA_SEARCH = "https://hn.algolia.com/api/v1/search"
FIREBASE_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"

async def fetch_hn_stories(query: str, tags: str = "story") -> list[dict]:
    """Historical search via Algolia. Use for company/founder name lookups."""
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(ALGOLIA_SEARCH, params={
            "query": query,
            "tags": tags,
            "hitsPerPage": 50,
        })
        r.raise_for_status()
        hits = r.json()["hits"]
    for hit in hits:
        source = Source(
            kind=SourceKind.HACKERNEWS,
            ref=f"item:{hit['objectID']}",
            ingested_at=datetime.utcnow(),
            raw_payload_hash=hash_json(hit),
            retrieved_by="hackernews.fetch_hn_stories",
        )
        out.append({"source": source, "content": {
            "title": hit.get("title"),
            "url": hit.get("url"),
            "points": hit.get("points", 0),
            "num_comments": hit.get("num_comments", 0),
            "created_at": hit.get("created_at"),
            "author": hit.get("author"),
        }})
    return out


async def fetch_hn_topstories() -> list[int]:
    """Live top stories via Firebase. Used by outbound scan for signal detection."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(FIREBASE_TOP)
        r.raise_for_status()
        return r.json()[:100]   # top 100 only
```

**Claim mapping:**
- `content["points"] > 50` → Claim(kind=TRACTION, text="Hacker News post '{title}' (item:{id}) has {points} points.")

### 6.4 Product Hunt (GraphQL v2)

**Auth:** OAuth Bearer token in `PRODUCTHUNT_TOKEN` env var. Header: `Authorization: Bearer <token>`.

**Rate limit (verified 2026-07-19):** Two-layer limit applied per application:
1. **Request-rate limit:** ~900 requests per 15-minute window (sliding).
2. **Complexity limit:** 1000 complexity points per query (GraphQL field-cost model).

Both are returned in response headers — inspect `X-Rate-Limit-Remaining` and `X-Rate-Limit-Reset` and back off accordingly. Bound lookback windows, batch conservatively, hard cap at 200 results per scan to stay well under both limits.

```python
# backend/app/ingestion/producthunt.py
import httpx
from datetime import datetime, timedelta
from app.utils.hashing import hash_json
from app.schemas.claim import Source, SourceKind
from app.config import settings

PH_TOKEN = settings.PRODUCTHUNT_TOKEN
PH_GQL = "https://api.producthunt.com/v2/api/graphql"

SEARCH_QUERY = """
query($query: String!, $cursor: String) {
  search(query: $query, type: POST, first: 20, after: $cursor) {
    edges {
      node {
        ... on Post {
          id
          name
          tagline
          votesCount
          website
          launchedAt
          topics { edges { node { name } } }
          makers { name username }
        }
      }
    }
    pageInfo { endCursor hasNextPage }
  }
}
"""

async def fetch_ph_launches(query: str, lookback_days: int = 365, max_pages: int = 10) -> list[dict]:
    """Search PH for launches matching company or founder name."""
    headers = {"Authorization": f"Bearer {PH_TOKEN}"}
    out: list[dict] = []
    cursor = None
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    page = 0
    async with httpx.AsyncClient(timeout=15, headers=headers) as c:
        while page < max_pages:
            r = await c.post(PH_GQL, json={
                "query": SEARCH_QUERY,
                "variables": {"query": query, "cursor": cursor},
            })
            r.raise_for_status()
            data = r.json()["data"]["search"]
            for edge in data["edges"]:
                node = edge["node"]
                launched = datetime.fromisoformat(node["launchedAt"].replace("Z", "+00:00"))
                if launched < cutoff:
                    continue
                source = Source(
                    kind=SourceKind.PRODUCTHUNT,
                    ref=f"post:{node['id']}",
                    ingested_at=datetime.utcnow(),
                    raw_payload_hash=hash_json(node),
                    retrieved_by="producthunt.fetch_ph_launches",
                )
                out.append({"source": source, "content": node})
            if not data["pageInfo"]["hasNextPage"]:
                break
            cursor = data["pageInfo"]["endCursor"]
            page += 1
            if len(out) > 200:                      # hard cap
                break
    return out
```

**Claim mapping:**
- `content["votesCount"] > 100` → Claim(kind=TRACTION, text="Product Hunt launch '{name}' received {votesCount} upvotes.")
- `content["makers"]` → Claim(kind=FOUNDER_NETWORK, text="Founder is listed as maker on Product Hunt launch '{name}'.")

### 6.5 Company website (founder-provided URL only)

**Auth:** none. **Rule:** fetch ONLY URLs the founder explicitly provided in the application form. NEVER bulk-crawl. NEVER follow internal links.

```python
# backend/app/ingestion/website.py
import httpx
from datetime import datetime
from app.utils.hashing import hash_json
from app.schemas.claim import Source, SourceKind
from bs4 import BeautifulSoup

async def fetch_company_website(url: str) -> list[dict]:
    """Fetch a single founder-provided URL. Extract title, meta description, headings.
    Does NOT follow links. Does NOT crawl sitemap.
    """
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
        r = await c.get(url, headers={"User-Agent": "VC-Brain/1.0"})
        if r.status_code != 200:
            return out
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.string if soup.title else None
    meta_desc = soup.find("meta", attrs={"name": "description"})
    h1s = [h.get_text(strip=True) for h in soup.find_all("h1", limit=3)]
    content = {
        "url": str(url),
        "title": title,
        "meta_description": meta_desc["content"] if meta_desc else None,
        "h1_headings": h1s,
    }
    source = Source(
        kind=SourceKind.COMPANY_WEBSITE,
        ref=str(url),
        ingested_at=datetime.utcnow(),
        raw_payload_hash=hash_json(content),
        retrieved_by="website.fetch_company_website",
    )
    out.append({"source": source, "content": content})
    return out
```

### 6.6 Prohibited sources (DO NOT IMPLEMENT)

- **LinkedIn** — never scrape under any circumstance. Founder-pasted bio text from the application form is the only acceptable substitute (source.kind=FOUNDER_BIO).
- **Crunchbase** (bulk scrape) — use the official API within rate limits, or synthesize mock data for the demo. Never scrape HTML.
- **Bulk web crawling** of any platform not listed above.

---

## 7. Deduplication Logic

**Choice:** RapidFuzz `WRatio` as the default first-pass scorer (sub-millisecond on hackathon volumes). Splink/Dedupe are explicitly NOT integrated — they add infra we don't need below ~10k claims, and the demo will not produce that volume.

**Blocking strategy:** block on `(founder_id, claim.kind)`. Two claims of different kinds are never compared (a `market_size` claim and a `technical_depth` claim are obviously distinct). Within a block, pairwise WRatio.

**Thresholds:**
- WRatio ≥ 90 → auto-merge (keep earliest `ingested_at`, set `superseded_by` on the other).
- 80 ≤ WRatio < 90 → escalate to LLM (single YES/NO call to `gpt-5.6-luna` — cheap tier, $1/$6 per 1M tokens).
- WRatio < 80 → treat as distinct claims, no merge.

**Escalation cache:** `(sha256(t1) + sha256(t2))` → bool. Stored in `dedupe_cache` table. Prevents re-querying the LLM for the same pair across runs.

```python
# backend/app/ingestion/dedupe.py
from rapidfuzz import fuzz
from app.schemas.claim import Claim
from app.db.session import async_session
from app.db.models import DedupeCache
from sqlalchemy import select
from app.llm.client import llm_complete
from app.utils.hashing import hash_text
import hashlib

DEDUPE_THRESHOLD = 90
BORDERLINE_LOW = 80
BORDERLINE_HIGH = 90


def _pair_key(t1: str, t2: str) -> str:
    """Stable cache key — order-independent."""
    h1 = hashlib.sha256(t1.encode()).hexdigest()[:16]
    h2 = hashlib.sha256(t2.encode()).hexdigest()[:16]
    return f"{min(h1,h2)}:{max(h1,h2)}"


async def llm_says_same_claim(t1: str, t2: str) -> bool:
    cache_key = _pair_key(t1, t2)
    async with async_session() as s:
        cached = await s.get(DedupeCache, cache_key)
        if cached:
            return cached.is_same
    prompt = f"""Are these two atomic claims expressing the SAME verifiable proposition? Answer only "YES" or "NO".

Claim A: {t1}
Claim B: {t2}"""
    response = await llm_complete(prompt, model="gpt-5.6-luna", temperature=0)
    is_same = response.strip().upper().startswith("Y")
    async with async_session() as s:
        s.add(DedupeCache(key=cache_key, is_same=is_same))
        await s.commit()
    return is_same


async def dedupe_claims(claims: list[Claim]) -> list[Claim]:
    """Returns a new list with duplicates merged. Superseded claims get superseded_by set,
    not deleted — they remain in Postgres for audit trail.
    """
    # 1. Block by (founder_id, kind)
    blocks: dict[tuple, list[Claim]] = {}
    for c in claims:
        blocks.setdefault((c.founder_id, c.kind), []).append(c)

    out: list[Claim] = []
    for (fid, kind), block in blocks.items():
        if len(block) == 1:
            out.extend(block)
            continue

        merged_ids: set[str] = set()
        for i, c1 in enumerate(block):
            if c1.id in merged_ids:
                continue
            for c2 in block[i+1:]:
                if c2.id in merged_ids:
                    continue
                score = fuzz.WRatio(c1.text, c2.text)
                if score >= DEDUPE_THRESHOLD:
                    # Auto-merge: keep the one with earlier ingested_at
                    keep, drop = (c1, c2) if c1.source.ingested_at <= c2.source.ingested_at else (c2, c1)
                    drop.superseded_by = keep.id
                    merged_ids.add(drop.id)
                elif BORDERLINE_LOW <= score < BORDERLINE_HIGH:
                    # Escalate to LLM
                    if await llm_says_same_claim(c1.text, c2.text):
                        keep, drop = (c1, c2) if c1.source.ingested_at <= c2.source.ingested_at else (c2, c1)
                        drop.superseded_by = keep.id
                        merged_ids.add(drop.id)
            out.append(c1)
        # Add unmerged stragglers
        for c in block:
            if c.id not in merged_ids and c not in out:
                out.append(c)
    return out
```

**Fields blocked on:** `founder_id` (foreign key) + `claim.kind` (enum string).

**Escalation path:**
1. RapidFuzz WRatio computes a similarity score in [0, 100].
2. Score ≥ 90 → auto-merge, no LLM call.
3. 80 ≤ score < 90 → LLM escalation (cached by stable pair key).
4. Score < 80 → no merge.

**Why not Splink/Dedupe:** the demo will process ~10-50 founders with ~20 claims each = ~1000 claims total. RapidFuzz pairwise within blocks is ~10µs per pair = ~10ms per founder. Splink's DuckDB setup + probabilistic model training would add 30+ minutes of setup for no measurable quality gain at this volume. If we ever cross 10k claims, the swap is localized to this file.

---

## 8. Re-Scoring Trigger Logic

**Principle:** the pipeline is expensive (multiple LLM calls + external API fetches). Card/memo views are cheap. We re-run the pipeline only when genuinely new information arrives; we serve cached output otherwise.

**Cache TTL:** 60 minutes. Within 60 min of the last `AggregatorOutput`, card/memo views return the cache without invoking any LLM.

**Re-score triggers (any one fires a re-run):**
1. New application received from this founder (`Application.received_at` within TTL window).
2. New external signal with `conviction_delta > 5` (e.g. viral HN post, new GitHub push, new arxiv paper) detected by the outbound scan cron.
3. No prior score exists for this founder (first time we see them).
4. Last score is older than 24 hours (stale-cache sweep).

**Cache-hit (do NOT re-run):**
- Card/memo view request, no new application, no threshold-crossing signal, last score < 60 min old.

```python
# backend/app/triggers/rescore.py
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, desc
from app.db.session import async_session
from app.db.models import Application, FounderSignal, FounderScoreSnapshot, CachedAggregator
import uuid

RESCORE_CACHE_TTL_MINUTES = 60
STALE_CACHE_HOURS = 24


async def should_rescore(founder_id: UUID, application_id: UUID | None) -> tuple[bool, str]:
    """Decide whether to re-run the full pipeline or serve cached AggregatorOutput.
    Returns (rescore: bool, reason: str).
    """
    now = datetime.utcnow()
    ttl_cutoff = now - timedelta(minutes=RESCORE_CACHE_TTL_MINUTES)
    stale_cutoff = now - timedelta(hours=STALE_CACHE_HOURS)

    async with async_session() as s:
        # 1. New application?
        if application_id is not None:
            app = await s.get(Application, application_id)
            if app and app.received_at >= ttl_cutoff:
                return True, "new_application"

        # 2. New external signal crossing conviction threshold?
        sig_q = (
            select(FounderSignal)
            .where(FounderSignal.founder_id == founder_id, FounderSignal.detected_at >= ttl_cutoff)
            .order_by(desc(FounderSignal.detected_at))
        )
        recent_signals = (await s.execute(sig_q)).scalars().all()
        if any(sig.conviction_delta > 5 for sig in recent_signals):
            return True, "signal_threshold_crossed"

        # 3. No prior score?
        last_score_q = (
            select(FounderScoreSnapshot)
            .where(FounderScoreSnapshot.founder_id == founder_id)
            .order_by(desc(FounderScoreSnapshot.computed_at))
        )
        last_score = (await s.execute(last_score_q)).scalars().first()
        if last_score is None:
            return True, "no_prior_score"

        # 4. Stale cache (>24h)?
        if last_score.computed_at < stale_cutoff:
            return True, "stale_cache_24h"

    # 5. Cache hit
    return False, "cache_hit"


async def get_or_compute(founder_id: UUID, application_id: UUID | None) -> tuple[dict, str]:
    """Entry point for card/memo view endpoints.
    Returns (aggregator_output_dict, reason).
    """
    should, reason = await should_rescore(founder_id, application_id)
    if not should:
        cached = await CachedAggregator.read(founder_id)
        if cached:
            return cached.payload, reason
        # Cache miss (rare — TTL expired but stale_check passed): fall through to recompute
        reason = "cache_miss"

    # Re-run pipeline. thread_id = founder_id so LangGraph resumes from checkpoint
    # if interrupted.
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "application_id": application_id,
            # ... other inputs populated by graph entry node
        },
        config={"configurable": {"thread_id": str(founder_id)}},
    )
    out = state["aggregator_output"].model_dump(mode="json")
    await CachedAggregator.write(founder_id, out)
    return out, reason
```

**State diagram (textual):**

```
                                  ┌──────────────────────────────┐
                                  │  card/memo view request      │
                                  │  for founder F               │
                                  └──────────────┬───────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────┐
                              │  should_rescore(F, app_id)       │
                              └────┬────────┬─────────┬──────────┘
                                   │        │         │
                  new_application  │        │ stale_  │ no trigger
                                   │ signal │ cache   │
                                   ▼        ▼ 24h     ▼
                          ┌────────────────────┐   ┌────────────────┐
                          │  re-run pipeline   │   │  serve cached  │
                          │  (LangGraph ainvoke│   │  AggregatorOut │
                          │   thread_id=F)     │   │  from Postgres │
                          └─────────┬──────────┘   └────────────────┘
                                    │
                                    ▼
                          ┌────────────────────┐
                          │  write new         │
                          │  ScoreSnapshot to  │
                          │  founder_scores    │
                          │  (APPEND-only)     │
                          └─────────┬──────────┘
                                    │
                                    ▼
                          ┌────────────────────┐
                          │  update            │
                          │  cached_aggregator │
                          │  row for F         │
                          └────────────────────┘
```

**Critical invariant:** `founder_scores.score_history` is append-only. The re-score logic writes a new row to `founder_score_snapshots` and updates `founder_scores.current_score` + `last_updated_at`, but NEVER deletes or overwrites prior snapshot rows. This satisfies the brief's "persists across applications, never resets" requirement.

---

## 9. UX Component Spec

The UX must be "Notion-level approachability, Bloomberg-level analytical depth." Concrete components below.

### 9.1 Compact Card (Inbox list view)

Render one card per founder in the inbox. Maximum information density without overflow. Cards stack vertically in the inbox list; clicking a card opens the Founder Detail Page (§9.2).

**Visual mock (ASCII representation of layout):**

```
┌─────────────────────────────────────────────────────────────────────┐
│ Acme AI                          Berlin, DE     AI Infra    2h ago   │
│ ─────────────────────────────────────────────────────────────────── │
│ Founder    ▲ 72  [▰▰▰▰▰▰▰▱▱▱]  cold-start⚠️   trend: improving      │
│ Market     ● 65  [▰▰▰▰▰▰▰▱▱▱]  neutral                              │
│ Idea↔Mkt   ▲ 80  [▰▰▰▰▰▰▰▰▰▱]                                       │
│ Thesis Fit     74  [▰▰▰▰▰▰▰▰▱▱]                                     │
│ ─────────────────────────────────────────────────────────────────── │
│ Conviction 70/100   evidence 0.62   contradictions: 1              │
│ ▸ deep_dive                                                         │
│ [Open Memo]  [Pass]  [Fast-Track]                                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Exact field list (top-to-bottom, left-to-right):**

| Row | Field | Source | Format |
|---|---|---|---|
| 1 | Company name | `Application.raw_payload.company_name` | H3, semibold, `text-base` |
| 1 | Geography | `Application.raw_payload.hq_country` (ISO-2 → city/country) | small muted, `text-xs text-muted-foreground` |
| 1 | Sector tag | derived from `Thesis.sectors` match | badge, primary color |
| 1 | Received time | `Application.received_at` (relative) | small muted, `text-xs` |
| 2 | "Founder" axis label | fixed string | `text-sm font-medium` |
| 2 | Trend arrow | `FounderAgentOutput.trend` | ▲ improving (green), ▼ declining (red), ● stable (gray), ⊘ insufficient (muted) |
| 2 | Founder score | `FounderAgentOutput.technical_score` avg with other components, but surfaced as one number | `font-mono text-sm` |
| 2 | Score bar | 0-100 mapped to 10-segment bar | shadcn `Progress` variant |
| 2 | Cold-start flag | `FounderAgentOutput.cold_start` | ⚠️ icon + amber text "cold-start" if true |
| 2 | Trend text | `FounderAgentOutput.trend` | `text-xs text-muted-foreground` |
| 3 | "Market" axis | same pattern | trend arrow = stable by default |
| 3 | Market verdict | `MarketAgentOutput.market_score` (bullish/neutral/bear) | bullish=green, neutral=amber, bear=red |
| 4 | "Idea↔Mkt" axis | `IdeaVsMarketAgentOutput.fit_score` | same pattern |
| 5 | "Thesis Fit" | `AggregatorOutput.thesis_fit_score` | secondary visual weight |
| 6 | Conviction | `AggregatorOutput.overall_conviction` | `font-mono font-semibold` |
| 6 | Evidence coverage | `AggregatorOutput.evidence_coverage` | `text-xs` |
| 6 | Open contradictions count | `len(AggregatorOutput.open_contradictions)` | `text-xs`, red if >0 |
| 7 | Recommendation pill | `AggregatorOutput.overall_recommendation` | colored pill: fast_pass=green, deep_dive=blue, pass=gray, reject=red |
| 8 | Action buttons | n/a | [Open Memo]=primary, [Pass]=ghost, [Fast-Track]=secondary (only shown if recommendation==fast_pass) |

**Cold-start visual treatment:** when `cold_start==true`, the entire card gets a 1px amber border and a small "❄" icon next to the company name.

### 9.2 Full Memo View

**Layout:** single-column scrollable document, max-width 760px (Notion-like), centered. Left rail: section nav with anchor links. Right rail: Pipeline Trace panel (Langfuse trace tree, expandable per agent node — collapsible by default to preserve reading flow).

**Section list** (mapped to Appendix 1 checklist):

| # | Section | Required? | Source data |
|---|---|---|---|
| 1 | Company Snapshot | REQUIRED | `Application.raw_payload` + `Claim` records of kind=product |
| 2 | Investment Hypotheses | REQUIRED | 3-5 bullets, each citing ≥1 claim_id |
| 3 | SWOT | REQUIRED | 4-quadrant grid, each cell cites ≥1 claim_id |
| 4 | Problem & Product | REQUIRED | claims of kind=product |
| 5 | Traction & KPIs | REQUIRED | markdown table (KPI, value, period, source) |
| 6 | Team & History | OPTIONAL | flag with yellow callout "Team & History not disclosed — request from founder." if missing |
| 7 | Technology & Defensibility | OPTIONAL | same callout pattern |
| 8 | Market Sizing | OPTIONAL | same |
| 9 | Competition | OPTIONAL | same |
| 10 | Financials & Round Structure | OPTIONAL | same |
| 11 | Cap Table | OPTIONAL | same |
| 12 | Due Diligence Log | ALWAYS rendered | markdown table: `| Claim | Status | Confidence | Source |` with one row per Validator output |
| 13 | Exit Perspective | OPTIONAL | same callout pattern |
| 14 | Recommendation | REQUIRED | `overall_recommendation`, `overall_conviction`, `evidence_coverage`, `next_actions` |

**Evidence chip rendering:** every `[^claim_id]` citation in the memo renders as an inline chip:

| Validator status | Chip color | Label |
|---|---|---|
| verified | green | `[verified]` |
| unverifiable | yellow | `[unverified]` |
| contradicted | red | `[contradicted]` |
| not_disclosed | gray | `[missing]` |

Clicking a chip opens a right-side drawer (`<Sheet side="right">`) with:
- Full claim text
- Source.kind, Source.ref (as a hyperlink if URL)
- Validator status, confidence, counter_evidence (if any)
- Raw payload (truncated to first 500 chars with "Show more" expander)
- Langfuse trace link (deep link to the span that produced this claim)

**Cold-start banner:** if `AggregatorOutput.founder_output.cold_start == true`, render a red-bordered banner at the very top of the memo, above the title:

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️  Cold-start founder.                                            │
│     External signals absent. All scores carry wide confidence      │
│     bands. Recommend deep_dive, not fast_pass, regardless of       │
│     headline numbers.                                              │
└─────────────────────────────────────────────────────────────────────┘
```

**Header bar (sticky):** company name + overall_recommendation pill + conviction score. Stays visible while scrolling the memo.

**Pipeline Trace side panel:** collapsible right rail showing the Langfuse trace tree for the current run. Top-level nodes: ingestion, fetch_external_evidence, thesis_fit, validator, founder, market, idea_vs_market, aggregator. Each expands to show:
- LLM model used
- Token count (input + output)
- Latency
- Status (success/error)
- Nested spans for each tool call (GitHub fetch, arxiv fetch, etc.)

The trace panel is fetched from `GET /api/traces/{run_id}` which proxies to Langfuse's `/api/public/traces/{traceId}` endpoint.

### 9.3 Additional pages

- **ThesisPage** (`/thesis`): form to edit the active `Thesis` config. Fields: name, sectors (multi-select chips), stage, geography (ISO-2 chips), check_size_usd, ownership_target_pct, risk_appetite (collapsible subsection). Save button writes to `POST /thesis` and triggers a re-score of the entire inbox (with a confirmation modal: "Saving will re-evaluate all 24 founders in the inbox. Continue?").
- **OutboundPage** (`/outbound`): table of outbound-identified founders, same compact card UI as inbox but with a "sourcing_channel" badge (github | arxiv | ph | hn | accelerator). Clicking opens the same Founder Detail Page.
- **InboxPage** (`/`): default landing page. List of compact cards, sorted by `overall_conviction` desc. Filter bar: sector, geography, recommendation, cold-start toggle. Search box: free-text query that uses the multi-attribute reasoning endpoint (`POST /query` — resolves compound queries like "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator" in one pass).

### 9.4 Compound query resolution (Multi-Attribute Reasoning)

The inbox search box accepts compound natural-language queries. These are NOT manual filter toggles — the query goes to `POST /api/query`:

```python
# Request
{
  "query": "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator",
  "thesis_id": "uuid"
}

# Response: list of matching founder cards, ranked by composite score
[
  {"founder_id": "...", "score": 87, "matched_attributes": ["technical", "Berlin", "AI infra", "no_prior_vc", "YC"]},
  ...
]
```

Implementation: the endpoint decomposes the query into atomic attributes (via a small LLM call), maps each attribute to a Claim predicate, and runs a single SQL query joining `claims` + `founder_scores` with all predicates AND'd. This satisfies the brief's "in one pass, not as manual filters" requirement.

---

## 10. Build Order with Acceptance Criteria

Tasks are ordered by judging weight. Within each weight tier, dependencies are respected. Every task has a one-line "done when" acceptance criterion a coding agent can self-check against.

### Tier A — Data Architecture & Intelligence (30% weight)

| # | Task | Done when... |
|---|---|---|
| A1 | Stand up Postgres 16 + pgvector + Langfuse via `infra/docker-compose.yml` | `docker compose up` brings up Postgres (5432), Langfuse (3000), and `CREATE EXTENSION vector;` succeeds on a fresh DB. |
| A2 | Implement Pydantic schemas (`app/schemas/*.py`) — Claim, FounderScore, Thesis, Application, agent outputs | `python -c "from app.schemas.claim import Claim; Claim(...)"` constructs without error; `pytest tests/test_schemas.py` passes. |
| A3 | Implement Alembic migrations for `claims`, `founder_scores`, `founder_score_snapshots`, `applications`, `founder_signals`, `thesis_configs`, `github_etag_cache`, `dedupe_cache`, `cached_aggregator` tables | `alembic upgrade head` runs clean on a fresh DB; `pgvector` extension is created in migration 0003. |
| A4 | Implement Ingestion Agent + the four ingestion modules (`github.py`, `arxiv.py`, `hackernews.py`, `producthunt.py`) + `website.py` | A unit-test fixture (sample deck PDF + sample GitHub repo slug + sample arxiv query) produces ≥5 Claim records with correct `source.kind`, `source.ref`, `source.raw_payload_hash`. |
| A5 | Implement RapidFuzz dedupe with LLM escalation (`ingestion/dedupe.py`) | A test with 3 near-duplicate claims (WRatio 95, 85, 70 against a reference) merges the first two, escalates the second pair to LLM, and leaves the third distinct. |
| A6 | Implement LangGraph pipeline wiring (`graph/state.py`, `graph/nodes.py`, `graph/pipeline.py`) with `AsyncPostgresSaver` checkpointer | `pipeline.ainvoke({...})` runs end-to-end on a fixture founder and writes a checkpoint row to Postgres `langgraph_checkpoints` table. |
| A7 | Implement `embed_text()` and `cosine_similarity()` in `utils/embeddings.py` using local Sentence-BERT ONNX model | A test embedding of "AI infrastructure" returns a 384-dim float list; cosine_similarity of identical strings returns 1.0. |

### Tier B — Investment Utility & Execution (30% weight)

| # | Task | Done when... |
|---|---|---|
| B1 | Implement Founder Agent with cold-start rule (`agents/founder.py` + `agents/prompts/founder.txt`) | A test founder with zero external signals returns `cold_start=true`, `confidence_band` width ≥ 50 points, and `flags` contains all 5 of `no_github`, `no_arxiv`, `no_ph_launch`, `no_accelerator`, `no_prior_vc`. |
| B2 | Implement Market Agent (`agents/market.py`) | A test with 2 verified growth claims returns `market_score="bullish"`; a test with 1 verified contraction claim returns `"bear"`; a test with only deck-sourced claims returns `"neutral"`. |
| B3 | Implement Idea-vs-Market Agent (`agents/idea_vs_market.py`) | `fit_score` and `defensibility_score` are within [0,100]; `differentiation` is ≥2 sentences; if no verified competitive claims exist, `defensibility_score ≤ 50`. |
| B4 | Implement Validator Agent with per-claim confidence and 4 status values (`agents/validator.py`) | A test claim with no external evidence returns `status="unverifiable"`; a test claim with contradicting evidence returns `status="contradicted"` with `counter_evidence_source` set; a missing-entirely claim returns `status="not_disclosed"` with `confidence=0.0`. |
| B5 | Implement Aggregator (tool-less synthesizer) producing `AggregatorOutput` with full `memo_markdown` (`agents/aggregator.py`) | Output memo contains all 5 required sections; every factual sentence has a `[^claim_id]` citation; `evidence_coverage` equals `verified_count / total_claims_count`; if `founder_output.cold_start==true`, the memo opens with the cold-start banner and `overall_recommendation != "fast_pass"`. |
| B6 | Implement `thesis_fit_node` using Sentence-BERT cosine similarity between `thesis.sectors` and founder's claimed focus text | Output `thesis_fit_score` is a float in [0, 100]; `market_fit_similarity` is a float in [0, 1]. |
| B7 | Implement re-scoring trigger logic with 60-min cache (`triggers/rescore.py`) | A second invocation within 60 min returns `reason="cache_hit"` and does NOT invoke any LLM; an invocation after a new `Application` insert returns `reason="new_application"` and re-runs the pipeline. |
| B8 | Implement FastAPI endpoints: `POST /applications`, `GET /founders/{id}/memo`, `GET /founders/{id}/card`, `GET /applications/inbox`, `POST /thesis`, `POST /outbound/scan`, `POST /query` | OpenAPI docs at `/docs` list all 7 endpoints; a curl round-trip works for each; the `POST /applications` endpoint triggers the pipeline asynchronously and returns a 202 with the `founder_id`. |
| B9 | Implement outbound scan script (`scripts/run_outbound_scan.py`) that pulls GitHub trending repos + recent arxiv papers + recent PH launches + top HN posts, scores them through the same pipeline as inbound | Running the script on a 1-hour lookback produces ≥1 new `FounderScore` row that did not exist before; the new founder appears in `/outbound` page with `sourcing_channel` badge. |
| B10 | Implement the "first signal to decision" instrumentation: log `received_at`, `ingestion_complete_at`, `validator_complete_at`, `scoring_complete_at`, `aggregator_complete_at` timestamps on every `Application` row | A test application has all 5 timestamps populated within 90 seconds of `POST /applications`; the `/admin/latency` endpoint returns p50/p95 for each phase. |

### Tier C — Intelligent Analysis & Trust (25% weight)

| # | Task | Done when... |
|---|---|---|
| C1 | Wire Langfuse tracing into every node with `@observe()` decorator (or `langfuse.openai` wrapper for LLM calls) | A single pipeline run produces a trace in Langfuse UI with one span per node and per-LLM-call nested spans; the trace ID is written to `Application.trace_id` for cross-linking. |
| C2 | Implement cross-claim contradiction detection in Validator | A test pair of mutually-exclusive `market_size` claims both get flagged `status="contradicted"` with each other's claim_id cited in `counter_evidence_source`. |
| C3 | Implement evidence coverage computation in Aggregator | `evidence_coverage` equals exactly `verified_count / total_claims_count`; if `< 0.4`, `overall_recommendation` is downgraded by one tier (fast_pass → deep_dive, deep_dive → pass). |
| C4 | Implement cold-start path through the entire pipeline (Ingestion → Founder → Aggregator) | End-to-end test on a cold-start fixture (no GitHub/arxiv/PH/accelerator inputs) produces an `AggregatorOutput` with `founder_output.cold_start==true`, the memo's cold-start banner is present, and `overall_recommendation != "fast_pass"`. |
| C5 | Implement tool-less synthesizer boundary enforcement | Static analysis confirms `app/agents/aggregator.py` contains no `bind_tools()` call and no `tools=` argument; the synthesizer's input is `AggregatorAgentInput` (no `raw_inputs`, no `external_evidence`, no URLs). |
| C6 | Implement the missing-section flagging: every optional section in the memo either has cited content OR renders the "not disclosed — request from founder" callout | A test fixture missing `team_and_history` data produces a memo where the Team & History section contains the callout and `missing_optional_sections` includes `"team_and_history"`. |

### Tier D — UX & Design (15% weight)

| # | Task | Done when... |
|---|---|---|
| D1 | Frontend scaffold: Vite + React 18 + Tailwind 3 + shadcn/ui + TanStack Query 5 | `npm run dev` starts on port 5173 and renders a placeholder InboxPage; `npm run build` produces a production bundle < 500KB gzipped. |
| D2 | Implement `InboxPage` with compact cards matching §9.1 exactly | 10 fixture founders render as cards; every field in §9.1's table is present; the cold-start amber border renders for `cold_start==true` founders. |
| D3 | Implement `FounderDetailPage` with full memo view, evidence chips, side drawer | Clicking a card opens the memo; every claim chip is clickable; the drawer shows `source.ref` + raw payload; the cold-start banner renders at the top when applicable. |
| D4 | Implement `ThesisPage` (edit active thesis config) | Changing sectors/check_size saves to backend and re-scores the inbox; a confirmation modal appears before re-scoring. |
| D5 | Implement `OutboundPage` (list of outbound-identified founders, same card UI) | Outbound-sourced founders appear in a separate tab; clicking them opens the same memo UI; the `sourcing_channel` badge is rendered on each card. |
| D6 | Implement `PipelineTrace` side panel (Langfuse trace tree) | The panel fetches `/api/traces/{run_id}` and renders a collapsible tree of node spans with latency + token counts; clicking a span expands to show nested LLM call spans. |
| D7 | Implement compound query resolution in the inbox search box (`POST /api/query`) | Typing "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator" returns a ranked list of matching founders, each with `matched_attributes` displayed. |

### Stretch goals (only after D7 is complete — priority order)

| # | Task | Done when... |
|---|---|---|
| S1 | Agentic Traceability — every `[^claim_id]` citation in the memo hyperlinks to the exact Langfuse span that produced it | Clicking a citation scrolls the trace panel to the corresponding span and highlights it. |
| S2 | Self-Correction Loop — a re-Validator pass that runs after Aggregator and re-checks any claim the memo cites as evidence for a hypothesis | A test fixture with a fabricated claim (injected manually) gets flagged `status="contradicted"` in the second pass and the memo is regenerated with the claim demoted. |
| S3 | Sourcing Graph — track `sourcing_channel` per founder and compute conversion rate per channel | `/api/sourcing-stats` returns `{channel, count, fast_pass_rate, invested_rate}`; the OutboundPage renders a bar chart of conversion by channel. |

---

## 11. Explicit Non-Goals

The VC Brain MVP handles ONLY: **Sourcing → Screening → Diligence → Decision**. The following are explicitly out of scope and MUST NOT be built. If a coding agent finds itself implementing any of the below, STOP and re-read this section — the 24-hour build window does not allow scope creep into post-investment territory.

### 11.1 Out-of-scope functional areas

- ❌ **Portfolio monitoring** — no KPI dashboards for invested companies post-close, no investor updates tracker, no quarterly reporting automation.
- ❌ **Follow-on investment logic** — no pro-rata calculations, no follow-on sizing, no reserve management, no signal-based follow-on triggers.
- ❌ **Fund operations** — no LP reporting, no capital calls, no NAV calculations, no management fee accrual, no GP/LP waterfalls.
- ❌ **Exit tooling** — no exit modeling, no IRR/MOIC trackers, no acquisition scenario planners, no secondary market pricing.
- ❌ **Legal document generation** — no SAFE generation, no term sheet drafting, no side letter templates. The system recommends a decision; humans handle paperwork.
- ❌ **CRM-style founder communication workflows beyond cold-outreach email generation** — no drip campaigns, no meeting scheduling, no calendar integration, no automated follow-up sequences.
- ❌ **Bulk web crawling** of LinkedIn or any platform the brief prohibits scraping (see §6.6).
- ❌ **Real-time streaming of GitHub commits into the inbox** — signals are polled on a schedule (hourly outbound scan + 60-min re-score TTL); the inbox is a daily-review surface, not a Slack-style real-time feed.
- ❌ **Multi-fund / multi-thesis support in the UI** — the data schema supports multiple `Thesis` rows, but the MVP UI exposes only one active thesis at a time. The ThesisPage is a single-record editor, not a multi-thesis manager.
- ❌ **Authentication and multi-user tenancy** — single-user demo. No OAuth, no SSO, no RBAC. The `User` table does not exist in the MVP. (Add later for production.)
- ❌ **Audit log and compliance reporting** — out of scope for the hackathon. The `superseded_by` field on Claims provides basic provenance; full audit trails come later.
- ❌ **Mobile-responsive design** — desktop-first. The brief targets an investor at a desk reviewing memos, not a mobile user. Tailwind breakpoints exist but mobile layout is not validated.
- ❌ **Internationalization (i18n)** — English-only. No translation layer.

### 11.2 Out-of-scope technical decisions (locked, do not revisit)

- ❌ Do NOT swap LangGraph for CrewAI / Mastra / Pydantic AI / MAF — the choice is made in §1 and the graph wiring in §5 depends on LangGraph's `StateGraph` + `Annotated[list, reducer]` semantics.
- ❌ Do NOT swap Postgres for MongoDB / DynamoDB / a vector DB service — pgvector satisfies the embedding storage requirement at hackathon scale; introducing a separate vector DB adds infra without measurable benefit.
- ❌ Do NOT swap RapidFuzz for Splink / Dedupe — volumes are too low to justify the infra (§7).
- ❌ Do NOT swap Langfuse for Arize Phoenix / MLflow — Langfuse's step-level tracing maps 1:1 to LangGraph nodes and is the default (§1).
- ❌ Do NOT introduce a message queue (Kafka / RabbitMQ / SQS) — the pipeline runs synchronously per request with `AsyncPostgresSaver` checkpointing for resilience. A queue adds operational complexity we don't need.
- ❌ Do NOT containerize the LLM provider — we use OpenAI's hosted API. Self-hosting a model is out of scope.

### 11.3 Scope boundary restated

The MVP delivers:
1. **Sourcing**: inbound applications (POST /applications) + outbound scan (GitHub trending, arxiv, PH, HN).
2. **Screening**: Ingestion → Validator → 3 parallel scoring agents (Founder, Market, Idea-vs-Market) → Aggregator.
3. **Diligence**: full investment memo with per-claim evidence, contradictions flagged, missing sections called out.
4. **Decision**: overall_recommendation (fast_pass / deep_dive / pass / reject) + next_actions + 24h deployability signal.

Anything before sourcing (raw deal-flow CRM) or after decision (portfolio ops, follow-on, exits, fund admin) is out of scope. If the coding agent is asked to build any of those, the answer is "not in MVP — see §11."

---

## Formatting & Handoff Notes

- All code blocks are complete and pasteable. No `...` truncations.
- Every schema is complete Pydantic v2 (or SQLAlchemy mirror), not pseudocode.
- Every system prompt is ready to paste into `ChatOpenAI(...).invoke([{"role":"system","content":PROMPT},{"role":"user","content":json.dumps(input)}])`.
- Every external API integration includes auth, rate limit, endpoint, pagination, and Claim mapping.
- Where the brief offered options (orchestration framework, dedupe approach, observability tool, vector store), the choice is made and justified in §1.
- Where the brief flagged a critical differentiator (cold-start handling), the rule is repeated verbatim in §3.2 (FounderScore schema), §4.1 (Ingestion Agent R3), §4.2 (Founder Agent — full cold-start rule), §4.5 (Validator Agent cold-start handling), §4.6 (Aggregator cold-start case + downgrade rule), §9.1 (card visual treatment), §9.2 (memo banner), §10.B1 (acceptance criterion), §10.B5 (acceptance criterion), §10.C4 (end-to-end test). Any of those locations will catch a regression.
- The tool-less synthesizer boundary is enforced at three levels (code, prompt, input) — see §5.4. The Aggregator cannot introduce unverified claims because it has no tool access and receives only pre-verified structured facts.
- Build order (§10) matches judging weights exactly: Tier A (30%) → Tier B (30%) → Tier C (25%) → Tier D (15%). Stretch goals S1/S2/S3 follow only after D7.

This file is the single source of truth. Hand it to a coding agent with no human editing pass in between.
