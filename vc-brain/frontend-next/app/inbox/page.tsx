"use client";
import { useState, useEffect, Suspense, lazy } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, AlertCircle, SlidersHorizontal } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { FounderCard } from "@/components/founder/founder-card";
import { Button, Input, Badge, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { QueryMatch } from "@/lib/types";
import { AgentWorkflowPanel, ViewAgentWorkflowButton } from "@/components/agents/agent-workflow";

// Lazy-load SignalRadar so it never blocks the founder card list
const SignalRadarLazy = lazy(() =>
  import("@/components/radar/signal-radar").then((m) => ({ default: m.SignalRadar }))
);
const { SignalRadarErrorBoundary } = require("@/components/radar/signal-radar");

export default function InboxPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-24 text-sm text-text-muted">Loading…</div>}>
      <InboxContent />
    </Suspense>
  );
}

function InboxContent() {
  const searchParams = useSearchParams();
  const [search, setSearch] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [sector, setSector] = useState("");
  const [geography, setGeography] = useState("");
  const [recFilter, setRecFilter] = useState("");
  const [coldStartOnly, setColdStartOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [showWorkflow, setShowWorkflow] = useState(false);

  // Read ?q= param from URL (set by the hero/landing page)
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !submittedQuery) {
      setSearch(q);
      setSubmittedQuery(q);
    }
  }, [searchParams, submittedQuery]);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["inbox", sector, geography, recFilter, coldStartOnly],
    queryFn: () =>
      api.getInbox({
        sector: sector || undefined,
        geography: geography || undefined,
        recommendation: recFilter || undefined,
        cold_start: coldStartOnly ? true : undefined,
        limit: 50,
      }),
  });

  const queryResult = useQuery({
    queryKey: ["query", submittedQuery],
    queryFn: () => api.query(submittedQuery),
    enabled: submittedQuery.length > 0,
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedQuery(search.trim());
  };

  const clearSearch = () => {
    setSearch("");
    setSubmittedQuery("");
  };

  return (
    <AppShell>
      <div className="max-w-6xl px-4 py-5 sm:mx-auto sm:px-8 sm:py-6">
        <header className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Inbox</h1>
          <p className="text-sm text-text-muted mt-1">
            Sorted by overall conviction. {isLoading ? "Loading founders..." : `${data?.total ?? 0} founders.`}
          </p>
        </header>

        <form onSubmit={onSubmit} className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
            <Input
              aria-label="Search founders with a compound query"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder='Compound query: "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator"'
              className="pl-10 pr-24"
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {submittedQuery && (
                <Button type="button" size="sm" variant="ghost" onClick={clearSearch}>
                  Clear
                </Button>
              )}
              <Button type="submit" size="sm" disabled={!search.trim()}>
                Search
              </Button>
            </div>
          </div>
          <p className="text-[10px] text-text-subtle mt-1.5 ml-1">
            Multi-attribute reasoning: NOT manual filter toggles — decomposes into atomic
            attributes and runs a single SQL pass against all claims.
          </p>
        </form>

        <div className="flex items-center gap-2 mb-6">
          <Button size="sm" variant="outline" onClick={() => setShowFilters(!showFilters)}>
            <SlidersHorizontal className="w-3 h-3 mr-1.5" />
            Filters
          </Button>
          <ViewAgentWorkflowButton onClick={() => setShowWorkflow(!showWorkflow)} label={showWorkflow ? "Hide Agents" : "View Agent Workflow"} />
          {recFilter && <FilterChip label={recFilter} onClear={() => setRecFilter("")} />}
          {coldStartOnly && <FilterChip label="cold-start only" onClear={() => setColdStartOnly(false)} />}
          {sector && <FilterChip label={`sector: ${sector}`} onClear={() => setSector("")} />}
          {geography && <FilterChip label={`geo: ${geography}`} onClear={() => setGeography("")} />}
        </div>

        {showFilters && (
          <div className="metal-panel mb-6 grid grid-cols-1 gap-3 rounded-sm p-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="text-xs">
              <span className="text-text-muted">Sector</span>
              <Input value={sector} onChange={(e) => setSector(e.target.value)} placeholder="AI infra" />
            </label>
            <label className="text-xs">
              <span className="text-text-muted">Geography (ISO-2)</span>
              <Input
                value={geography}
                onChange={(e) => setGeography(e.target.value.toUpperCase())}
                placeholder="DE"
                maxLength={2}
              />
            </label>
            <label className="text-xs">
              <span className="text-text-muted">Recommendation</span>
              <select
                value={recFilter}
                onChange={(e) => setRecFilter(e.target.value)}
                className="metal-input h-9 w-full rounded-sm border border-border-strong px-3 text-sm text-text-primary"
              >
                <option value="">any</option>
                <option value="fast_pass">fast_pass</option>
                <option value="deep_dive">deep_dive</option>
                <option value="pass">pass</option>
                <option value="reject">reject</option>
              </select>
            </label>
            <div className="text-xs flex flex-col">
              <span className="text-text-muted">Cold-start</span>
              <label className="flex items-center gap-2 h-9">
                <input
                  type="checkbox"
                  checked={coldStartOnly}
                  onChange={(e) => setColdStartOnly(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">cold-start only</span>
              </label>
            </div>
          </div>
        )}

        {submittedQuery && (
          <section className="mb-8">
            <h2 className="text-sm font-bold mb-3 text-text-muted uppercase tracking-wide">
              Compound query results
            </h2>
            {queryResult.isLoading && (
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <Loader2 className="w-4 h-4 animate-spin" /> Decomposing query…
              </div>
            )}
            {queryResult.error && (
              <div className="flex items-center gap-2 text-sm text-error">
                <AlertCircle className="w-4 h-4" /> {(queryResult.error as Error).message}
                <Button size="sm" variant="outline" onClick={() => queryResult.refetch()}>Retry</Button>
              </div>
            )}
            {queryResult.data && (
              <div className="space-y-3">
                <div className="text-xs text-text-muted">
                  Decomposed into{" "}
                  <span className="font-bold text-text-primary">
                    {queryResult.data.decomposed_attributes.length}
                  </span>{" "}
                  attributes:{" "}
                  {queryResult.data.decomposed_attributes.map((a, i) => (
                    <Badge key={i} variant="outline" className="mx-0.5">
                      {a}
                    </Badge>
                  ))}
                </div>
                {queryResult.data.matches.length === 0 ? (
                  <p className="text-sm text-text-muted">No founders matched all attributes.</p>
                ) : (
                  queryResult.data.matches.map((m) => <QueryMatchRow key={m.founder_id} match={m} />)
                )}
              </div>
            )}
          </section>
        )}

        <section>
          {isLoading && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" aria-label="Loading founders">
              {Array.from({ length: 6 }).map((_, i) => <FounderCardSkeleton key={i} />)}
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 p-4 rounded-md border border-error-border bg-error-bg text-sm text-error">
              <AlertCircle className="w-4 h-4" />
              {(error as Error).message}
              <Button size="sm" variant="outline" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          )}
          {data && data.cards.length === 0 && (
            <div className="text-center py-12">
              <p className="text-sm text-text-muted">
                {submittedQuery
                  ? "No founders match the current inbox filters. Clear a filter or broaden the search."
                  : "No applications in the inbox yet. New applications will appear here as their pipeline run begins."}
              </p>
            </div>
          )}
          {data && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {data.cards.map((card) => (
                <FounderCard key={card.founder_id} card={card} />
              ))}
            </div>
          )}
        </section>

        {/* Agent Workflow Panel (collapsible) */}
        {showWorkflow && (
          <section className="mt-6" aria-label="Agent workflow visualization">
            <AgentWorkflowPanel onClose={() => setShowWorkflow(false)} />
          </section>
        )}

        <section className="mt-10" aria-label="Pipeline telemetry">
          <div className="mb-3 flex items-end justify-between gap-4">
            <div><p className="technical-label">Secondary operator view</p><h2 className="text-lg font-bold text-text-primary">Live Signal Radar</h2></div>
            <p className="max-w-sm text-right text-xs text-text-muted">Live agent activity and permitted source signals. The investment queue above remains the primary decision surface.</p>
          </div>
          <SignalRadarErrorBoundary>
            <Suspense fallback={<div className="radar-console radar-console--loading">Loading signal telemetry...</div>}>
              <SignalRadarLazy />
            </Suspense>
          </SignalRadarErrorBoundary>
        </section>
      </div>
    </AppShell>
  );
}

function FilterChip({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <button
      type="button"
      onClick={onClear}
      className="inline-flex items-center rounded-full bg-elevated px-2 py-0.5 text-[10px] font-medium text-text-secondary transition-colors hover:bg-modal focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
      aria-label={`Clear ${label} filter`}
    >
      {label} ×
    </button>
  );
}

function FounderCardSkeleton() {
  return (
    <div className="metal-panel rounded-sm p-4 space-y-4">
      <div className="flex justify-between"><Skeleton className="h-4 w-32" /><Skeleton className="h-4 w-14" /></div>
      <Skeleton className="h-px w-full" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-5/6" />
      <Skeleton className="h-3 w-4/6" />
      <Skeleton className="h-7 w-24" />
    </div>
  );
}

function QueryMatchRow({ match }: { match: QueryMatch }) {
  return (
    <a
      href={`/founders/${match.founder_id}`}
      className="metal-panel metal-panel--interactive block rounded-sm p-3"
    >
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-bold text-text-primary">{match.founder_name}</span>
          {match.company_name && (
            <span className="text-sm text-text-muted ml-2">{match.company_name}</span>
          )}
        </div>
        <span className="font-mono text-sm font-bold" data-numeric>
          {match.score.toFixed(0)}
        </span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {match.matched_attributes.map((attr, i) => (
          <Badge key={i} variant="success" className="text-[10px]">
            ✓ {attr}
          </Badge>
        ))}
      </div>
    </a>
  );
}
