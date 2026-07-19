"use client";
import { useState, useEffect, Suspense, lazy } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, AlertCircle, SlidersHorizontal } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { FounderCard } from "@/components/founder/founder-card";
import { Button, Input, Badge } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { QueryMatch } from "@/lib/types";

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

  // Read ?q= param from URL (set by the hero/landing page)
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !submittedQuery) {
      setSearch(q);
      setSubmittedQuery(q);
    }
  }, [searchParams, submittedQuery]);

  const { data, isLoading, error } = useQuery({
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
      <div className="px-8 py-6 max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Inbox</h1>
          <p className="text-sm text-text-muted mt-1">
            Sorted by overall conviction. {data?.total ?? 0} founders.
          </p>
        </header>

        <form onSubmit={onSubmit} className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
            <Input
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
          {recFilter && (
            <Badge variant="secondary" className="cursor-pointer" onClick={() => setRecFilter("")}>
              {recFilter} ×
            </Badge>
          )}
          {coldStartOnly && (
            <Badge variant="secondary" className="cursor-pointer" onClick={() => setColdStartOnly(false)}>
              cold-start only ×
            </Badge>
          )}
          {sector && (
            <Badge variant="secondary" className="cursor-pointer" onClick={() => setSector("")}>
              sector: {sector} ×
            </Badge>
          )}
          {geography && (
            <Badge variant="secondary" className="cursor-pointer" onClick={() => setGeography("")}>
              geo: {geography} ×
            </Badge>
          )}
        </div>

        {showFilters && (
          <div className="mb-6 p-4 border border-border rounded-md bg-card grid grid-cols-4 gap-3">
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
                className="h-9 w-full rounded-md border border-border-strong bg-card px-3 text-sm text-text-primary"
              >
                <option value="">any</option>
                <option value="fast_pass">fast_pass</option>
                <option value="deep_dive">deep_dive</option>
                <option value="pass">pass</option>
                <option value="reject">reject</option>
              </select>
            </label>
            <label className="text-xs flex flex-col">
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
            </label>
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

        {/* Signal Radar — live pipeline activity feed */}
        <SignalRadarErrorBoundary>
          <Suspense fallback={<div className="rounded-lg p-4 mb-6" style={{ background: "#0a0908", border: "1px solid #4a3a1a33" }}><div className="font-mono text-[10px]" style={{ color: "#4a3a1a" }}>Loading Signal Radar...</div></div>}>
            <div className="mb-6">
              <SignalRadarLazy />
            </div>
          </Suspense>
        </SignalRadarErrorBoundary>

        <section>
          {isLoading && (
            <div className="flex items-center justify-center py-12 text-sm text-text-muted">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading inbox…
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 p-4 rounded-md border border-error-border bg-error-bg text-sm text-error">
              <AlertCircle className="w-4 h-4" />
              {(error as Error).message}
            </div>
          )}
          {data && data.cards.length === 0 && !submittedQuery && (
            <div className="text-center py-12">
              <p className="text-sm text-text-muted">
                No applications in the inbox yet. Submit one via POST /api/applications.
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
      </div>
    </AppShell>
  );
}

function QueryMatchRow({ match }: { match: QueryMatch }) {
  return (
    <a
      href={`/founders/${match.founder_id}`}
      className="block p-3 rounded-md border border-border bg-card hover:bg-elevated transition-colors"
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
