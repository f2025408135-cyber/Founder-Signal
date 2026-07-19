/** FounderDetailPage — full memo view per spec §9.2.

Layout:
- Single-column scrollable document, max-width 760px, centered.
- Left rail: section nav with anchor links (collapsible).
- Right rail: Pipeline Trace panel (collapsible).
- Sticky header: company name + recommendation pill + conviction score.
- Cold-start banner at the very top if cold_start==true.
- Memo body rendered via MemoView with EvidenceChip substitution.
- Score history sparkline.
*/
import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2, AlertCircle, ChevronRight, ChevronDown } from "lucide-react";
import Layout from "../components/Layout";
import MemoView from "../components/MemoView";
import PipelineTrace from "../components/PipelineTrace";
import { Badge, Card, Button } from "../components/ui";
import { api } from "../lib/api";
import { cn, recommendationColor, timeAgo } from "../lib/utils";

export default function FounderDetailPage() {
  const { founderId } = useParams<{ founderId: string }>();
  const [showSectionNav, setShowSectionNav] = useState(true);

  const { data: memo, isLoading, error } = useQuery({
    queryKey: ["founder-memo", founderId],
    queryFn: () => api.getFounderMemo(founderId!),
    enabled: !!founderId,
  });

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-24 text-sm text-[var(--color-muted-foreground)]">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading memo…
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="px-8 py-6 max-w-3xl mx-auto">
          <Link to="/" className="inline-flex items-center text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] mb-4">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to inbox
          </Link>
          <Card className="p-5 border-[var(--color-destructive)]/30 bg-[var(--color-destructive)]/5">
            <div className="flex items-center gap-2 text-[var(--color-destructive)]">
              <AlertCircle className="w-4 h-4" />
              <span className="font-medium text-sm">Failed to load memo</span>
            </div>
            <p className="text-xs mt-2 text-[var(--color-muted-foreground)]">
              {(error as Error).message}
            </p>
            <p className="text-xs mt-2 text-[var(--color-muted-foreground)]">
              The pipeline may not have completed for this founder. Submit an application first via POST /api/applications.
            </p>
          </Card>
        </div>
      </Layout>
    );
  }

  if (!memo) return null;

  const agg = memo.aggregator_output;
  const recColor = recommendationColor(agg.overall_recommendation);
  // Use the LATEST snapshot's cold_start flag (score_history is sorted oldest-first
  // per founders.py:181 — `order_by(FounderScoreSnapshot.computed_at.asc())`).
  // Spec §9.2: banner renders when the current run is cold-start.
  const latestSnapshot = memo.score_history.length > 0
    ? memo.score_history[memo.score_history.length - 1]
    : null;
  const isColdStart = latestSnapshot?.cold_start === true;

  // Extract section headings from memo for the nav rail
  const sections = agg.memo_markdown
    .split("\n")
    .filter((l) => l.startsWith("## "))
    .map((l) => l.slice(3).trim());

  return (
    <Layout>
      <div className="flex h-full">
        {/* Left rail: section nav */}
        <aside className="w-48 border-r border-[var(--color-border)] bg-[var(--color-card)] flex flex-col">
          <div className="px-3 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
              Sections
            </span>
            <button onClick={() => setShowSectionNav(!showSectionNav)}>
              {showSectionNav ? (
                <ChevronDown className="w-3 h-3 text-[var(--color-muted-foreground)]" />
              ) : (
                <ChevronRight className="w-3 h-3 text-[var(--color-muted-foreground)]" />
              )}
            </button>
          </div>
          {showSectionNav && (
            <nav className="flex-1 overflow-auto px-2 py-2 space-y-0.5">
              <Link
                to="/"
                className="flex items-center text-xs text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] py-1 px-2"
              >
                <ArrowLeft className="w-3 h-3 mr-1" /> Inbox
              </Link>
              {sections.map((s) => (
                <a
                  key={s}
                  href={`#${s.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
                  className="block text-xs text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] py-1 px-2 rounded truncate"
                  title={s}
                >
                  {s}
                </a>
              ))}
            </nav>
          )}
        </aside>

        {/* Center: memo */}
        <main className="flex-1 overflow-auto">
          {/* Sticky header */}
          <div className="sticky top-0 z-10 bg-[var(--color-background)]/95 backdrop-blur border-b border-[var(--color-border)] px-6 py-3">
            <div className="max-w-3xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h1 className="text-base font-semibold">{memo.company_name || memo.founder_name}</h1>
                <span
                  className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-medium",
                    recColor
                  )}
                >
                  {agg.overall_recommendation}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span>
                  <span className="font-mono font-semibold">{agg.overall_conviction.toFixed(0)}</span>
                  <span className="text-[var(--color-muted-foreground)]">/100</span>
                </span>
                <span className="text-[var(--color-muted-foreground)]">
                  {timeAgo(agg.computed_at)}
                </span>
              </div>
            </div>
          </div>

          {/* Memo body */}
          <div className="px-6 py-8 max-w-3xl mx-auto">
            {/* Founder identity strip — photo + name + education + github.
                Minimal addition to existing UI; uses demo-only fields surfaced
                from founder.bio_text JSON (see scripts/seed_dataset.py). */}
            <div className="flex items-center gap-4 mb-6 p-3 rounded-md border border-[var(--color-border)] bg-[var(--color-card)]">
              {memo.photo_url && (
                <img
                  src={memo.photo_url}
                  alt={memo.founder_name}
                  className="w-16 h-16 rounded-full object-cover border border-[var(--color-border)] flex-shrink-0"
                  onError={(e) => {
                    // If the image fails to load (e.g. offline SVG path mismatch),
                    // hide it so we don't show a broken-image icon.
                    (e.currentTarget as HTMLImageElement).style.display = "none";
                  }}
                />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-base font-semibold">{memo.founder_name}</h2>
                  {memo.categories.map((c) => (
                    <span
                      key={c}
                      className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wider border border-[var(--color-border)] text-[var(--color-muted-foreground)]"
                    >
                      {c.replace("_", " ")}
                    </span>
                  ))}
                </div>
                {memo.prior_experience && (
                  <p className="text-xs text-[var(--color-muted-foreground)] mt-1">
                    {memo.prior_experience}
                  </p>
                )}
                {memo.education && (
                  <div className="flex items-center gap-2 mt-2">
                    {memo.university_image_url && (
                      <img
                        src={memo.university_image_url}
                        alt={memo.education.university}
                        className="w-8 h-8 rounded object-cover border border-[var(--color-border)] flex-shrink-0"
                        onError={(e) => {
                          (e.currentTarget as HTMLImageElement).style.display = "none";
                        }}
                      />
                    )}
                    <span className="text-xs text-[var(--color-muted-foreground)]">
                      {memo.education.degree}, {memo.education.university} ({memo.education.year})
                    </span>
                  </div>
                )}
                {memo.github_profile && (
                  <p className="text-xs mt-1 font-mono text-[var(--color-muted-foreground)]">
                    github: {memo.github_profile.username} · {memo.github_profile.stars}★ · {memo.github_profile.primary_language}
                  </p>
                )}
              </div>
            </div>

            {/* Cold-start banner is rendered by MemoView from memo_markdown
                (aggregator.py:222-225 embeds it as a blockquote at the top).
                Per spec §9.2: RED border, exact spec text. We do NOT render a
                duplicate banner here — MemoView handles it. */}

            {/* Rescore reason */}
            {memo.rescore_reason && (
              <div className="mb-4 text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
                cache: {memo.rescore_reason}
              </div>
            )}

            {/* Memo markdown */}
            <MemoView markdown={agg.memo_markdown} claims={memo.claims} />

            {/* Score history sparkline */}
            <ScoreHistory history={memo.score_history} />

            {/* Open contradictions */}
            {agg.open_contradictions.length > 0 && (
              <Card className="mt-6 p-4 border-[var(--color-contradicted)]/30 bg-[var(--color-contradicted)]/5">
                <h3 className="text-sm font-semibold text-[var(--color-contradicted)] mb-2">
                  Open Contradictions ({agg.open_contradictions.length})
                </h3>
                <ul className="space-y-1">
                  {agg.open_contradictions.map((c, i) => (
                    <li key={i} className="text-xs text-[var(--color-muted-foreground)]">
                      • {c}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {/* Missing sections */}
            {agg.missing_required_sections.length > 0 && (
              <Card className="mt-4 p-4 border-[var(--color-destructive)]/30 bg-[var(--color-destructive)]/5">
                <h3 className="text-sm font-semibold text-[var(--color-destructive)] mb-2">
                  Missing Required Sections
                </h3>
                <ul className="space-y-1">
                  {agg.missing_required_sections.map((s) => (
                    <li key={s} className="text-xs">
                      • {s.replace(/_/g, " ")}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {agg.missing_optional_sections.length > 0 && (
              <Card className="mt-4 p-4">
                <h3 className="text-sm font-semibold mb-2">Missing Optional Sections</h3>
                <div className="flex flex-wrap gap-1.5">
                  {agg.missing_optional_sections.map((s) => (
                    <Badge key={s} variant="outline" className="text-[10px]">
                      {s.replace(/_/g, " ")}
                    </Badge>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </main>

        {/* Right rail: Pipeline Trace (spec §9.2) */}
        <aside className="w-80 border-l border-[var(--color-border)] bg-[var(--color-card)] p-4 overflow-auto">
          <PipelineTrace traceId={agg.trace_id} />

          {/* Next actions */}
          <div className="mt-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)] mb-2">
              Next Actions
            </h3>
            <ul className="space-y-1.5">
              {agg.next_actions.map((a, i) => (
                <li key={i} className="text-xs flex items-start gap-2">
                  <span className="text-[var(--color-primary)] mt-0.5">▸</span>
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Latency / metadata */}
          <div className="mt-6 text-[10px] text-[var(--color-muted-foreground)] space-y-1">
            <div>founder_id: <code className="font-mono break-all">{memo.founder_id}</code></div>
            <div>computed_at: {new Date(agg.computed_at).toLocaleString()}</div>
            <div>evidence_coverage: <span className="font-mono">{agg.evidence_coverage.toFixed(2)}</span></div>
            <div>thesis_fit_score: <span className="font-mono">{agg.thesis_fit_score.toFixed(1)}</span></div>
          </div>
        </aside>
      </div>
    </Layout>
  );
}

function ScoreHistory({ history }: { history: Array<{ computed_at: string; score: number; trend: string; trigger: string; cold_start: boolean }> }) {
  if (history.length === 0) return null;
  const maxScore = Math.max(...history.map((h) => h.score), 100);
  return (
    <Card className="mt-6 p-4">
      <h3 className="text-sm font-semibold mb-3">Score History ({history.length} snapshots)</h3>
      <div className="flex items-end gap-1 h-24">
        {history.slice(-15).map((h, i) => (
          <div key={i} className="flex-1 flex flex-col items-center justify-end" title={`${h.score.toFixed(1)} - ${h.trigger}`}>
            <div
              className={cn(
                "w-full rounded-t-sm min-h-[2px]",
                h.cold_start ? "bg-[var(--color-cold-start)]" : "bg-[var(--color-primary)]"
              )}
              style={{ height: `${(h.score / maxScore) * 100}%` }}
            />
            <div className="text-[9px] text-[var(--color-muted-foreground)] mt-1 -rotate-45 origin-center whitespace-nowrap">
              {new Date(h.computed_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-3 text-[10px] text-[var(--color-muted-foreground)]">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 bg-[var(--color-primary)] rounded-sm" /> verified
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 bg-[var(--color-cold-start)] rounded-sm" /> cold-start
        </span>
      </div>
    </Card>
  );
}
