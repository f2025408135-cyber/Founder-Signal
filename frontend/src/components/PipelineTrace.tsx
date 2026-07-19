/** PipelineTrace — right-side collapsible panel showing the Langfuse trace tree.

Per spec §9.2:
- Top-level nodes: ingestion, fetch_external_evidence, thesis_fit, validator,
  founder, market, idea_vs_market, aggregator
- Each expands to show: LLM model, token count, latency, status, nested tool-call spans
- Fetched from GET /api/traces/{run_id} (Langfuse proxy)
*/
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, Clock, Cpu, AlertCircle, Activity } from "lucide-react";
import { api, type TraceNode } from "../lib/api";
import { cn } from "../lib/utils";

export default function PipelineTrace({ traceId }: { traceId: string | null | undefined }) {
  const [collapsed, setCollapsed] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["trace", traceId],
    queryFn: () => api.getTrace(traceId!),
    enabled: !!traceId,
  });

  if (!traceId) {
    return (
      <div className="text-xs text-[var(--color-muted-foreground)] p-4 border border-dashed border-[var(--color-border)] rounded-md">
        No trace available for this run.
      </div>
    );
  }

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="text-xs text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] flex items-center gap-1"
      >
        <ChevronRight className="w-3 h-3" /> Show trace
      </button>
    );
  }

  return (
    <div className="border border-[var(--color-border)] rounded-md bg-[var(--color-card)] overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2 text-xs font-semibold">
          <Activity className="w-3.5 h-3.5" />
          Pipeline Trace
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
        >
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="p-3 max-h-[60vh] overflow-auto">
        {isLoading && (
          <div className="text-xs text-[var(--color-muted-foreground)] flex items-center gap-1.5">
            <Clock className="w-3 h-3 animate-spin" /> Loading trace…
          </div>
        )}
        {error && (
          <div className="text-xs text-[var(--color-destructive)] flex items-center gap-1.5">
            <AlertCircle className="w-3 h-3" /> {(error as Error).message}
          </div>
        )}
        {data && !data.available && (
          <div className="text-xs text-[var(--color-muted-foreground)]">
            {data.reason || "Trace not available."}
          </div>
        )}
        {data && data.available && data.nodes && data.nodes.length > 0 && (
          <TraceTree nodes={data.nodes} />
        )}
        {data && data.available && (!data.nodes || data.nodes.length === 0) && (
          <div className="text-xs text-[var(--color-muted-foreground)]">
            Trace exists but no spans were returned.
          </div>
        )}
      </div>

      <div className="px-3 py-2 border-t border-[var(--color-border)] text-[10px] text-[var(--color-muted-foreground)] font-mono break-all">
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
      ? "text-[var(--color-verified)]"
      : node.status === "error"
        ? "text-[var(--color-destructive)]"
        : "text-[var(--color-muted-foreground)]";

  return (
    <li>
      <div
        className={cn(
          "flex items-center gap-2 text-xs py-1 px-2 rounded hover:bg-[var(--color-accent)] cursor-default",
          hasDetails && "cursor-pointer"
        )}
        onClick={() => hasDetails && setExpanded(!expanded)}
      >
        {hasDetails ? (
          expanded ? (
            <ChevronDown className="w-3 h-3 shrink-0" />
          ) : (
            <ChevronRight className="w-3 h-3 shrink-0" />
          )
        ) : (
          <span className="w-3 h-3 shrink-0" />
        )}
        <span className="font-mono truncate flex-1">{node.name || node.type || "(unnamed)"}</span>
        {node.model && (
          <span className="text-[10px] text-[var(--color-muted-foreground)] flex items-center gap-0.5">
            <Cpu className="w-2.5 h-2.5" />
            {node.model}
          </span>
        )}
        {node.latency_ms != null && (
          <span className="text-[10px] text-[var(--color-muted-foreground)] flex items-center gap-0.5">
            <Clock className="w-2.5 h-2.5" />
            {(node.latency_ms / 1000).toFixed(2)}s
          </span>
        )}
        <span className={cn("w-1.5 h-1.5 rounded-full", statusColor.replace("text-", "bg-"))} />
      </div>
      {expanded && hasDetails && (
        <div className="ml-5 mt-1 mb-2 p-2 rounded bg-[var(--color-muted)] text-[11px] space-y-1">
          {node.model && (
            <div>
              <span className="text-[var(--color-muted-foreground)]">model:</span>{" "}
              <code className="font-mono">{node.model}</code>
            </div>
          )}
          {node.input_tokens != null && (
            <div>
              <span className="text-[var(--color-muted-foreground)]">input_tokens:</span>{" "}
              <span className="font-mono">{node.input_tokens}</span>
            </div>
          )}
          {node.output_tokens != null && (
            <div>
              <span className="text-[var(--color-muted-foreground)]">output_tokens:</span>{" "}
              <span className="font-mono">{node.output_tokens}</span>
            </div>
          )}
          {node.latency_ms != null && (
            <div>
              <span className="text-[var(--color-muted-foreground)]">latency:</span>{" "}
              <span className="font-mono">{(node.latency_ms / 1000).toFixed(3)}s</span>
            </div>
          )}
          {node.start_time && (
            <div>
              <span className="text-[var(--color-muted-foreground)]">start:</span>{" "}
              <span className="font-mono">{new Date(node.start_time).toLocaleString()}</span>
            </div>
          )}
          <div>
            <span className="text-[var(--color-muted-foreground)]">status:</span>{" "}
            <span className={statusColor + " font-mono"}>{node.status}</span>
          </div>
          <div>
            <span className="text-[var(--color-muted-foreground)]">level:</span>{" "}
            <span className="font-mono">{node.level}</span>
          </div>
        </div>
      )}
    </li>
  );
}
