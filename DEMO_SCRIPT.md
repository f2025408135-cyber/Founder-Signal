# Founder Signal Demo Script

Duration: 4 minutes. The narrative is **thesis → decision → evidence → uncertainty → operating system**.

## Before The Room

1. For a live run, start the backend and frontend as described in `README.md`, confirm `/health`, and verify `/api/applications/inbox` has cards.
2. For a deterministic UI demo without Docker, run `backend/.venv/Scripts/python.exe -m uvicorn scripts.demo_api:app --port 8001` from the repository root and set `BACKEND_URL=http://localhost:8001` in `vc-brain/frontend-next/.env.local`.
3. Open `http://localhost:5173/hero` and keep `http://localhost:5173/inbox` ready in another tab.

## 0:00 - Frame The Investment Thesis

1. Open **Fin** and use one suggestion chip to show the conversational sourcing surface.
2. Point to the live Thesis Capture panel: Fin turns natural-language intent into sectors, stage, geography, check size, ownership, and risk posture.
3. State the principle: no pipeline status is claimed until the backend confirms it. The deal queue is the source of truth.
4. Use **Skip to dashboard**.

## 0:35 - Make A Decision First

1. In the Inbox, point out the active thesis in the sidebar and the queue sorted by Conviction.
2. Open **VerifiedCo**.
3. Start at the **Decision Brief**, not the long memo. Show the recommendation, four independent axes, evidence coverage, confidence range, diligence flags, and next actions in one screen.
4. State explicitly: Conviction is not an average of the axes; a weak axis remains visible.

## 1:20 - Prove The Decision

1. In **The Verdict**, show the Bull Case is drawn from verified claims and cited SWOT evidence.
2. Click a `[verified]` citation. Show its claim text, source, validator status, confidence, and traceability drawer.
3. Explain that the evidence ledger distinguishes verified, contradicted, unverifiable, missing, and still-unvalidated claims. It does not silently turn uncertainty into a score.

## 2:00 - Show Honest Uncertainty

1. Return to Inbox and open **StealthCo**.
2. In the Decision Brief, show the wide confidence range and cold-start warning beside the recommendation.
3. Show the empty Bull/Bear state only where the validator has no material evidence; point out the memo’s explicit Cap Table and Financials disclosure requests.
4. Explain the differentiator: cold-start founders are not punished or falsely precision-scored. The recommendation routes them to deeper diligence.

## 2:45 - Show The System Can Argue Against Itself

1. Open **ContradictedCo**.
2. Show the Bear Case, contradiction count, and cited contradictory claim.
3. Open the evidence drawer and state that a contradiction is retained as a first-class decision input rather than being hidden by a headline score.

## 3:20 - Close On Operating Discipline

1. Return to Inbox and scroll to **Live Signal Radar**. It is secondary telemetry, not a made-up performance metric: it only displays permitted pipeline events from the current session.
2. Open **Sourcing Map**. Explain that it maps evidence channels to founders; it intentionally does not claim institution relationships that the current data does not prove.
3. Close with the evaluation mapping:
   - cold-start confidence handling and no fast pass: B1/C4;
   - claim-level validation and contradiction detection: B4/C2;
   - cited memo, evidence coverage, and tool-less synthesis: B5/C3/C5;
   - missing-data callouts: C6;
   - cards, citation drawers, traceability, and operating views: D2/D3/D6.
