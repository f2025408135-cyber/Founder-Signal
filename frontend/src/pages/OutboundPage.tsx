/** OutboundPage — list of outbound-sourced founders (spec §9.3).

Per spec §9.3: "table of outbound-identified founders, same compact card UI as inbox but
with a 'sourcing_channel' badge (github | arxiv | ph | hn | accelerator). Clicking opens
the same Founder Detail Page."
*/
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, AlertCircle, RefreshCw, Radio } from "lucide-react";
import Layout from "../components/Layout";
import FounderCard from "../components/FounderCard";
import { Button, Badge } from "../components/ui";
import { api } from "../lib/api";

const CHANNEL_COLOR: Record<string, string> = {
  github: "text-[var(--color-verified)] border-[var(--color-verified)]/30",
  arxiv: "text-[var(--color-deep-dive)] border-[var(--color-deep-dive)]/30",
  ph: "text-[var(--color-cold-start)] border-[var(--color-cold-start)]/30",
  hn: "text-[var(--color-pass)] border-[var(--color-pass)]/30",
  accelerator: "text-[var(--color-primary)] border-[var(--color-primary)]/30",
  external: "text-[var(--color-muted-foreground)] border-[var(--color-border)]",
};

export default function OutboundPage() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["outbound"],
    queryFn: () => api.getOutboundQueue(50),
    refetchInterval: 60_000, // refresh every minute
  });

  const scanMutation = useMutation({
    mutationFn: () => api.triggerOutboundScan(1),
    onSuccess: () => {
      // Poll for new results after a brief delay
      setTimeout(() => qc.invalidateQueries({ queryKey: ["outbound"] }), 2000);
      setTimeout(() => qc.invalidateQueries({ queryKey: ["outbound"] }), 5000);
    },
  });

  return (
    <Layout>
      <div className="px-8 py-6 max-w-6xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Outbound Sourcing</h1>
            <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
              Founders discovered via GitHub trending, arxiv, ProductHunt, and Hacker News.
            </p>
          </div>
          <Button
            onClick={() => scanMutation.mutate()}
            disabled={scanMutation.isPending}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${scanMutation.isPending ? "animate-spin" : ""}`} />
            Run Scan
          </Button>
        </header>

        {scanMutation.isSuccess && (
          <div className="mb-4 p-3 rounded-md border border-[var(--color-verified)]/30 bg-[var(--color-verified)]/5 text-xs">
            <div className="flex items-center gap-2 text-[var(--color-verified)]">
              <Radio className="w-3 h-3" />
              Scan queued (id: <code className="font-mono">{scanMutation.data.scan_id.slice(0, 8)}</code>).
              Results will appear below as signals are detected.
            </div>
          </div>
        )}
        {scanMutation.isError && (
          <div className="mb-4 p-3 rounded-md border border-[var(--color-destructive)]/30 bg-[var(--color-destructive)]/5 text-xs text-[var(--color-destructive)]">
            <AlertCircle className="w-3 h-3 inline mr-1" />
            {(scanMutation.error as Error).message}
          </div>
        )}

        {/* Channel summary */}
        {data && data.founders.length > 0 && (
          <div className="mb-6 flex items-center gap-2 flex-wrap">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)] mr-2">
              Channels:
            </span>
            {Object.entries(
              data.founders.reduce<Record<string, number>>((acc, f) => {
                const ch = (f as { sourcing_channel?: string }).sourcing_channel || "external";
                acc[ch] = (acc[ch] || 0) + 1;
                return acc;
              }, {})
            ).map(([ch, count]) => (
              <Badge
                key={ch}
                variant="outline"
                className={`text-[10px] ${CHANNEL_COLOR[ch] || CHANNEL_COLOR.external}`}
              >
                {ch}: {count}
              </Badge>
            ))}
          </div>
        )}

        {/* Cards */}
        {isLoading && (
          <div className="flex items-center justify-center py-12 text-sm text-[var(--color-muted-foreground)]">
            <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading outbound queue…
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 p-4 rounded-md border border-[var(--color-destructive)]/30 bg-[var(--color-destructive)]/5 text-sm text-[var(--color-destructive)]">
            <AlertCircle className="w-4 h-4" />
            {(error as Error).message}
          </div>
        )}
        {data && data.founders.length === 0 && (
          <div className="text-center py-12">
            <Radio className="w-8 h-8 mx-auto text-[var(--color-muted-foreground)] mb-3" />
            <p className="text-sm text-[var(--color-muted-foreground)]">
              No outbound signals yet. Click "Run Scan" to scan GitHub trending, arxiv, PH, and HN.
            </p>
          </div>
        )}
        {data && data.founders.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.founders.map((f) => (
              <FounderCard
                key={f.founder_id}
                card={f}
                sourcingChannel={(f as { sourcing_channel?: string }).sourcing_channel}
              />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
