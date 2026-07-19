"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ArrowLeft, Loader2, AlertCircle, ChevronRight, ChevronDown } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { MemoView } from "@/components/memo/memo-view";
import { Verdict } from "@/components/memo/verdict";
import { PipelineTrace } from "@/components/trace/pipeline-trace";
import { Badge, Card, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { cn, recommendationColor, timeAgo } from "@/lib/utils";

export default function FounderDetailPage() {
  const params = useParams<{ founderId: string }>();
  const founderId = params?.founderId;
  const [showSectionNav, setShowSectionNav] = useState(true);

  const { data: memo, isLoading, error } = useQuery({
    queryKey: ["founder-memo", founderId],
    queryFn: () => api.getFounderMemo(founderId!),
    enabled: !!founderId,
  });

  if (isLoading) {
    return (
      <AppShell>
        <div className="px-8 py-6 max-w-3xl mx-auto space-y-5" aria-label="Loading investment memo">
          <Skeleton className="h-8 w-2/5" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="px-8 py-6 max-w-3xl mx-auto">
          <Link
            href="/inbox"
            className="inline-flex items-center text-sm text-text-muted hover:text-text-primary mb-4"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to inbox
          </Link>
          <Card className="p-5 border-error-border bg-error-bg">
            <div className="flex items-center gap-2 text-error">
              <AlertCircle className="w-4 h-4" />
              <span className="font-bold text-sm">Failed to load memo</span>
            </div>
            <p className="text-xs mt-2 text-text-muted">{(error as Error).message}</p>
            <p className="text-xs mt-2 text-text-muted">
              The pipeline may not have completed for this founder. Submit an application first via
              POST /api/applications.
            </p>
          </Card>
        </div>
      </AppShell>
    );
  }

  if (!memo?.aggregator_output) {
    return (
      <AppShell>
        <div className="px-8 py-6 max-w-3xl mx-auto">
          <Card className="p-5 border-warning-border bg-warning-bg">
            <h1 className="text-sm font-bold text-text-primary">Memo is still processing</h1>
            <p className="mt-2 text-xs text-text-secondary">
              Evidence is being collected and validated. Return to the inbox and try this founder again shortly.
            </p>
            <Link href="/inbox" className="mt-4 inline-flex text-xs text-accent underline">Back to inbox</Link>
          </Card>
        </div>
      </AppShell>
    );
  }

  const agg = memo.aggregator_output;
  const recColor = recommendationColor(agg.overall_recommendation);
  const latestSnapshot =
    memo.score_history.length > 0
      ? memo.score_history[memo.score_history.length - 1]
      : null;
  const isColdStart = latestSnapshot?.cold_start === true;

  const sections = agg.memo_markdown
    .split("\n")
    .filter((l) => l.startsWith("## "))
    .map((l) => l.slice(3).trim());

  return (
    <AppShell>
      <div className="flex h-full">
        {/* Left rail: section nav */}
          <aside className="hidden w-48 shrink-0 border-r border-border bg-card lg:flex lg:flex-col">
          <div className="px-3 py-3 border-b border-border flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-wider text-text-muted">Sections</span>
            <button
              onClick={() => setShowSectionNav(!showSectionNav)}
              aria-label={showSectionNav ? "Collapse memo sections" : "Expand memo sections"}
              aria-expanded={showSectionNav}
              className="rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
            >
              {showSectionNav ? (
                <ChevronDown className="w-3 h-3 text-text-muted" />
              ) : (
                <ChevronRight className="w-3 h-3 text-text-muted" />
              )}
            </button>
          </div>
          {showSectionNav && (
            <nav className="flex-1 overflow-auto px-2 py-2 space-y-0.5">
              <Link
                href="/inbox"
                className="flex items-center text-xs text-text-muted hover:text-text-primary py-1 px-2"
              >
                <ArrowLeft className="w-3 h-3 mr-1" /> Inbox
              </Link>
              {sections.map((s) => (
                <a
                  key={s}
                  href={`#${s.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
                  className="block text-xs text-text-muted hover:text-text-primary py-1 px-2 rounded truncate"
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
          <div className="glass sticky top-0 z-10 border-b border-border px-6 py-3">
            <div className="max-w-3xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h1 className="text-base font-bold text-text-primary">
                  {memo.company_name || memo.founder_name}
                </h1>
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
                  <span className="font-mono font-bold" data-numeric>
                    {agg.overall_conviction.toFixed(0)}
                  </span>
                  <span className="text-text-muted">/100</span>
                </span>
                <span className="text-text-muted">{timeAgo(agg.computed_at)}</span>
              </div>
            </div>
          </div>

          {/* Memo body */}
          <div className="px-6 py-8 max-w-3xl mx-auto">
            {/* Cold-start banner is rendered by MemoView from memo_markdown (RED border) */}

            {memo.rescore_reason && (
              <div className="mb-4 text-[10px] uppercase tracking-wider text-text-muted">
                cache: {memo.rescore_reason}
              </div>
            )}

            <MemoView markdown={agg.memo_markdown} claims={memo.claims} />

            <Verdict
              key={memo.founder_id}
              founderId={memo.founder_id}
              founderName={memo.founder_name}
              claims={memo.claims}
              memoMarkdown={agg.memo_markdown}
            />

            {/* Score history sparkline */}
            <ScoreHistory history={memo.score_history} />

            {/* Open contradictions */}
            {agg.open_contradictions.length > 0 && (
              <Card className="mt-6 p-4 border-error-border bg-error-bg">
                <h3 className="text-sm font-bold text-error mb-2">
                  Open Contradictions ({agg.open_contradictions.length})
                </h3>
                <ul className="space-y-1">
                  {agg.open_contradictions.map((c, i) => (
                    <li key={i} className="text-xs text-text-secondary">
                      • {c}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {/* Missing required sections */}
            {agg.missing_required_sections.length > 0 && (
              <Card className="mt-4 p-4 border-error-border bg-error-bg">
                <h3 className="text-sm font-bold text-error mb-2">Missing Required Sections</h3>
                <ul className="space-y-1">
                  {agg.missing_required_sections.map((s) => (
                    <li key={s} className="text-xs text-text-secondary">
                      • {s.replace(/_/g, " ")}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {agg.missing_optional_sections.length > 0 && (
              <Card className="mt-4 p-4">
                <h3 className="text-sm font-bold mb-2 text-text-primary">Missing Optional Sections</h3>
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

        {/* Right rail: Pipeline Trace + Next Actions + metadata */}
        <aside className="hidden w-80 shrink-0 overflow-auto border-l border-border bg-card p-4 xl:block">
          <PipelineTrace traceId={agg.trace_id} />

          <div className="mt-6">
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted mb-2">
              Next Actions
            </h3>
            <ul className="space-y-1.5">
              {agg.next_actions.map((a, i) => (
                <li key={i} className="text-xs flex items-start gap-2">
                  <span className="text-accent mt-0.5">▸</span>
                  <span className="text-text-secondary">{a}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-6 text-[10px] text-text-subtle space-y-1">
            <div>
              founder_id: <code className="font-mono break-all">{memo.founder_id}</code>
            </div>
            <div>computed_at: {new Date(agg.computed_at).toLocaleString()}</div>
            <div>
              evidence_coverage:{" "}
              <span className="font-mono" data-numeric>
                {agg.evidence_coverage.toFixed(2)}
              </span>
            </div>
            <div>
              thesis_fit_score:{" "}
              <span className="font-mono" data-numeric>
                {agg.thesis_fit_score.toFixed(1)}
              </span>
            </div>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}

function ScoreHistory({
  history,
}: {
  history: Array<{
    computed_at: string;
    score: number;
    trend: string;
    trigger: string;
    cold_start: boolean;
  }>;
}) {
  if (history.length === 0) return null;
  const maxScore = Math.max(...history.map((h) => h.score), 100);
  return (
    <Card className="mt-6 p-4">
      <h3 className="text-sm font-bold mb-3 text-text-primary">
        Score History ({history.length} snapshots)
      </h3>
      <div className="flex items-end gap-1 h-24">
        {history.slice(-15).map((h, i) => (
          <div
            key={i}
            className="flex-1 flex flex-col items-center justify-end"
            title={`${h.score.toFixed(1)} - ${h.trigger}`}
          >
            <div
              className={cn(
                "w-full rounded-t-sm min-h-[2px]",
                h.cold_start ? "bg-warning" : "bg-accent"
              )}
              style={{ height: `${(h.score / maxScore) * 100}%` }}
            />
            <div className="text-[9px] text-text-subtle mt-1 -rotate-45 origin-center whitespace-nowrap">
              {new Date(h.computed_at).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-3 text-[10px] text-text-muted">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 bg-accent rounded-sm" /> verified
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 bg-warning rounded-sm" /> cold-start
        </span>
      </div>
    </Card>
  );
}
