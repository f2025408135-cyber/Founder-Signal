"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button, Card, Skeleton } from "@/components/ui/primitives";
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

  return <AppShell><div className="flex h-full flex-col"><header className="border-b border-border px-8 py-4"><h1 className="text-2xl font-bold tracking-tight text-text-primary">Network View</h1><p className="mt-1 text-sm text-text-muted">Founders, sourcing channels, and institutions as a connected graph.</p></header>{isLoading ? <NetworkSkeleton /> : errors.length > 0 && inboundCards.length === 0 && outboundFounders.length === 0 ? <StateMessage tone="error" message="The network could not be loaded. Check that the backend is running, then retry." action={retry} /> : <>{errors.length > 0 && <StateMessage tone="warning" message="Some network data is unavailable. The graph below contains only the sources that loaded." action={retry} />}{inboundCards.length + outboundFounders.length === 0 ? <StateMessage tone="empty" message="No founder relationships yet. An isolated founder will appear here after the first application is received." /> : <NetworkCanvas inbound={inbound.data!} outbound={outboundFounders} />}</>}<div className="flex items-center gap-4 border-t border-border px-8 py-3 text-[10px] text-text-muted"><span className="flex items-center gap-1"><span className="h-3 w-3 rounded-full border border-border-strong" /> Founder</span><span className="flex items-center gap-1"><span className="h-3 w-3 rounded-full bg-success" /> Channel</span><span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm border border-warning-border" /> Cold-start</span></div></div></AppShell>;
}

function NetworkSkeleton() { return <div className="grid min-h-[560px] grid-cols-3 gap-4 p-8" aria-label="Loading network"><Skeleton className="h-24" /><Skeleton className="h-24" /><Skeleton className="h-24" /><Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" /></div>; }
function StateMessage({ tone, message, action }: { tone: "error" | "warning" | "empty"; message: string; action?: () => void }) { const classes = tone === "error" ? "border-error-border bg-error-bg" : tone === "warning" ? "border-warning-border bg-warning-bg" : "border-border bg-card"; return <div className="flex flex-1 items-center justify-center p-8"><Card className={`max-w-md p-5 text-center ${classes}`}><AlertCircle className="mx-auto h-5 w-5 text-text-muted" /><p className="mt-3 text-sm text-text-secondary">{message}</p>{action && <Button className="mt-4" size="sm" variant="outline" onClick={action}>Retry</Button>}</Card></div>; }
