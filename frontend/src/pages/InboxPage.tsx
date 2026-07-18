/** InboxPage — list of compact cards + compound query search box (spec §9.1 + §9.3 + §9.4). */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, AlertCircle, SlidersHorizontal } from "lucide-react";
import Layout from "../components/Layout";
import FounderCard from "../components/FounderCard";
import { Button, Input, Badge } from "../components/ui";
import { api, type QueryMatch } from "../lib/api";
import { cn } from "../lib/utils";

export default function InboxPage() {
  const [search, setSearch] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [sector, setSector] = useState("");
  const [geography, setGeography] = useState("");
  const [recFilter, setRecFilter] = useState("");
  const [coldStartOnly, setColdStartOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Inbox query — refreshes when filters change
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

  // Compound query — only fires when user submits
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
    <Layout>
      <div className="px-8 py-6 max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Inbox</h1>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
            Sorted by overall conviction. {data?.total ?? 0} founders.
          </p>
        </header>

        {/* Compound query search box (spec §9.4) */}
        <form onSubmit={onSubmit} className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted-foreground)]" />
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
          <p className="text-[10px] text-[var(--color-muted-foreground)] mt-1.5 ml-1">
            Multi-attribute reasoning: this is NOT manual filter toggles — the query decomposes into
            atomic attributes and runs a single SQL pass against all claims.
          </p>
        </form>

        {/* Filter bar (manual filters) */}
        <div className="flex items-center gap-2 mb-6">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
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
          <div className="mb-6 p-4 border border-[var(--color-border)] rounded-md bg-[var(--color-card)] grid grid-cols-4 gap-3">
            <label className="text-xs">
              <span className="text-[var(--color-muted-foreground)]">Sector</span>
              <Input value={sector} onChange={(e) => setSector(e.target.value)} placeholder="AI infra" />
            </label>
            <label className="text-xs">
              <span className="text-[var(--color-muted-foreground)]">Geography (ISO-2)</span>
              <Input value={geography} onChange={(e) => setGeography(e.target.value.toUpperCase())} placeholder="DE" maxLength={2} />
            </label>
            <label className="text-xs">
              <span className="text-[var(--color-muted-foreground)]">Recommendation</span>
              <select
                value={recFilter}
                onChange={(e) => setRecFilter(e.target.value)}
                className="h-9 w-full rounded-md border border-[var(--color-input)] bg-transparent px-3 text-sm"
              >
                <option value="">any</option>
                <option value="fast_pass">fast_pass</option>
                <option value="deep_dive">deep_dive</option>
                <option value="pass">pass</option>
                <option value="reject">reject</option>
              </select>
            </label>
            <label className="text-xs flex flex-col">
              <span className="text-[var(--color-muted-foreground)]">Cold-start</span>
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

        {/* Compound query results */}
        {submittedQuery && (
          <section className="mb-8">
            <h2 className="text-sm font-semibold mb-3 text-[var(--color-muted-foreground)] uppercase tracking-wide">
              Compound query results
            </h2>
            {queryResult.isLoading && (
              <div className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
                <Loader2 className="w-4 h-4 animate-spin" /> Decomposing query…
              </div>
            )}
            {queryResult.error && (
              <div className="flex items-center gap-2 text-sm text-[var(--color-destructive)]">
                <AlertCircle className="w-4 h-4" /> {(queryResult.error as Error).message}
              </div>
            )}
            {queryResult.data && (
              <div className="space-y-3">
                <div className="text-xs text-[var(--color-muted-foreground)]">
                  Decomposed into{" "}
                  <span className="font-medium text-[var(--color-foreground)]">
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
                  <p className="text-sm text-[var(--color-muted-foreground)]">
                    No founders matched all attributes.
                  </p>
                ) : (
                  queryResult.data.matches.map((m) => <QueryMatchRow key={m.founder_id} match={m} />)
                )}
              </div>
            )}
          </section>
        )}

        {/* Inbox cards */}
        <section>
          {isLoading && (
            <div className="flex items-center justify-center py-12 text-sm text-[var(--color-muted-foreground)]">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading inbox…
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 p-4 rounded-md border border-[var(--color-destructive)]/30 bg-[var(--color-destructive)]/5 text-sm text-[var(--color-destructive)]">
              <AlertCircle className="w-4 h-4" />
              {(error as Error).message}
            </div>
          )}
          {data && data.cards.length === 0 && !submittedQuery && (
            <div className="text-center py-12">
              <p className="text-sm text-[var(--color-muted-foreground)]">
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
    </Layout>
  );
}

function QueryMatchRow({ match }: { match: QueryMatch }) {
  return (
    <a
      href={`/founders/${match.founder_id}`}
      className="block p-3 rounded-md border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-accent)] transition-colors"
    >
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium">{match.founder_name}</span>
          {match.company_name && (
            <span className="text-sm text-[var(--color-muted-foreground)] ml-2">{match.company_name}</span>
          )}
        </div>
        <span className="font-mono text-sm font-semibold">{match.score.toFixed(0)}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {match.matched_attributes.map((attr, i) => (
          <Badge key={i} variant="outline" className="text-[10px] text-[var(--color-verified)] border-[var(--color-verified)]/30">
            ✓ {attr}
          </Badge>
        ))}
      </div>
    </a>
  );
}
