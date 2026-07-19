# Founder Signal Demo Script

Duration: 3 to 5 minutes. Start with the services in `README.md` running and wait until all three fixture applications have completed their pipeline runs.

## 0:00 - Open The Inbox

1. Open `http://localhost:5173/inbox`.
2. Point out the distinct Founder, Market, Idea-vs-Market, and Thesis Fit rows. They are displayed independently; the headline Conviction is not an average of those axes.
3. Open `StealthCo` first.

## 0:30 - Cold-Start Differentiator

1. At the top of the StealthCo memo, show the red-bordered `Cold-start founder` banner.
2. Scroll to the score history and point out the visibly wide amber confidence band for the cold-start snapshot.
3. Scroll through `Cap Table` and `Financials & Round Structure` to show the explicit `not disclosed - request from founder` callouts.
4. Explain the decision: insufficient external evidence leads to a deep-dive path rather than a falsely precise fast-pass decision.

## 1:30 - Evidence Trail

1. Return to the Inbox from the memo section rail.
2. Open `VerifiedCo`.
3. Click a green `[verified]` citation chip in the memo.
4. In the right-side drawer, show the claim text, validator status, confidence, source reference, and Langfuse trace link when tracing is configured.
5. Click the GitHub source link to show that the citation resolves to the source repository.
6. Point out that missing evidence uses a labeled state rather than being silently filled in.

## 2:30 - Contradiction And Trace

1. Return to Inbox and open `ContradictedCo`.
2. Find a red `[contradicted]` citation chip and open its drawer.
3. Show the counter-evidence reference and the `Open Contradictions` card below the memo.
4. Open the `Pipeline Trace` rail. Expand a node to show its model, tokens, latency, and result status. If Langfuse is not configured, point out the explicit unavailable state rather than treating it as an error.

## 3:15 - Network And Evaluation Mapping

1. Click `Network` in the sidebar.
2. Select a founder node, then open its memo from the node detail panel.
3. Close on the acceptance-criteria mapping in `docs/BUILD_SPEC.md` section 10:
   - B1/C4: cold-start confidence handling and no fast pass.
   - B4/C2: per-claim validation and contradiction detection.
   - B5/C3/C5: cited memo, evidence coverage, and tool-less synthesis.
   - C6: missing-data callouts.
   - D2/D3/D6: founder cards, citation drawers, and pipeline traceability.

## Demo-Day Checks

1. Verify `GET http://localhost:8000/health` returns `{"status":"ok"...}`.
2. Verify `GET http://localhost:8000/api/applications/inbox` returns fixture cards before opening the browser.
3. If external enrichment is unavailable, use StealthCo to demonstrate the explicit cold-start and missing-evidence experience.
4. Do not refresh scores by opening cards. A view should report a cache hit unless new evidence has arrived.
