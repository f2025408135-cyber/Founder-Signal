"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowRight, Zap, Filter, CheckCircle2, Clock, XCircle, TrendingUp, Users, Radar } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button, Card, Skeleton, Badge } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function FunnelPage() {
  const inbound = useQuery({ queryKey: ["inbox", "funnel"], queryFn: () => api.getInbox({ limit: 200 }) });
  const outbound = useQuery({ queryKey: ["outbound", "funnel"], queryFn: () => api.getOutboundQueue(200) });
  const applications = useQuery({ queryKey: ["applications", "funnel"], queryFn: () => api.getApplications(200) });
  const queries = [inbound, outbound, applications];
  const isLoading = queries.some((q) => q.isLoading);
  const errorCount = queries.filter((q) => q.error).length;
  const cards = [...(inbound.data?.cards ?? []), ...(outbound.data?.founders ?? [])];
  const uniqueCards = [...new Map(cards.map((c) => [c.founder_id, c])).values()];

  const stages = {
    sourced: uniqueCards.length,
    screened: uniqueCards.filter((c) => c.recommendation !== null).length,
    diligence: uniqueCards.filter((c) => c.recommendation === "deep_dive").length,
    fastPass: uniqueCards.filter((c) => c.recommendation === "fast_pass").length,
    pass: uniqueCards.filter((c) => c.recommendation === "pass").length,
    reject: uniqueCards.filter((c) => c.recommendation === "reject").length,
  };
  const conversion = stages.screened > 0 ? ((stages.fastPass + stages.diligence) / stages.screened) * 100 : 0;
  const retry = () => queries.forEach((q) => q.refetch());

  // Channel breakdown
  const channelBreakdown: Record<string, number> = {};
  outbound.data?.founders.forEach((f) => {
    const ch = f.sourcing_channel || "external";
    channelBreakdown[ch] = (channelBreakdown[ch] || 0) + 1;
  });

  // Status breakdown
  const statusBreakdown: Record<string, number> = {};
  applications.data?.applications.forEach((a) => {
    statusBreakdown[a.status] = (statusBreakdown[a.status] || 0) + 1;
  });

  const maxChannelCount = Math.max(...Object.values(channelBreakdown), 1);

  return (
    <AppShell>
      <div className="px-4 py-5 sm:px-8 sm:py-6">
        {/* Header */}
        <header className="mb-8">
          <p className="technical-label">Pipeline Overview</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-text-primary">Sourcing Funnel</h1>
          <p className="mt-1 text-sm text-text-muted">From first signal to investment decision — every stage, every outcome, in one view.</p>
        </header>

        {isLoading ? <FunnelSkeleton /> : errorCount === queries.length ? (
          <FunnelMessage message="The funnel could not be loaded. Check that the backend is running, then retry." action={retry} error />
        ) : (
          <>
            {errorCount > 0 && <div className="mb-4"><FunnelMessage message="Some funnel sources are unavailable. Counts below use the sources that loaded." action={retry} /></div>}

            {stages.sourced === 0 ? (
              <FunnelMessage message="No founders have entered the funnel yet. Submit an application or run an outbound scan to begin." />
            ) : (
              <>
                {/* Top metrics strip */}
                <div className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-5">
                  <MetricCard icon={Users} label="Inbound" value={inbound.data?.total ?? 0} color="#5e6ad2" />
                  <MetricCard icon={Radar} label="Outbound" value={outbound.data?.total ?? 0} color="#3ecf8e" />
                  <MetricCard icon={CheckCircle2} label="Screened" value={stages.screened} color="#e6e6e6" />
                  <MetricCard icon={Zap} label="Deep Dive" value={stages.diligence} color="#d4a843" />
                  <MetricCard icon={TrendingUp} label="Conversion" value={`${conversion.toFixed(1)}%`} color="#3ecf8e" />
                </div>

                {/* Main funnel visualization */}
                <Card className="mb-8 metal-panel p-6">
                  <div className="mb-8 flex items-center gap-3">
                    <Filter className="h-4 w-4 text-accent" />
                    <h2 className="text-sm font-bold uppercase tracking-wide text-text-primary">Screening Funnel</h2>
                    <div className="flex-1 h-px bg-border" />
                    <span className="text-[10px] font-mono text-text-muted">{stages.sourced} total founders</span>
                  </div>

                  {/* Funnel stages — 3D-feel trapezoidal narrowing */}
                  <div className="space-y-1">
                    <FunnelBar
                      label="Sourced"
                      count={stages.sourced}
                      total={stages.sourced}
                      color="linear-gradient(135deg, #5e6ad2, #3d5a80)"
                      sublabel={`${inbound.data?.total ?? 0} inbound · ${outbound.data?.total ?? 0} outbound`}
                      icon={Users}
                      delay={0}
                    />
                    <FunnelConnector height="24px" />
                    <FunnelBar
                      label="Screened"
                      count={stages.screened}
                      total={stages.sourced}
                      color="linear-gradient(135deg, #3d5a80, #4a6298)"
                      sublabel="pipeline completed"
                      icon={CheckCircle2}
                      delay={1}
                    />
                    <FunnelConnector height="24px" />
                    <FunnelBar
                      label="Deep Dive"
                      count={stages.diligence}
                      total={stages.sourced}
                      color="linear-gradient(135deg, #d4a843, #c49a3a)"
                      sublabel="recommendation: deep_dive"
                      icon={Clock}
                      delay={2}
                    />
                  </div>

                  {/* Decision outcomes — 3-card split */}
                  <div className="mt-8">
                    <div className="mb-3 flex items-center gap-2">
                      <div className="h-px flex-1 bg-border" />
                      <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Decision Outcomes</span>
                      <div className="h-px flex-1 bg-border" />
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <DecisionCard
                        icon={Zap}
                        label="Fast Pass"
                        count={stages.fastPass}
                        color="#3ecf8e"
                        bg="rgba(62,207,142,0.06)"
                        border="rgba(62,207,142,0.2)"
                        desc="Immediate $100K deployment"
                      />
                      <DecisionCard
                        icon={Clock}
                        label="Park"
                        count={stages.pass}
                        color="#9ca3af"
                        bg="rgba(156,163,175,0.06)"
                        border="rgba(156,163,175,0.15)"
                        desc="Revisit in 30 days"
                      />
                      <DecisionCard
                        icon={XCircle}
                        label="Reject"
                        count={stages.reject}
                        color="#d44a5c"
                        bg="rgba(212,74,92,0.06)"
                        border="rgba(212,74,92,0.2)"
                        desc="Fatal weakness detected"
                      />
                    </div>
                  </div>
                </Card>

                {/* Two-column: channel breakdown + status breakdown */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {/* Channel breakdown */}
                  <Card className="metal-panel p-5">
                    <div className="mb-4 flex items-center gap-2">
                      <Radar className="h-4 w-4 text-success" />
                      <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">Outbound Channel Breakdown</h3>
                    </div>
                    {Object.keys(channelBreakdown).length === 0 ? (
                      <p className="text-sm text-text-muted">No outbound signals detected yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {Object.entries(channelBreakdown).map(([channel, count]) => (
                          <div key={channel} className="flex items-center gap-3">
                            <div className="w-24 text-xs font-mono capitalize text-text-secondary">{channel}</div>
                            <div className="relative h-6 flex-1 rounded-sm border border-border bg-canvas-base/40">
                              <div
                                className="absolute inset-y-0 left-0 rounded-sm transition-all duration-500"
                                style={{
                                  width: `${(count / maxChannelCount) * 100}%`,
                                  background: channel === "github" ? "linear-gradient(90deg, #3ecf8e40, #3ecf8e80)" : channel === "arxiv" ? "linear-gradient(90deg, #5e6ad240, #5e6ad280)" : "linear-gradient(90deg, #d4a84340, #d4a84380)",
                                  border: `1px solid ${channel === "github" ? "#3ecf8e30" : channel === "arxiv" ? "#5e6ad230" : "#d4a84330"}`,
                                }}
                              />
                            </div>
                            <div className="w-8 text-right font-mono text-sm font-bold text-text-primary" data-numeric>{count}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>

                  {/* Application status breakdown */}
                  <Card className="metal-panel p-5">
                    <div className="mb-4 flex items-center gap-2">
                      <Users className="h-4 w-4 text-accent" />
                      <h3 className="text-sm font-bold uppercase tracking-wide text-text-primary">Application Status Breakdown</h3>
                    </div>
                    {Object.keys(statusBreakdown).length === 0 ? (
                      <p className="text-sm text-text-muted">No applications submitted yet.</p>
                    ) : (
                      <div className="grid grid-cols-3 gap-3">
                        {Object.entries(statusBreakdown).map(([status, count]) => {
                          const color = status === "fast_pass" ? "#3ecf8e" : status === "deep_dive" ? "#5e6ad2" : status === "rejected" ? "#d44a5c" : status === "passed" ? "#9ca3af" : "#6b7280";
                          return (
                            <div
                              key={status}
                              className="rounded-md border p-3 text-center"
                              style={{ borderColor: `${color}30`, background: `${color}08` }}
                            >
                              <div className="mb-1 text-[10px] uppercase tracking-wider" style={{ color }}>{status.replace(/_/g, " ")}</div>
                              <div className="font-mono text-xl font-bold" style={{ color }} data-numeric>{count}</div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </Card>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}

// ============= COMPONENTS =============

function MetricCard({ icon: Icon, label, value, color }: { icon: typeof Users; label: string; value: number | string; color: string }) {
  return (
    <Card className="metal-panel p-4">
      <div className="mb-2 flex items-center gap-2">
        <Icon className="h-3.5 w-3.5" style={{ color }} />
        <span className="text-[10px] uppercase tracking-wider text-text-muted">{label}</span>
      </div>
      <div className="font-mono text-2xl font-bold" style={{ color }} data-numeric>
        {typeof value === "number" ? value.toFixed(0) : value}
      </div>
    </Card>
  );
}

function FunnelBar({ label, count, total, color, sublabel, icon: Icon, delay }: {
  label: string;
  count: number;
  total: number;
  color: string;
  sublabel: string;
  icon: typeof Users;
  delay: number;
}) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  const width = Math.max(pct, 15); // min 15% so even small counts are visible

  return (
    <div className="flex items-center justify-center">
      <div
        className="relative overflow-hidden rounded-md border border-border-strong transition-all duration-700"
        style={{
          width: `${width}%`,
          background: color,
          boxShadow: "inset 0 1px 0 rgba(255,255,255,0.15), inset 0 -1px 0 rgba(0,0,0,0.3), 0 4px 14px -6px rgba(0,0,0,0.5)",
          animationDelay: `${delay * 100}ms`,
        }}
      >
        {/* Sheen overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.12) 0%, transparent 40%, transparent 60%, rgba(0,0,0,0.1) 100%)" }}
        />
        <div className="relative flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Icon className="h-4 w-4 text-white/70" />
            <div>
              <div className="text-sm font-bold uppercase tracking-wider text-white">{label}</div>
              <div className="text-[10px] text-white/60">{sublabel}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="font-mono text-3xl font-bold text-white" data-numeric>{count}</div>
            <div className="text-[10px] font-mono text-white/50">{pct.toFixed(0)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FunnelConnector({ height = "24px" }: { height?: string }) {
  return (
    <div className="flex justify-center" style={{ height }}>
      <svg width="40" height={parseInt(height)} viewBox={`0 0 40 ${parseInt(height)}`}>
        <line x1="20" y1="0" x2="20" y2={parseInt(height)} stroke="rgba(255,255,255,0.08)" strokeWidth="1" strokeDasharray="3 4" />
        <polygon points="14,0 26,0 20,8" fill="rgba(255,255,255,0.06)" />
      </svg>
    </div>
  );
}

function DecisionCard({ icon: Icon, label, count, color, bg, border, desc }: {
  icon: typeof Zap;
  label: string;
  count: number;
  color: string;
  bg: string;
  border: string;
  desc: string;
}) {
  return (
    <div
      className="metal-panel rounded-md border p-4 text-center transition-all hover:scale-[1.02]"
      style={{ borderColor: border, background: bg, boxShadow: `inset 0 1px 0 ${color}15, 0 4px 14px -8px rgba(0,0,0,0.4)` }}
    >
      <Icon className="mx-auto mb-2 h-5 w-5" style={{ color }} />
      <div className="mb-1 text-xs font-bold uppercase tracking-wider" style={{ color }}>{label}</div>
      <div className="font-mono text-3xl font-bold" style={{ color }} data-numeric>{count}</div>
      <div className="mt-1 text-[10px] text-text-muted">{desc}</div>
    </div>
  );
}

function FunnelSkeleton() {
  return (
    <div className="space-y-6" aria-label="Loading funnel">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
      </div>
      <Skeleton className="h-[420px] w-full" />
    </div>
  );
}

function FunnelMessage({ message, action, error = false }: { message: string; action?: () => void; error?: boolean }) {
  return (
    <Card className={cn("mx-auto max-w-md p-5 text-center", error ? "border-error-border bg-error-bg" : "border-warning-border bg-warning-bg")}>
      <AlertCircle className="mx-auto h-5 w-5 text-text-muted" />
      <p className="mt-3 text-sm text-text-secondary">{message}</p>
      {action && <Button className="mt-4" size="sm" variant="outline" onClick={action}>Retry</Button>}
    </Card>
  );
}
