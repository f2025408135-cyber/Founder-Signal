"use client";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, Clock, Cpu, AlertCircle, Activity } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import type { TraceNode } from "@/lib/types";
import { cn } from "@/lib/utils";

export function PipelineTrace({ traceId }: { traceId: string | null | undefined }) {
  const [collapsed, setCollapsed] = useState(false);
  const { data, isLoading, error } = useQuery({
    queryKey: ["trace", traceId],
    queryFn: () => api.getTrace(traceId!),
    enabled: !!traceId,
  });

  if (!traceId) {
    return (
      <div className="text-xs text-text-muted p-4 border border-dashed border-border rounded-md">
        No trace available for this run.
      </div>
    );
  }

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="text-xs text-text-muted hover:text-text-primary flex items-center gap-1"
      >
        <ChevronRight className="w-3 h-3" /> Show trace
      </button>
    );
  }

  return (
    <div className="metal-panel rounded-sm overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2 text-xs font-bold text-text-primary">
          <Activity className="w-3.5 h-3.5" />
          Pipeline Trace
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="text-text-muted hover:text-text-primary"
        >
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="p-3 max-h-[60vh] overflow-auto">
        {isLoading && (
          <div className="text-xs text-text-muted flex items-center gap-1.5">
            <Clock className="w-3 h-3 animate-spin" /> Loading trace…
          </div>
        )}
        {error && (
          <div className="text-xs text-error flex items-center gap-1.5">
            <AlertCircle className="w-3 h-3" /> {(error as Error).message}
          </div>
        )}
        {data && !data.available && (
          <div className="text-xs text-text-muted">{data.reason || "Trace not available."}</div>
        )}
        {data && data.available && data.nodes && data.nodes.length > 0 && (
          <TraceTree nodes={data.nodes} />
        )}
        {data && data.available && (!data.nodes || data.nodes.length === 0) && (
          <div className="text-xs text-text-muted">Trace exists but no spans were returned.</div>
        )}
      </div>

      <div className="px-3 py-2 border-t border-border text-[10px] text-text-subtle font-mono break-all">
        {traceId}
      </div>
    </div>
  );
}

function TraceTree({ nodes }: { nodes: TraceNode[] }) {
  return (
    <ul className="space-y-1">
      {nodes.map((node, i) => (
        <TraceNodeRow key={node.id || i} node={node} />
      ))}
    </ul>
  );
}

function TraceNodeRow({ node }: { node: TraceNode }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails = node.model || node.input_tokens || node.output_tokens || node.latency_ms;
  const statusColor =
    node.status === "success"
      ? "bg-success"
      : node.status === "error"
        ? "bg-error"
        : "bg-text-muted";

  return (
    <li>
      {hasDetails ? (
      <button
        type="button"
        className="flex w-full items-center gap-2 rounded px-2 py-1 text-left text-xs hover:bg-elevated"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        {expanded ? (
          <ChevronDown className="w-3 h-3 shrink-0 text-text-muted" />
        ) : (
          <ChevronRight className="w-3 h-3 shrink-0 text-text-muted" />
        )}
        <span className="font-mono truncate flex-1 text-text-secondary">
          {node.name || node.type || "(unnamed)"}
        </span>
        {node.model && (
          <span className="text-[10px] text-text-muted flex items-center gap-0.5">
            <Cpu className="w-2.5 h-2.5" />
            {node.model}
          </span>
        )}
        {node.latency_ms != null && (
          <span className="text-[10px] text-text-muted flex items-center gap-0.5">
            <Clock className="w-2.5 h-2.5" />
            {(node.latency_ms / 1000).toFixed(2)}s
          </span>
        )}
        <span className={cn("w-1.5 h-1.5 rounded-full", statusColor)} aria-label={`Status: ${node.status}`} />
      </button>
      ) : (
      <div className="flex items-center gap-2 rounded px-2 py-1 text-xs">
        <span className="w-3 h-3 shrink-0" />
        <span className="font-mono truncate flex-1 text-text-secondary">{node.name || node.type || "(unnamed)"}</span>
        <span className={cn("w-1.5 h-1.5 rounded-full", statusColor)} aria-label={`Status: ${node.status}`} />
      </div>
      )}
      {expanded && hasDetails && (
        <div className="ml-5 mt-1 mb-2 p-2 rounded bg-elevated text-[11px] space-y-1">
          {node.model && (
            <div>
              <span className="text-text-muted">model:</span>{" "}
              <code className="font-mono">{node.model}</code>
            </div>
          )}
          {node.input_tokens != null && (
            <div>
              <span className="text-text-muted">input_tokens:</span>{" "}
              <span className="font-mono" data-numeric>{node.input_tokens}</span>
            </div>
          )}
          {node.output_tokens != null && (
            <div>
              <span className="text-text-muted">output_tokens:</span>{" "}
              <span className="font-mono" data-numeric>{node.output_tokens}</span>
            </div>
          )}
          {node.latency_ms != null && (
            <div>
              <span className="text-text-muted">latency:</span>{" "}
              <span className="font-mono" data-numeric>{(node.latency_ms / 1000).toFixed(3)}s</span>
            </div>
          )}
          {node.start_time && (
            <div>
              <span className="text-text-muted">start:</span>{" "}
              <span className="font-mono">{new Date(node.start_time).toLocaleString()}</span>
            </div>
          )}
          <div>
            <span className="text-text-muted">status:</span>{" "}
            <span className="font-mono">{node.status}</span>
          </div>
        </div>
      )}
    </li>
  );
}
