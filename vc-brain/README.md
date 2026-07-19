# Founder Signal — VC Brain

> An AI-powered investment screening operating system that sources, screens, and scores startup founders for a solo VC investor deploying $100K checks. Built in 24 hours for a hackathon.

**Live repo**: [github.com/f2025408135-cyber/Founder-Signal](https://github.com/f2025408135-cyber/Founder-Signal)

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [Demo Videos](#2-demo-videos)
3. [Quick Start (5 Minutes)](#3-quick-start-5-minutes)
4. [Architecture Overview](#4-architecture-overview)
5. [Tech Stack](#5-tech-stack)
6. [Repository Structure](#6-repository-structure)
7. [Backend: How It Works](#7-backend-how-it-works)
8. [Frontend: Pages & Features](#8-frontend-pages--features)
9. [Key Concepts](#9-key-concepts)
10. [API Reference](#10-api-reference)
11. [Testing](#11-testing)
12. [Configuration](#12-configuration)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. What Is This?

**Founder Signal** (a.k.a. "VC Brain") is an agentic investment screening system. It takes raw signals — GitHub commits, arXiv papers, Product Hunt launches, investor applications — and runs them through a pipeline of 6 specialized AI agents to produce an evidence-backed investment memo in minutes instead of weeks.

### The two things that make it different from every other "AI for VC" tool:

1. **Cold-start handling**: A founder with zero funding history, no GitHub, no network still gets scored fairly. The system returns a wide, honest confidence range built from what IS inferable (the deck itself), rather than defaulting to a falsely precise low score. This is enforced at 4 levels: schema, ingestion, founder scoring, and aggregation.

2. **Tool-less synthesizer boundary**: The final memo generator (Aggregator agent) has ZERO tool access. It receives only pre-verified structured facts — no URLs, no raw data, no web search. It can only cite what upstream agents already verified. A static analysis script enforces this in CI.

### What it does NOT do (by design):
- ❌ Portfolio monitoring, follow-on logic, fund operations
- ❌ Legal document generation (SAFEs, term sheets)
- ❌ LinkedIn scraping or bulk web crawling
- ❌ Real-time streaming (signals are polled hourly)
- ❌ Authentication / multi-user tenancy

---

## 2. Demo Videos

Two videos are included in the `video/out/` directory:

| Video | File | Duration | Purpose |
|---|---|---|---|
| **Technical Architecture** | `vc-brain-demo.mp4` | 60s | How the system works internally (agent swarm, pipeline, trust) |
| **Product Demo** | `vc-brain-product-demo.mp4` | 60s | What it does for an investor (Fin Agent, Radar, cold-start, verdict) |

Plus 6 detailed architectural clips in `video/out/clips/`:
- `Clip1MemoryIngestion.mp4` — Memory layer & ingestion pipeline (15s)
- `Clip2AgentSwarm.mp4` — 8-node LangGraph pipeline topology (12s)
- `Clip3ThreeAxes.mp4` — Three independent axes, never averaged (12s)
- `Clip4Validator.mp4` — Per-claim evidence verification (15s)
- `Clip5ColdStart.mp4` — Cold-start rule & wide confidence band (12s)
- `Clip6Toolless.mp4` — Tool-less synthesizer boundary (13s)

---

## 3. Quick Start (5 Minutes)

### Prerequisites

- **Docker** + Docker Compose (for Postgres + Langfuse)
- **Python 3.12+** (for backend)
- **Node.js 18+** with npm (for frontend)
- **OpenAI API key** (GPT-5.6 series — or any OpenAI-compatible model)

### Step 1: Start Postgres + Langfuse

```bash
cd vc-brain/infra
docker compose up -d
```

Wait for healthchecks to pass:
```bash
docker compose ps  # both services should show "healthy"
```

### Step 2: Configure backend

```bash
cd vc-brain/backend
cp .env.example .env
# Edit .env and fill in:
#   OPENAI_API_KEY=sk-...
#   GITHUB_TOKEN=ghp_... (optional, for outbound scan)
#   LANGFUSE_PUBLIC_KEY=pk-lf-... (create project at http://localhost:3000)
#   LANGFUSE_SECRET_KEY=sk-lf-...
```

### Step 3: Install backend + run migrations

```bash
cd vc-brain/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

### Step 4: Start the backend

```bash
cd vc-brain/backend
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

### Step 5: Start the frontend

```bash
cd vc-brain/frontend-next
npm install
npm run dev
```

Open `http://localhost:3000` — you'll land on the **Fin Agent** hero screen.

### Step 6: Try it out

1. Type a thesis in plain English: `"pre-seed AI infra founders in Berlin"`
2. Answer Fin Agent's follow-up questions
3. Confirm the thesis → pipeline runs
4. View results in the Inbox
5. Click any founder card to open the full investment memo

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 16 + React 19)                │
│                                                                     │
│  /hero (Fin Agent)  /inbox (Dashboard)  /founders/[id] (Memo)      │
│  /thesis (Config)   /network (Graph)   /funnel (Pipeline)          │
│  /guide (Usage Guide)                                               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP /api/*
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + LangGraph)                     │
│                                                                     │
│  POST /applications ──►  ┌──────────────────────────┐               │
│  POST /outbound/scan ──► │   LangGraph Pipeline      │               │
│                          │   (8 nodes, parallel)     │               │
│                          └──────────┬───────────────┘               │
│                                     │                               │
│  ingestion ──► [fetch_evidence || thesis_fit]                       │
│                      │                                              │
│                    validator                                        │
│                      │                                              │
│          [founder || market] ──► idea_vs_market                     │
│                      │                                              │
│                    aggregator (TOOL-LESS)                           │
│                      │                                              │
│                    AggregatorOutput + memo_markdown                 │
│                                                                     │
│  GET /founders/{id}/card   GET /founders/{id}/memo                  │
│  GET /applications/inbox   POST /query   GET /traces/{run_id}       │
│  GET /events/stream (SSE)  POST /fin/chat                           │
└─────────┬─────────────────────────┬──────────────┬──────────────────┘
          │                         │              │
          ▼                         ▼              ▼
   ┌────────────┐          ┌──────────────┐  ┌──────────────┐
   │ PostgreSQL │          │   Langfuse   │  │    OpenAI    │
   │   18 +     │          │     v3       │  │   GPT-5.6    │
   │  pgvector  │          │  (tracing)   │  │ Luna + Sol   │
   └────────────┘          └──────────────┘  └──────────────┘
```

### Pipeline Flow (8 LangGraph nodes)

```
ingestion ──► [fetch_external_evidence || thesis_fit]   # parallel
                    │
                    ▼
                validator
                    │
        [founder || market] ──► idea_vs_market          # founder+market parallel
                    │
                    ▼
               aggregator (TOOL-LESS)
                    │
                    ▼
           AggregatorOutput + memo_markdown
```

- `claims` and `validator_outputs` use `Annotated[list, append_list]` reducers so parallel writes merge rather than overwrite.
- `AsyncPostgresSaver` checkpointer with `thread_id = founder_id` for resume-on-interrupt.

---

## 5. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend framework** | Python 3.12 + FastAPI | Same language as LangGraph — zero serialization boundary |
| **Orchestration** | LangGraph 1.2+ | Native `StateGraph` with `Annotated[list, add]` reducers for parallel writes |
| **Database** | PostgreSQL 18 + pgvector 0.8.x | Relational core + 384-dim vector embeddings for similarity search |
| **Observability** | Langfuse v3 (self-hosted) | Step-level tracing maps 1:1 to LangGraph nodes |
| **LLM** | OpenAI GPT-5.6 Luna (workers) + GPT-5.6 Sol (validator/aggregator) | Cost/latency split — 3 parallel workers on cheap tier |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | 384-dim, CPU-runnable, no per-call cost |
| **Deduplication** | RapidFuzz WRatio | Sub-millisecond on hackathon volumes |
| **Frontend** | Next.js 16 + React 19 + Tailwind CSS v4 + shadcn/ui | App Router + RSC for heavy static content |
| **Network graph** | React Flow (xyflow) | 2D HTML/SVG, handles 500 nodes natively |
| **Video** | Remotion (React-based) | Frame-accurate programmatic video |
| **Charts** | Recharts | Composable, dark-mode friendly |
| **Tables** | TanStack Table v8 | Headless, column resizing + sorting |

---

## 6. Repository Structure

```
vc-brain/
├── README.md                           # This file
├── DOCUMENTATION.md                    # 3700-line comprehensive build record
├── FRONTEND_SPEC.md                    # 1300-line frontend build specification
├── DEMO_SCRIPT.md                      # Live demo script for judges
├── docs/
│   └── BUILD_SPEC.md                   # The 1944-line resolved spec (source of truth)
├── backend/                            # Python FastAPI + LangGraph backend
│   ├── app/
│   │   ├── main.py                     # FastAPI app factory
│   │   ├── config.py                   # Pydantic settings (env-driven)
│   │   ├── agents/                     # 6 AI agents + system prompts
│   │   │   ├── ingestion.py            # Raw signals → atomic Claims
│   │   │   ├── founder.py              # Founder scoring (cold-start rule)
│   │   │   ├── market.py               # Market verdict (bullish/neutral/bear)
│   │   │   ├── idea_vs_market.py       # Product-market fit + defensibility
│   │   │   ├── validator.py            # Per-claim verification (ONLY flag writer)
│   │   │   ├── aggregator.py           # Tool-less synthesizer (memo generator)
│   │   │   └── prompts/                # System prompts (6 .txt files)
│   │   ├── graph/                      # LangGraph wiring
│   │   │   ├── state.py                # PipelineState TypedDict + reducers
│   │   │   ├── nodes.py                # 8 node functions (@observe-decorated)
│   │   │   └── pipeline.py             # build_pipeline() + AsyncPostgresSaver
│   │   ├── api/routes/                 # FastAPI endpoints
│   │   │   ├── applications.py         # POST /applications (202 + async pipeline)
│   │   │   ├── inbox.py                # GET /applications/inbox
│   │   │   ├── founders.py             # GET /founders/{id}/card + /memo
│   │   │   ├── thesis.py               # GET/POST /thesis
│   │   │   ├── outbound.py             # POST /outbound/scan + GET /queue
│   │   │   ├── query.py                # POST /query (compound search)
│   │   │   ├── traces.py               # GET /traces/{run_id} (Langfuse proxy)
│   │   │   ├── events.py               # GET /events/stream (SSE for Signal Radar)
│   │   │   ├── fin.py                  # POST /fin/chat (Fin Agent)
│   │   │   └── admin.py                # GET /admin/latency
│   │   ├── ingestion/                  # External API clients
│   │   │   ├── github.py               # REST + GraphQL + ETag
│   │   │   ├── arxiv.py                # Atom XML search
│   │   │   ├── hackernews.py           # Algolia + Firebase
│   │   │   ├── producthunt.py          # GraphQL v2
│   │   │   ├── website.py              # Founder-provided URL only
│   │   │   └── dedupe.py               # RapidFuzz + LLM escalation
│   │   ├── schemas/                    # Pydantic v2 models
│   │   ├── db/                         # SQLAlchemy ORM + 3 Alembic migrations
│   │   ├── triggers/rescore.py         # 4 re-scoring triggers + 60-min cache
│   │   ├── llm/client.py               # OpenAI + Langfuse wrapper (NO tools)
│   │   ├── tracing.py                  # @observe() decorator
│   │   └── utils/                      # embeddings, hashing, ratelimit
│   └── tests/                          # 117 tests (116 passing + 1 env-specific)
├── frontend-next/                      # Next.js 16 frontend (primary)
│   ├── app/
│   │   ├── hero/                       # Fin Agent (conversational entry point)
│   │   ├── inbox/                      # Dashboard (founder cards + Signal Radar)
│   │   ├── founders/[founderId]/       # Investment memo view
│   │   ├── thesis/                     # Thesis config editor
│   │   ├── network/                    # React Flow relationship graph
│   │   ├── funnel/                     # Sourcing-to-decision funnel
│   │   └── guide/                      # Visual usage guide
│   ├── components/                     # UI components (shadcn-style)
│   │   ├── founder/                    # FounderCard, AxisScore, ConfidenceBand
│   │   ├── memo/                       # MemoView, EvidenceChip, EvidenceDrawer, Verdict
│   │   ├── radar/                      # SignalRadar (SVG HUD)
│   │   ├── hero/                       # ParticleSphere (Three.js)
│   │   └── ui/                         # Button, Card, Badge, Sheet, etc.
│   └── lib/                            # API client, types, utils, hooks
├── video/                              # Remotion video project
│   ├── src/                            # Video compositions + scenes + clips
│   └── out/                            # Rendered MP4 files
├── dataset/                            # 50-founder synthetic dataset
│   ├── founders/                       # 50 JSON files (one per founder)
│   ├── index.json                      # Summary index
│   └── README.md                       # Distribution docs + demo fixtures
├── infra/
│   ├── docker-compose.yml              # Postgres 18 + pgvector + Langfuse
│   └── postgres-init/001-extensions.sql
└── scripts/                            # Seed, scan, validation scripts
```

---

## 7. Backend: How It Works

### The 6 Agents

| Agent | Role | Model | Key Rule |
|---|---|---|---|
| **Ingestion** | Raw signals → atomic Claims | GPT-5.6 Luna | R3: Must emit `cold_start_inferred` claim if no external signals |
| **Validator** | Per-claim verification — the ONLY agent that writes `claim.flags` and `claim.confidence` | GPT-5.6 Sol | R2: Self-reported claims can NEVER be "verified" without external corroboration |
| **Founder** | Scores founder across 4 axes (technical, market_fit, network, momentum) | GPT-5.6 Luna | Cold-start rule: confidence_band width ≥ 50, all 5 flags, never fast_pass |
| **Market** | Categorical verdict: bullish / neutral / bear | GPT-5.6 Luna | NEVER a numeric average. Bullish requires ≥2 verified growth claims |
| **Idea-vs-Market** | Scores FIT (product→market) and DEFENSIBILITY | GPT-5.6 Luna | R3: No verified competitive claims → defensibility ≤ 50 |
| **Aggregator** | Tool-less synthesizer — produces final memo | GPT-5.6 Sol | NO tools, NO URLs, NO raw_inputs. Can only cite pre-verified facts |

### The Cold-Start Rule (4 levels of enforcement)

1. **Schema**: `ClaimKind.COLD_START_INFERRED` enum value + `cold_start: bool` field on `FounderAgentOutput`
2. **Ingestion Agent R3**: If no external source kinds (GitHub/arXiv/PH/accelerator), MUST emit at least one `cold_start_inferred` claim
3. **Founder Agent Rule**: `confidence_band` width ≥ 50, ALL 5 flags enumerated (`no_github`, `no_arxiv`, `no_ph_launch`, `no_accelerator`, `no_prior_vc`)
4. **Aggregator Downgrade**: `overall_recommendation ≠ "fast_pass"` — forced to `deep_dive`

### Trust Scores (Per-Claim, Never Whole-Company)

| Status | Color | Meaning | Confidence |
|---|---|---|---|
| `verified` | 🟢 Green | External source confirms | ≥ 0.8 |
| `unverifiable` | 🟡 Amber | No external data | 0.3-0.5 |
| `contradicted` | 🔴 Red | External source disputes | ≤ 0.2 |
| `not_disclosed` | ⚪ Gray | Missing entirely | 0.0 |

### Re-Scoring Triggers (60-min cache TTL)

1. New application received from this founder
2. External signal with `conviction_delta > 5` detected by outbound scan
3. No prior score exists (first time we see them)
4. Last score older than 24 hours (stale-cache sweep)

---

## 8. Frontend: Pages & Features

| Page | Route | What It Does |
|---|---|---|
| **Fin Agent** | `/hero` | Conversational entry point — type your thesis in plain English, Fin Agent interviews you, runs the pipeline, hands off to dashboard. Includes Three.js particle sphere. |
| **Inbox** | `/inbox` | Founder card grid sorted by conviction. Includes compound query search, filters, and the Signal Radar (live pipeline activity HUD). |
| **Founder Detail** | `/founders/[id]` | 3-column memo view: section nav + memo with evidence chips + pipeline trace. Click any chip to see source provenance. |
| **Thesis Config** | `/thesis` | Edit active investment thesis. Chip-based multi-selects for sectors/stage/geography. Confirmation modal before re-scoring inbox. |
| **Network** | `/network` | React Flow 2D canvas — founders ↔ sourcing channels ↔ institutions as connected nodes. |
| **Funnel** | `/funnel` | Sankey-style funnel: Sourced → Screened → Diligence → Decision (fast_pass/pass/reject). |
| **Guide** | `/guide` | Visual usage guide — 11 sections explaining every feature using real UI components. |

### Design Tokens

```
Background:        #0a0908 (graphite black)
Card surface:      #14151a
Modal/overlay:     #1e1e22
Accent:            #5e6ad2 (lavender-blue — primary actions only)
Verified:          #3ecf8e (desaturated emerald)
Warning:           #d4a843 (desaturated amber)
Error:             #d44a5c (desaturated crimson)
Text primary:      #f7f8f8 (NOT pure white — reduces eye strain)
Font:              Geist Sans (Medium 500 + Bold 700 only)
```

---

## 9. Key Concepts

### Atomic Claims
Every piece of evidence is a single declarative sentence — one verifiable proposition per Claim. "Founder has 8 years of AI experience and previously sold a YC company" is TWO claims, split by the Ingestion Agent.

### Geometric Mean (Not Arithmetic)
Conviction = (founder × market_numeric × idea × thesis_fit) ^ 0.25. This prevents one strong axis from masking a fatal weakness: arithmetic mean of 95/10/95/95 = 73.75 looks investible; geometric mean = 52.5 reveals the weakness.

### Tool-Less Synthesizer Boundary
The Aggregator agent has NO tool access — enforced at 3 levels:
1. **Code**: No `bind_tools()` call anywhere in `aggregator.py` (verified by `scripts/check_toolless_boundary.py`)
2. **Prompt**: "YOU HAVE NO TOOLS. DO NOT ATTEMPT TO CALL ANY FUNCTION."
3. **Input**: `AggregatorAgentInput` excludes `raw_inputs`, `external_evidence`, and URLs

### Append-Only Score History
`FounderScore.score_history` is a list that NEVER resets. Each pipeline run appends a new `ScoreSnapshot`. This satisfies the "persists across applications, never resets" requirement.

---

## 10. API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/applications` | Submit application → 202 + founder_id, pipeline runs async |
| GET | `/api/applications/inbox` | Founder card list sorted by conviction |
| GET | `/api/founders/{id}/card` | Compact card data |
| GET | `/api/founders/{id}/memo` | Full memo + claims + score history |
| GET | `/api/thesis` | Read active thesis |
| POST | `/api/thesis` | Update thesis (invalidates inbox cache) |
| POST | `/api/outbound/scan` | Trigger outbound scan (background) |
| GET | `/api/outbound/queue` | Outbound-sourced founders with channel badges |
| POST | `/api/query` | Compound query (natural language → SQL) |
| GET | `/api/traces/{run_id}` | Langfuse trace proxy |
| GET | `/api/events/stream` | SSE stream for Signal Radar |
| POST | `/api/fin/chat` | Fin Agent conversational endpoint |
| GET | `/api/admin/latency` | p50/p95 latency per pipeline phase |
| GET | `/api/ping` | Health check |

---

## 11. Testing

```bash
cd vc-brain/backend
python -m pytest tests/ -v
```

**117 tests** across 12 test files:
- `test_schemas.py` (11) — Pydantic schema validation
- `test_dedupe.py` (10) — RapidFuzz deduplication
- `test_agents.py` (6) — Ingestion Agent rules
- `test_ingestion_modules.py` (9) — GitHub/arXiv/HN/PH/website modules
- `test_embeddings.py` (7) — Sentence-BERT embeddings
- `test_pipeline.py` (4) — End-to-end pipeline on 3 fixtures
- `test_api.py` (9) — FastAPI endpoint tests
- `test_triggers.py` (5) — Re-scoring trigger logic
- `test_outbound_scan.py` (4) — Outbound scan script
- `test_tier_c.py` (19) — Tracing, contradictions, boundary, missing sections
- `test_adversarial_fixes.py` (24) — Regression tests from adversarial review
- `test_frontend.py` (9) — Frontend build + source structure

### Static Analysis
```bash
python scripts/check_toolless_boundary.py
# Verifies no bind_tools() in aggregator.py
```

---

## 12. Configuration

All configuration is environment-variable driven via `backend/.env`:

```bash
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain

# Optional (for tracing)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Optional (for outbound scan)
GITHUB_TOKEN=ghp_...
PRODUCTHUNT_TOKEN=...

# Models (defaults shown)
WORKER_MODEL=gpt-5.6-luna
SYNTHESIZER_MODEL=gpt-5.6-sol
```

---

## 13. Troubleshooting

### "ModuleNotFoundError: No module named 'sqlalchemy'"
Run `pip install -e ".[dev]"` from the `backend/` directory.

### Frontend shows white screen / CSS not loading
Make sure you're running `npm run dev` from the `frontend-next/` directory (not the repo root). Next.js dev server takes 10-15 seconds to compile on first load.

### Backend 500 error on API calls
Check that Postgres is running: `docker compose ps` from `infra/`. Check that migrations are applied: `alembic upgrade head` from `backend/`.

### Langfuse trace panel shows "not available"
Either Langfuse isn't running (`docker compose up -d` from `infra/`) or the `LANGFUSE_*` env vars aren't set in `backend/.env`.

### OpenAI API 403 "unsupported_country_region_territory"
The OpenAI API key is valid but the server region is blocked. Use a VPN/proxy or switch to a region-agnostic provider.

### Outbound scan returns no results
Ensure `GITHUB_TOKEN` is set in `backend/.env`. Without it, GitHub ingestion is skipped.

---

*This README is designed for someone with zero prior context about this repo. If you read this far, you should be able to run the system, understand every component, and know where to look when something breaks.*
