"use client";
import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertCircle } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Badge } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function FunnelPage() {
  const { data: outbound } = useQuery({
    queryKey: ["outbound"],
    queryFn: () => api.getOutboundQueue(200),
  });
  const { data: inbox } = useQuery({
    queryKey: ["inbox"],
    queryFn: () => api.getInbox({ limit: 200 }),
  });
  const { data: apps } = useQuery({
    queryKey: ["applications"],
    queryFn: () => api.getApplications(200),
  });

  const allCards = [
    ...(inbox?.cards ?? []),
    ...(outbound?.founders ?? []),
  ];

  const stages = {
    sourced: allCards.length,
    screened: allCards.filter((c) => c.recommendation !== null).length,
    diligence: allCards.filter((c) => c.recommendation === "deep_dive").length,
    fast_pass: allCards.filter((c) => c.recommendation === "fast_pass").length,
    pass: allCards.filter((c) => c.recommendation === "pass").length,
    reject: allCards.filter((c) => c.recommendation === "reject").length,
  };

  const inboundCount = inbox?.total ?? 0;
  const outboundCount = outbound?.total ?? 0;
  const conversionRate = stages.screened > 0
    ? ((stages.fast_pass + stages.diligence) / stages.screened) * 100
    : 0;

  return (
    <AppShell>
      <div className="px-8 py-6 max-w-5xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Funnel View</h1>
          <p className="text-sm text-text-muted mt-1">
            Inbound + outbound tracks converging into one screening funnel.
          </p>
        </header>

        {/* Top metrics */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <MetricCard label="Inbound" value={inboundCount} color="text-accent" />
          <MetricCard label="Outbound" value={outboundCount} color="text-success" />
          <MetricCard label="Screened" value={stages.screened} color="text-text-primary" />
          <MetricCard label="Conversion" value={`${conversionRate.toFixed(1)}%`} color="text-warning" />
        </div>

        {/* Funnel visualization */}
        <Card className="p-6">
          <h2 className="text-sm font-bold mb-6 text-text-primary uppercase tracking-wide">
            Screening Funnel
          </h2>

          {/* Stage 1: Sourced (inbound + outbound converge) */}
          <FunnelStage
            label="Sourced"
            count={stages.sourced}
            width="100%"
            color="bg-accent"
            sublabel={`${inboundCount} inbound + ${outboundCount} outbound`}
          />

          {/* Connector */}
          <FunnelConnector />

          {/* Stage 2: Screened */}
          <FunnelStage
            label="Screened"
            count={stages.screened}
            width="80%"
            color="bg-accent/80"
            sublabel="pipeline completed"
          />

          <FunnelConnector />

          {/* Stage 3: Diligence */}
          <FunnelStage
            label="Diligence"
            count={stages.diligence}
            width="50%"
            color="bg-warning"
            sublabel="recommendation: deep_dive"
          />

          <FunnelConnector />

          {/* Stage 4: Decision (split) */}
          <div className="flex justify-center gap-4 mt-6">
            <DecisionCard
              label="fast_pass"
              count={stages.fast_pass}
              color="text-success"
              bg="bg-success-bg"
              border="border-success-border"
            />
            <DecisionCard
              label="pass"
              count={stages.pass}
              color="text-text-muted"
              bg="bg-neutral-bg"
              border="border-neutral-border"
            />
            <DecisionCard
              label="reject"
              count={stages.reject}
              color="text-error"
              bg="bg-error-bg"
              border="border-error-border"
            />
          </div>
        </Card>

        {/* Channel breakdown */}
        {outbound && outbound.founders.length > 0 && (
          <Card className="mt-6 p-6">
            <h2 className="text-sm font-bold mb-4 text-text-primary uppercase tracking-wide">
              Outbound Channel Breakdown
            </h2>
            <div className="grid grid-cols-5 gap-3">
              {Object.entries(
                outbound.founders.reduce<Record<string, number>>((acc, f) => {
                  const ch = f.sourcing_channel || "external";
                  acc[ch] = (acc[ch] || 0) + 1;
                  return acc;
                }, {})
              ).map(([ch, count]) => (
                <div key={ch} className="text-center p-3 rounded-md border border-border">
                  <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">{ch}</div>
                  <div className="font-mono text-lg font-bold text-text-primary" data-numeric>
                    {count}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Status breakdown */}
        {apps && apps.applications.length > 0 && (
          <Card className="mt-6 p-6">
            <h2 className="text-sm font-bold mb-4 text-text-primary uppercase tracking-wide">
              Application Status Breakdown
            </h2>
            <div className="grid grid-cols-6 gap-3">
              {Object.entries(
                apps.applications.reduce<Record<string, number>>((acc, a) => {
                  acc[a.status] = (acc[a.status] || 0) + 1;
                  return acc;
                }, {})
              ).map(([status, count]) => (
                <div key={status} className="text-center p-3 rounded-md border border-border">
                  <div className="text-[10px] text-text-muted mb-1">{status}</div>
                  <div className="font-mono text-lg font-bold text-text-primary" data-numeric>
                    {count}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}

function MetricCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <Card className="p-4">
      <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">{label}</div>
      <div className={cn("text-2xl font-bold font-mono", color)} data-numeric>
        {typeof value === "number" ? value.toFixed(0) : value}
      </div>
    </Card>
  );
}

function FunnelStage({
  label,
  count,
  width,
  color,
  sublabel,
}: {
  label: string;
  count: number;
  width: string;
  color: string;
  sublabel?: string;
}) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={cn("rounded-md p-4 text-center transition-all", color)}
        style={{ width }}
      >
        <div className="text-xs text-white/80 uppercase tracking-wider mb-1">{label}</div>
        <div className="text-2xl font-bold text-white font-mono" data-numeric>
          {count}
        </div>
        {sublabel && <div className="text-[10px] text-white/60 mt-1">{sublabel}</div>}
      </div>
    </div>
  );
}

function FunnelConnector() {
  return <div className="w-px h-8 bg-border-strong mx-auto my-2" />;
}

function DecisionCard({
  label,
  count,
  color,
  bg,
  border,
}: {
  label: string;
  count: number;
  color: string;
  bg: string;
  border: string;
}) {
  return (
    <div className={cn("flex-1 max-w-[180px] p-4 rounded-md border text-center", bg, border)}>
      <div className={cn("text-xs uppercase tracking-wider mb-1", color)}>{label}</div>
      <div className={cn("text-2xl font-bold font-mono", color)} data-numeric>
        {count}
      </div>
    </div>
  );
}
