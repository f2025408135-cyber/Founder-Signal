"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button, Card, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function FunnelPage() {
  const inbound = useQuery({ queryKey: ["inbox", "funnel"], queryFn: () => api.getInbox({ limit: 200 }) });
  const outbound = useQuery({ queryKey: ["outbound", "funnel"], queryFn: () => api.getOutboundQueue(200) });
  const applications = useQuery({ queryKey: ["applications", "funnel"], queryFn: () => api.getApplications(200) });
  const queries = [inbound, outbound, applications];
  const isLoading = queries.some((query) => query.isLoading);
  const errorCount = queries.filter((query) => query.error).length;
  const cards = [...(inbound.data?.cards ?? []), ...(outbound.data?.founders ?? [])];
  const uniqueCards = [...new Map(cards.map((card) => [card.founder_id, card])).values()];
  const stages = {
    sourced: uniqueCards.length,
    screened: uniqueCards.filter((card) => card.recommendation !== null).length,
    diligence: uniqueCards.filter((card) => card.recommendation === "deep_dive").length,
    fastPass: uniqueCards.filter((card) => card.recommendation === "fast_pass").length,
    pass: uniqueCards.filter((card) => card.recommendation === "pass").length,
    reject: uniqueCards.filter((card) => card.recommendation === "reject").length,
  };
  const conversion = stages.screened > 0 ? ((stages.fastPass + stages.diligence) / stages.screened) * 100 : 0;
  const retry = () => queries.forEach((query) => query.refetch());

  return <AppShell><div className="px-4 py-5 sm:px-8 sm:py-6"><header className="mb-6"><h1 className="text-2xl font-bold tracking-tight text-text-primary">Funnel View</h1><p className="mt-1 text-sm text-text-muted">Inbound and outbound tracks converging into one screening funnel.</p></header>{isLoading ? <FunnelSkeleton /> : errorCount === queries.length ? <FunnelMessage message="The funnel could not be loaded. Check that the backend is running, then retry." action={retry} error /> : <>{errorCount > 0 && <FunnelMessage message="Some funnel sources are unavailable. Counts below use the sources that loaded." action={retry} />}{stages.sourced === 0 ? <FunnelMessage message="No founders have entered the funnel yet. Submit an application or run an outbound scan to begin." /> : <><div className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4"><MetricCard label="Inbound" value={inbound.data?.total ?? 0} color="text-accent" /><MetricCard label="Outbound" value={outbound.data?.total ?? 0} color="text-success" /><MetricCard label="Screened" value={stages.screened} color="text-text-primary" /><MetricCard label="Conversion" value={`${conversion.toFixed(1)}%`} color="text-warning" /></div><Card className="p-4 sm:p-6"><h2 className="mb-6 text-sm font-bold uppercase tracking-wide text-text-primary">Screening Funnel</h2><FunnelStage label="Sourced" count={stages.sourced} width="100%" color="bg-accent" sublabel={`${inbound.data?.total ?? 0} inbound + ${outbound.data?.total ?? 0} outbound`} /><FunnelConnector /><FunnelStage label="Screened" count={stages.screened} width="80%" color="bg-accent-muted" sublabel="pipeline completed" /><FunnelConnector /><FunnelStage label="Deep dive" count={stages.diligence} width="50%" color="bg-warning" sublabel="recommendation: deep_dive" /><FunnelConnector /><div className="grid grid-cols-3 gap-3"><DecisionCard label="fast_pass" count={stages.fastPass} color="text-success" bg="bg-success-bg" border="border-success-border" /><DecisionCard label="pass" count={stages.pass} color="text-text-secondary" bg="bg-neutral-bg" border="border-neutral-border" /><DecisionCard label="reject" count={stages.reject} color="text-error" bg="bg-error-bg" border="border-error-border" /></div></Card></>}</>}</div></AppShell>;
}

function FunnelSkeleton() { return <div className="space-y-6" aria-label="Loading funnel"><div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20" />)}</div><Skeleton className="h-[420px] w-full" /></div>; }
function FunnelMessage({ message, action, error = false }: { message: string; action?: () => void; error?: boolean }) { return <Card className={cn("mx-auto max-w-md p-5 text-center", error ? "border-error-border bg-error-bg" : "border-warning-border bg-warning-bg")}><AlertCircle className="mx-auto h-5 w-5 text-text-muted" /><p className="mt-3 text-sm text-text-secondary">{message}</p>{action && <Button className="mt-4" size="sm" variant="outline" onClick={action}>Retry</Button>}</Card>; }
function MetricCard({ label, value, color }: { label: string; value: number | string; color: string }) { return <Card className="p-4"><div className="mb-1 text-[10px] uppercase tracking-wider text-text-muted">{label}</div><div className={cn("font-mono text-2xl font-bold", color)}>{typeof value === "number" ? value.toFixed(0) : value}</div></Card>; }
function FunnelStage({ label, count, width, color, sublabel }: { label: string; count: number; width: string; color: string; sublabel: string }) { return <div className="flex flex-col items-center"><div className={cn("rounded-sm border border-border-strong p-4 text-center text-canvas-base shadow-[inset_0_1px_0_rgba(255,255,255,.35)]", color)} style={{ width }}><div className="mb-1 text-xs font-bold uppercase tracking-wider">{label}</div><div className="font-mono text-2xl font-bold">{count}</div><div className="mt-1 text-[10px] text-canvas-base/80">{sublabel}</div></div></div>; }
function FunnelConnector() { return <div className="mx-auto my-2 h-8 w-px bg-border-strong" />; }
function DecisionCard({ label, count, color, bg, border }: { label: string; count: number; color: string; bg: string; border: string }) { return <div className={cn("p-3 text-center sm:p-4", bg, border, "rounded-md border")}><div className={cn("mb-1 text-[10px] uppercase tracking-wider sm:text-xs", color)}>{label}</div><div className={cn("font-mono text-xl font-bold sm:text-2xl", color)}>{count}</div></div>; }
