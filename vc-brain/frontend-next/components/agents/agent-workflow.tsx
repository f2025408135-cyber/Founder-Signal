"use client";
import { useState, useEffect, useRef } from "react";
import {
  Inbox, Search, Cpu, GitBranch, TrendingUp, ShieldCheck,
  Layers, FileText, CheckCircle2, Loader2, Circle,
  ChevronDown, ChevronRight, Activity, X, ArrowRight
} from "lucide-react";

/**
 * AgentWorkflowPanel — live visualization of the 8-node LangGraph pipeline.
 *
 * Shows each agent as a card with:
 * - Current status: idle → working → done (with animated indicators)
 * - What it's "cooking" (one-line description)
 * - Real-time data flow between nodes
 * - Expandable detail (model, description)
 *
 * Powered by SSE /api/events/stream — same event source as Signal Radar.
 */

const AGENT_NODES = [
  {
    id: "ingestion",
    label: "Ingestion Agent",
    icon: Inbox,
    color: "#5e6ad2",
    cooking: "Transforming raw signals into atomic Claims",
    model: "GPT-5.6 Luna",
    detail: "Takes GitHub commits, arXiv papers, PH launches, applications → flat list of atomic Claim records. Enforces R1-R5 rules. Emits cold_start_inferred claim when no external signals.",
  },
  {
    id: "fetch_external_evidence",
    label: "Fetch Evidence",
    icon: Search,
    color: "#5e6ad2",
    cooking: "Gathering external corroboration for each claim",
    model: "httpx + Crunchbase mock",
    detail: "For each claim, fetches external evidence. Runs in PARALLEL with thesis_fit.",
  },
  {
    id: "thesis_fit",
    label: "Thesis Fit",
    icon: TrendingUp,
    color: "#5e6ad2",
    cooking: "Computing founder-market cosine similarity",
    model: "Sentence-BERT (all-MiniLM-L6-v2)",
    detail: "Embeds founder claims + thesis sectors, computes cosine similarity. Outputs thesis_fit_score (0-100). Runs in PARALLEL with fetch_evidence.",
  },
  {
    id: "validator",
    label: "Validator Agent",
    icon: ShieldCheck,
    color: "#3ecf8e",
    cooking: "Cross-checking every claim against real evidence",
    model: "GPT-5.6 Sol",
    detail: "The ONLY agent that writes claim.flags and claim.confidence. 4 statuses: verified / unverifiable / contradicted / not_disclosed. Cross-claim contradiction detection.",
  },
  {
    id: "founder",
    label: "Founder Agent",
    icon: Cpu,
    color: "#5e6ad2",
    cooking: "Scoring founder across 4 independent axes",
    model: "GPT-5.6 Luna",
    detail: "Technical, market_fit, network, momentum. Cold-start rule: wide confidence band (≥50), all 5 flags, never fast_pass. Runs in PARALLEL with market.",
  },
  {
    id: "market",
    label: "Market Agent",
    icon: GitBranch,
    color: "#5e6ad2",
    cooking: "Assessing market: bullish / neutral / bear",
    model: "GPT-5.6 Luna",
    detail: "Categorical verdict — NEVER a numeric average. Bullish requires ≥2 verified growth claims. Runs in PARALLEL with founder.",
  },
  {
    id: "idea_vs_market",
    label: "Idea-vs-Market",
    icon: Layers,
    color: "#5e6ad2",
    cooking: "Scoring product-market fit + defensibility",
    model: "GPT-5.6 Luna",
    detail: "fit_score + defensibility_score. Runs AFTER market (reads market_output.reasoning).",
  },
  {
    id: "aggregator",
    label: "Aggregator (Tool-less)",
    icon: FileText,
    color: "#d4a843",
    cooking: "Synthesizing evidence-backed investment memo",
    model: "GPT-5.6 Sol",
    detail: "TOOL-LESS synthesizer — NO tools, NO URLs. Can only cite pre-verified facts. Produces memo_markdown with [^claim_id] citations. Geometric mean for conviction.",
  },
];

const PARALLEL_PAIRS = [
  ["fetch_external_evidence", "thesis_fit"],
  ["founder", "market"],
];

type AgentStatus = "idle" | "working" | "done";

interface AgentState {
  status: AgentStatus;
  startTime?: string;
  endTime?: string;
  detail?: string;
}

export function AgentWorkflowPanel({ onClose }: { onClose?: () => void }) {
  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>(
    Object.fromEntries(AGENT_NODES.map((n) => [n.id, { status: "idle" as AgentStatus }]))
  );
  const [expanded, setExpanded] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [eventLog, setEventLog] = useState<Array<{ time: string; agent: string; text: string }>>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;
    const connect = () => {
      try {
        const es = new EventSource("/api/events/stream");
        eventSourceRef.current = es;
        es.onopen = () => setConnected(true);
        es.onmessage = (e) => {
          try { handleEvent(JSON.parse(e.data)); } catch {}
        };
        es.onerror = () => {
          setConnected(false);
          es.close();
          reconnectTimer = setTimeout(connect, 3000);
        };
      } catch { setConnected(false); reconnectTimer = setTimeout(connect, 3000); }
    };
    connect();
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  const handleEvent = (event: any) => {
    const now = new Date().toLocaleTimeString("en-US", { hour12: false });
    const type = event.type || "";
    const text = event.text || "";
    const updates: Record<string, AgentState> = {};

    if (type === "application_received" || type === "signal_detected") {
      updates.ingestion = { status: "working", startTime: now, detail: text };
    } else if (type === "ingestion_complete") {
      updates.ingestion = { status: "done", endTime: now, detail: "Claims extracted" };
      updates.fetch_external_evidence = { status: "working", startTime: now };
      updates.thesis_fit = { status: "working", startTime: now };
    } else if (type === "validator_complete") {
      updates.fetch_external_evidence = { status: "done", endTime: now };
      updates.thesis_fit = { status: "done", endTime: now };
      updates.validator = { status: "done", endTime: now, detail: text };
      updates.founder = { status: "working", startTime: now };
      updates.market = { status: "working", startTime: now };
    } else if (type === "scoring_complete") {
      updates.founder = { status: "done", endTime: now };
      updates.market = { status: "done", endTime: now };
      updates.idea_vs_market = { status: "done", endTime: now, detail: text };
    } else if (type === "aggregator_complete") {
      updates.aggregator = { status: "done", endTime: now, detail: text };
    }

    if (Object.keys(updates).length > 0) {
      setAgentStates((prev) => ({ ...prev, ...updates }));
    }

    const agentName = AGENT_NODES.find((n) => updates[n.id]?.status === "working")?.label || "Pipeline";
    setEventLog((prev) => [...prev, { time: now, agent: agentName, text }].slice(-20));
  };

  const resetAgents = () => {
    setAgentStates(Object.fromEntries(AGENT_NODES.map((n) => [n.id, { status: "idle" as AgentStatus }])));
    setEventLog([]);
  };

  return (
    <div className="rounded-lg overflow-hidden" style={{ background: "#0a0908", border: "1px solid rgba(94,106,210,0.15)" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: "rgba(94,106,210,0.1)" }}>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4" style={{ color: "#5e6ad2" }} />
          <span className="text-sm font-bold text-text-primary">Agent Workflow</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{
            color: connected ? "#3ecf8e" : "#d44a5c",
            background: connected ? "rgba(62,207,142,0.1)" : "rgba(212,74,92,0.1)",
          }}>
            {connected ? "● LIVE" : "○ WAITING"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={resetAgents} className="text-[10px] font-mono px-2 py-1 rounded border hover:bg-elevated transition-colors" style={{ borderColor: "rgba(255,255,255,0.12)", color: "#9ca3af" }}>
            RESET
          </button>
          {onClose && <button onClick={onClose} className="text-text-muted hover:text-text-primary"><X className="w-4 h-4" /></button>}
        </div>
      </div>

      {/* Agent nodes */}
      <div className="p-4 space-y-1">
        {AGENT_NODES.map((node, i) => {
          const state = agentStates[node.id] || { status: "idle" };
          const Icon = node.icon;
          const isExpanded = expanded === node.id;
          const prevNode = AGENT_NODES[i - 1];
          const isParallelWithPrev = prevNode && PARALLEL_PAIRS.some((pair) => pair.includes(node.id) && pair.includes(prevNode.id));

          return (
            <div key={node.id}>
              {/* Parallel indicator */}
              {isParallelWithPrev && (
                <div className="flex items-center gap-2 ml-6 my-1">
                  <div className="text-[9px] font-mono" style={{ color: "#3ecf8e" }}>∥ PARALLEL</div>
                  <div className="flex-1 h-px" style={{ background: "rgba(62,207,142,0.15)" }} />
                </div>
              )}

              {/* Agent card */}
              <div
                className="rounded-md border transition-all cursor-pointer"
                style={{
                  borderColor: state.status === "working" ? node.color : state.status === "done" ? "rgba(62,207,142,0.2)" : "rgba(255,255,255,0.06)",
                  background: state.status === "working" ? `${node.color}08` : "#14151a",
                  boxShadow: state.status === "working" ? `0 0 12px ${node.color}15` : "none",
                }}
                onClick={() => setExpanded(expanded === node.id ? null : node.id)}
              >
                <div className="flex items-center gap-3 p-3">
                  {/* Status indicator */}
                  <div className="relative shrink-0">
                    {state.status === "idle" && <Circle className="w-4 h-4" style={{ color: "#6b7280" }} />}
                    {state.status === "working" && <Loader2 className="w-4 h-4 animate-spin" style={{ color: node.color }} />}
                    {state.status === "done" && <CheckCircle2 className="w-4 h-4" style={{ color: "#3ecf8e" }} />}
                  </div>

                  {/* Icon */}
                  <Icon className="w-4 h-4 shrink-0" style={{ color: state.status === "idle" ? "#6b7280" : node.color }} />

                  {/* Label + cooking text */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium" style={{ color: state.status === "idle" ? "#9ca3af" : "#e6e6e6" }}>
                      {node.label}
                    </div>
                    {state.status === "working" && (
                      <div className="text-[10px] font-mono truncate" style={{ color: node.color }}>
                        ⚡ {node.cooking}...
                      </div>
                    )}
                    {state.status === "done" && state.detail && (
                      <div className="text-[10px] font-mono truncate" style={{ color: "#3ecf8e" }}>
                        ✓ {state.detail}
                      </div>
                    )}
                    {state.status === "idle" && (
                      <div className="text-[10px] font-mono truncate" style={{ color: "#4a4a4a" }}>
                        {node.cooking}
                      </div>
                    )}
                  </div>

                  {/* Timing */}
                  {state.startTime && (
                    <div className="text-[9px] font-mono text-right shrink-0" style={{ color: "#6b7280" }}>
                      {state.startTime}
                      {state.endTime && <div style={{ color: "#3ecf8e" }}>→ {state.endTime}</div>}
                    </div>
                  )}

                  {/* Expand chevron */}
                  {isExpanded ? <ChevronDown className="w-3.5 h-3.5 shrink-0" style={{ color: "#6b7280" }} /> : <ChevronRight className="w-3.5 h-3.5 shrink-0" style={{ color: "#6b7280" }} />}
                </div>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-1 space-y-2 border-t" style={{ borderColor: "rgba(255,255,255,0.04)" }}>
                    <div className="flex gap-4 text-[10px] font-mono">
                      <span style={{ color: "#6b7280" }}>MODEL:</span>
                      <span style={{ color: node.color }}>{node.model}</span>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: "#9ca3af" }}>{node.detail}</p>
                  </div>
                )}
              </div>

              {/* Data flow arrow */}
              {i < AGENT_NODES.length - 1 && !isParallelWithPrev && (
                <div className="flex justify-center py-0.5">
                  <ArrowRight className="w-3 h-3 rotate-90" style={{ color: "rgba(255,255,255,0.1)" }} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Live event log */}
      {eventLog.length > 0 && (
        <div className="border-t px-4 py-3" style={{ borderColor: "rgba(94,106,210,0.1)" }}>
          <div className="text-[10px] font-mono uppercase tracking-wider mb-2" style={{ color: "#6b7280" }}>LIVE EVENT LOG</div>
          <div className="space-y-0.5 max-h-32 overflow-y-auto">
            {eventLog.map((log, i) => (
              <div key={i} className="font-mono text-[10px] leading-tight whitespace-nowrap" style={{ opacity: Math.max(0.3, 1 - (eventLog.length - 1 - i) / 15) }}>
                <span style={{ color: "#4a4a4a" }}>[{log.time}]</span>{" "}
                <span style={{ color: "#5e6ad2" }}>{log.agent}</span>{" "}
                <span style={{ color: "#9ca3af" }}>{log.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/** Button to toggle the Agent Workflow panel */
export function ViewAgentWorkflowButton({ onClick, label = "View Agent Workflow" }: { onClick: () => void; label?: string }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all hover:scale-105"
      style={{ background: "rgba(94,106,210,0.1)", border: "1px solid rgba(94,106,210,0.3)", color: "#5e6ad2" }}
    >
      <Activity className="w-3.5 h-3.5" />
      {label}
    </button>
  );
}
