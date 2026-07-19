"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Activity, GitBranch, Zap, Snowflake, TrendingUp } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button, Card, Skeleton, Badge } from "@/components/ui/primitives";
import { api } from "@/lib/api";

const NetworkCanvas = dynamic(() => import("@/components/network/network-canvas"), {
  ssr: false,
  loading: () => <NetworkSkeleton />,
});

export default function NetworkPage() {
  const inbound = useQuery({ queryKey: ["inbox", "network"], queryFn: () => api.getInbox({ limit: 50 }) });
  const outbound = useQuery({ queryKey: ["outbound", "network"], queryFn: () => api.getOutboundQueue(50) });
  const isLoading = inbound.isLoading || outbound.isLoading;
  const errors = [inbound.error, outbound.error].filter(Boolean) as Error[];
  const retry = () => { inbound.refetch(); outbound.refetch(); };
  const inboundCards = inbound.data?.cards ?? [];
  const outboundFounders = outbound.data?.founders ?? [];

  // Stats
  const totalFounders = new Set([...inboundCards.map(c => c.founder_id), ...outboundFounders.map(f => f.founder_id)]).size;
  const channels = [...new Set(outboundFounders.map(f => f.sourcing_channel))];
  const coldStartCount = [...inboundCards, ...outboundFounders].filter(f => f.cold_start === true).length;
  const avgConviction = [...inboundCards, ...outboundFounders].filter(f => f.conviction != null).reduce((sum, f, _, arr) => sum + (f.conviction || 0) / arr.length, 0);

  return (
    <AppShell>
      <div className="flex h-full flex-col">
        {/* Header with stats strip */}
        <header className="border-b border-border px-8 py-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="technical-label">Evidence Provenance Graph</p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight text-text-primary">Sourcing Map</h1>
              <p className="mt-1 text-sm text-text-muted">Every founder connected to the channels that surfaced their evidence — trace how signal becomes conviction.</p>
            </div>
            <div className="flex gap-4">
              <StatChip icon={Activity} label="Founders" value={totalFounders} color="#5e6ad2" />
              <StatChip icon={GitBranch} label="Channels" value={channels.length} color="#3ecf8e" />
              <StatChip icon={Snowflake} label="Cold-start" value={coldStartCount} color="#d4a843" />
              <StatChip icon={TrendingUp} label="Avg Conviction" value={avgConviction.toFixed(0)} color="#5e6ad2" />
            </div>
          </div>
        </header>

        {/* Main content */}
        {isLoading ? <NetworkSkeleton /> : errors.length > 0 && inboundCards.length === 0 && outboundFounders.length === 0 ? (
          <StateMessage tone="error" message="The sourcing map could not be loaded. Check that the backend is running, then retry." action={retry} />
        ) : (
          <>
            {errors.length > 0 && (
              <div className="mx-8 mt-4">
                <StateMessage tone="warning" message="Some sourcing data is unavailable. The map below contains only the sources that loaded." action={retry} />
              </div>
            )}
            {inboundCards.length + outboundFounders.length === 0 ? (
              <StateMessage tone="empty" message="No sourcing relationships yet. An isolated founder will appear here after the first application is received." />
            ) : (
              <NetworkCanvas inbound={inbound.data!} outbound={outboundFounders} />
            )}
          </>
        )}

        {/* Legend bar */}
        <div className="flex items-center gap-6 border-t border-border px-8 py-3">
          <span className="text-[10px] font-mono uppercase tracking-wider text-text-subtle">Legend</span>
          <LegendItem shape="rounded-sm" borderColor="rgba(94,106,210,0.5)" label="Founder" />
          <LegendItem shape="rounded-full" bgColor="#3ecf8e" label="GitHub" />
          <LegendItem shape="rounded-full" bgColor="#5e6ad2" label="arXiv" />
          <LegendItem shape="rounded-full" bgColor="#d4a843" label="ProductHunt" />
          <LegendItem shape="rounded-full" bgColor="#d4a843" label="HackerNews" />
          <LegendItem shape="rounded-full" bgColor="#5e6ad2" label="Accelerator" />
          <LegendItem shape="rounded-sm" borderColor="rgba(212,168,67,0.5)" label="Cold-start" icon={Snowflake} />
        </div>
      </div>
    </AppShell>
  );
}

function StatChip({ icon: Icon, label, value, color }: { icon: typeof Activity; label: string; value: number | string; color: string }) {
  return (
    <div className="metal-panel flex items-center gap-2.5 rounded-sm px-3 py-2">
      <Icon className="h-4 w-4 shrink-0" style={{ color }} />
      <div>
        <div className="font-mono text-lg font-bold text-text-primary" data-numeric>{value}</div>
        <div className="text-[9px] uppercase tracking-wider text-text-muted">{label}</div>
      </div>
    </div>
  );
}

function LegendItem({ shape, borderColor, bgColor, label, icon: Icon }: { shape: string; borderColor?: string; bgColor?: string; label: string; icon?: typeof Snowflake }) {
  return (
    <div className="flex items-center gap-1.5 text-[10px] text-text-muted">
      <div
        className={`h-3 w-3 ${shape}`}
        style={{ border: borderColor ? `1px solid ${borderColor}` : "none", background: bgColor || "transparent" }}
      />
      {Icon && <Icon className="h-2.5 w-2.5 text-warning" />}
      {label}
    </div>
  );
}

function NetworkSkeleton() {
  return (
    <div className="grid min-h-[560px] grid-cols-3 gap-4 p-8" aria-label="Loading network">
      <Skeleton className="h-24" /><Skeleton className="h-24" /><Skeleton className="h-24" />
      <Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" />
    </div>
  );
}

function StateMessage({ tone, message, action }: { tone: "error" | "warning" | "empty"; message: string; action?: () => void }) {
  const classes = tone === "error" ? "border-error-border bg-error-bg" : tone === "warning" ? "border-warning-border bg-warning-bg" : "border-border bg-card";
  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <Card className={`max-w-md p-5 text-center ${classes}`}>
        <AlertCircle className="mx-auto h-5 w-5 text-text-muted" />
        <p className="mt-3 text-sm text-text-secondary">{message}</p>
        {action && <Button className="mt-4" size="sm" variant="outline" onClick={action}>Retry</Button>}
      </Card>
    </div>
  );
}
