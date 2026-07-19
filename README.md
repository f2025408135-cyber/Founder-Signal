# Founder Signal

Founder Signal is an evidence-first investment-screening workspace for early-stage founders. It collects founder-provided and permitted external signals, validates individual claims, presents separate Founder, Market, and Idea-vs-Market assessments, and produces a cited investment memo with explicit uncertainty.

Cold-start founders are intentionally treated as uncertain rather than weak: the product shows a wide confidence band, clear missing-data callouts, and a deep-dive recommendation rather than a falsely precise score.

## Repository Layout

- `backend/`: FastAPI, LangGraph pipeline, schemas, migrations, and tests.
- `vc-brain/frontend-next/`: Next.js 16 judging UI.
- `infra/`: Postgres/pgvector and Langfuse local services.
- `scripts/seed_fixtures.py`: creates the three named demo fixture applications.
- `docs/BUILD_SPEC.md` and `vc-brain/FRONTEND_SPEC.md`: product and interface specifications.

## Run Locally

Prerequisites: Python 3.12+, Node 20.9+, npm, and Docker Desktop. The backend needs Postgres for inbox, memo, and persistence routes. OpenAI is required to run a new scoring pipeline; GitHub, Product Hunt, and Langfuse credentials are optional.

1. Start local infrastructure from the repository root:

```powershell
docker compose -f infra/docker-compose.yml up -d
```

2. Configure and start the backend:

```powershell
Set-Location backend
Copy-Item .env.example .env
# Set OPENAI_API_KEY in backend/.env. Set LANGFUSE_ENABLED=false to run without Langfuse.
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

3. In a second terminal, configure and start the judging frontend:

```powershell
Set-Location vc-brain/frontend-next
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open `http://localhost:5173/inbox`. The frontend proxies `/api/*` to `BACKEND_URL`, which defaults to `http://localhost:8000`.

4. In a third terminal, create the demo fixture applications:

```powershell
Set-Location F:\Founder-Signal
backend\.venv\Scripts\python.exe scripts\seed_fixtures.py
```

The seed command prints the generated IDs. It creates application records only; submit the same payload through `POST /api/applications` when a live scoring run is required. This keeps fixture creation deterministic and avoids hidden LLM calls.

## Environment Variables

Backend variables are documented in `backend/.env.example`.

- Required for persisted local use: `DATABASE_URL`, `DATABASE_SYNC_URL`.
- Required for live scoring: `OPENAI_API_KEY`.
- Optional enrichment: `GITHUB_TOKEN`, `PRODUCTHUNT_TOKEN`.
- Optional tracing: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`; set `LANGFUSE_ENABLED=false` for an offline demo.
- Frontend: `BACKEND_URL` and optional `NEXT_PUBLIC_LANGFUSE_HOST` are documented in `vc-brain/frontend-next/.env.example`.

Without optional enrichment credentials, the pipeline retains founder-provided evidence and labels unavailable external evidence explicitly. Without Postgres, the health endpoint remains available but inbox and memo routes cannot serve data.

## Demo Fixtures

- `Jane Doe / StealthCo`: cold-start example. Show the wide confidence band, cold-start banner, and missing cap table/financials callouts.
- `Bob Smith / VerifiedCo`: verified-evidence example. Open the memo and inspect citation chips and source links.
- `Carol Wu / ContradictedCo`: contradiction example. Show the red contradicted claim state and open-contradictions section.

Use `DEMO_SCRIPT.md` for the click-by-click live walkthrough.

## Verification

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest

Set-Location ..\vc-brain\frontend-next
npm run build
```

The static C5 guard can also be run directly:

```powershell
Set-Location F:\Founder-Signal
backend\.venv\Scripts\python.exe scripts\check_toolless_boundary.py
```
