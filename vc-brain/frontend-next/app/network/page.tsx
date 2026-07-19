"use client";
import { useCallback, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type NodeMouseHandler,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Loader2, AlertCircle, Snowflake, Github, FileText, Rocket, Newspaper, Building } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button, Card, Badge } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface FounderNodeData {
  founderId: string;
  founderName: string;
  companyName: string | null;
  conviction: number | null;
  evidenceCoverage: number | null;
  recommendation: string | null;
  coldStart: boolean;
  [key: string]: unknown;
}

interface ChannelNodeData {
  channelType: string;
  signalCount: number;
  [key: string]: unknown;
}

const channelConfig: Record<string, { color: string; bg: string; icon: typeof Github }> = {
  github: { color: "text-success", bg: "bg-success-bg", icon: Github },
  arxiv: { color: "text-accent", bg: "bg-accent/20", icon: FileText },
  producthunt: { color: "text-warning", bg: "bg-warning-bg", icon: Rocket },
  hackernews: { color: "text-warning", bg: "bg-warning-bg", icon: Newspaper },
  accelerator: { color: "text-accent", bg: "bg-accent/20", icon: Building },
};

function FounderNodeComponent({ data }: { data: FounderNodeData }) {
  return (
    <div
      className={cn(
        "bg-card border rounded-lg p-3 min-w-[160px]",
        data.coldStart ? "border-warning/40" : "border-border-strong"
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-accent !w-2 !h-2" />
      <div className="flex items-center gap-2 mb-2">
        <div
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold",
            data.recommendation === "fast_pass"
              ? "bg-success-bg text-success"
              : data.recommendation === "deep_dive"
                ? "bg-accent/20 text-accent"
                : data.recommendation === "reject"
                  ? "bg-error-bg text-error"
                  : "bg-neutral-bg text-neutral"
          )}
        >
          {data.founderName.charAt(0)}
        </div>
        <div>
          <div className="text-sm font-bold text-text-primary">{data.founderName}</div>
          <div className="text-xs text-text-muted">{data.companyName}</div>
        </div>
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-text-muted">Conviction</span>
          <span className="font-mono text-text-primary" data-numeric>
            {data.conviction?.toFixed(0) ?? "—"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-muted">Evidence</span>
          <span className="font-mono text-text-primary" data-numeric>
            {data.evidenceCoverage?.toFixed(2) ?? "—"}
          </span>
        </div>
        {data.coldStart && (
          <div className="flex items-center gap-1 text-warning">
            <Snowflake className="w-3 h-3" />
            <span className="text-[10px]">cold-start</span>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-accent !w-2 !h-2" />
    </div>
  );
}

function ChannelNodeComponent({ data }: { data: ChannelNodeData }) {
  const config = channelConfig[data.channelType] ?? channelConfig.github;
  const Icon = config.icon;
  return (
    <div className="bg-card border border-border-strong rounded-full p-3 flex items-center gap-2 min-w-[120px]">
      <Handle type="target" position={Position.Top} className="!bg-accent !w-2 !h-2" />
      <div className={cn("w-6 h-6 rounded-full flex items-center justify-center", config.bg, config.color)}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div>
        <div className="text-xs font-bold text-text-primary capitalize">{data.channelType}</div>
        <div className="text-[10px] text-text-muted">{data.signalCount} signals</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-accent !w-2 !h-2" />
    </div>
  );
}

const nodeTypes = {
  founder: FounderNodeComponent,
  channel: ChannelNodeComponent,
};

const defaultEdgeOptions = {
  type: "smoothstep",
  style: { stroke: "rgba(255, 255, 255, 0.15)", strokeWidth: 1.5 },
  animated: false,
};

export default function NetworkPage() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const { data: outbound, isLoading: outboundLoading, error: outboundError } = useQuery({
    queryKey: ["outbound"],
    queryFn: () => api.getOutboundQueue(50),
  });

  const { data: inbox } = useQuery({
    queryKey: ["inbox"],
    queryFn: () => api.getInbox({ limit: 50 }),
  });

  const { nodes, edges } = useMemo(() => {
    const n: Node[] = [];
    const e: Edge[] = [];
    const channelCounts: Record<string, number> = {};
    const channelY: Record<string, number> = {};

    // Channel nodes (top row)
    const channels = new Set<string>();
    outbound?.founders.forEach((f) => channels.add(f.sourcing_channel));
    Array.from(channels).forEach((ch, i) => {
      const count = outbound?.founders.filter((f) => f.sourcing_channel === ch).length ?? 0;
      channelCounts[ch] = count;
      channelY[ch] = i * 120;
      n.push({
        id: `channel-${ch}`,
        type: "channel",
        position: { x: 200 + i * 200, y: 0 },
        data: { channelType: ch, signalCount: count },
      });
    });

    // Founder nodes (middle row) — outbound
    outbound?.founders.forEach((f, i) => {
      const founderId = `founder-${f.founder_id}`;
      n.push({
        id: founderId,
        type: "founder",
        position: { x: 100 + (i % 5) * 200, y: 200 + Math.floor(i / 5) * 160 },
        data: {
          founderId: f.founder_id,
          founderName: f.founder_name,
          companyName: f.company_name,
          conviction: f.conviction,
          evidenceCoverage: f.evidence_coverage,
          recommendation: f.recommendation,
          coldStart: f.cold_start === true,
        },
      });
      e.push({
        id: `e-${f.sourcing_channel}-${f.founder_id}`,
        source: `channel-${f.sourcing_channel}`,
        target: founderId,
      });
    });

    // Founder nodes (middle row) — inbox (only those not already in outbound)
    const outboundIds = new Set(outbound?.founders.map((f) => f.founder_id));
    inbox?.cards
      .filter((c) => !outboundIds.has(c.founder_id))
      .forEach((f, i) => {
        n.push({
          id: `founder-${f.founder_id}`,
          type: "founder",
          position: { x: 100 + (i % 5) * 200, y: 400 + Math.floor(i / 5) * 160 },
          data: {
            founderId: f.founder_id,
            founderName: f.founder_name,
            companyName: f.company_name,
            conviction: f.conviction,
            evidenceCoverage: f.evidence_coverage,
            recommendation: f.recommendation,
            coldStart: f.cold_start === true,
          },
        });
      });

    return { nodes: n, edges: e };
  }, [outbound, inbox]);

  const onNodeClick: NodeMouseHandler = useCallback((_, node) => {
    setSelectedNode(node);
  }, []);

  return (
    <AppShell>
      <div className="h-full flex flex-col">
        <header className="px-8 py-4 border-b border-border">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Network View</h1>
          <p className="text-sm text-text-muted mt-1">
            Founders ↔ sourcing channels ↔ institutions as a connected graph.
          </p>
        </header>

        {outboundLoading && (
          <div className="flex items-center justify-center py-12 text-sm text-text-muted">
            <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading network…
          </div>
        )}
        {outboundError && (
          <div className="m-8 flex items-center gap-2 p-4 rounded-md border border-error-border bg-error-bg text-sm text-error">
            <AlertCircle className="w-4 h-4" />
            {(outboundError as Error).message}
          </div>
        )}

        <div className="flex-1 flex">
          <div className="flex-1 relative">
            {nodes.length > 0 && (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                onNodeClick={onNodeClick}
                defaultEdgeOptions={defaultEdgeOptions}
                nodesDraggable
                nodesConnectable={false}
                onlyRenderVisibleElements
                minZoom={0.2}
                maxZoom={2}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                proOptions={{ hideAttribution: true }}
                colorMode="dark"
              >
                <Background color="rgba(255,255,255,0.03)" gap={20} />
                <Controls className="!bg-card !border-border" />
                <MiniMap
                  className="!bg-card !border-border"
                  nodeColor={(node) => {
                    if (node.type === "founder") return "#5e6ad2";
                    if (node.type === "channel") return "#3ecf8e";
                    return "#6b7280";
                  }}
                  maskColor="rgba(11, 15, 25, 0.7)"
                />
              </ReactFlow>
            )}
          </div>

          {/* Node detail sidebar */}
          {selectedNode && (
            <aside className="w-80 border-l border-border bg-card p-4 overflow-auto">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-text-primary">Node Detail</h3>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-text-muted hover:text-text-primary text-xs"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-3 text-xs">
                {selectedNode.type === "founder" && (
                  <>
                    <div>
                      <div className="text-text-muted">Name</div>
                      <div className="font-bold text-text-primary">
                        {(selectedNode.data as FounderNodeData).founderName}
                      </div>
                    </div>
                    <div>
                      <div className="text-text-muted">Company</div>
                      <div className="text-text-secondary">
                        {(selectedNode.data as FounderNodeData).companyName || "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-text-muted">Conviction</div>
                      <div className="font-mono text-text-primary" data-numeric>
                        {(selectedNode.data as FounderNodeData).conviction?.toFixed(1) ?? "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-text-muted">Recommendation</div>
                      <Badge variant="outline">
                        {(selectedNode.data as FounderNodeData).recommendation || "—"}
                      </Badge>
                    </div>
                    <a
                      href={`/founders/${(selectedNode.data as FounderNodeData).founderId}`}
                      className="block mt-3"
                    >
                      <Button size="sm">Open Memo →</Button>
                    </a>
                  </>
                )}
                {selectedNode.type === "channel" && (
                  <>
                    <div>
                      <div className="text-text-muted">Channel</div>
                      <div className="font-bold text-text-primary capitalize">
                        {(selectedNode.data as ChannelNodeData).channelType}
                      </div>
                    </div>
                    <div>
                      <div className="text-text-muted">Signal Count</div>
                      <div className="font-mono text-text-primary" data-numeric>
                        {(selectedNode.data as ChannelNodeData).signalCount}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </aside>
          )}
        </div>

        {/* Legend */}
        <div className="px-8 py-3 border-t border-border flex items-center gap-4 text-[10px] text-text-muted">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full border border-border-strong" /> Founder
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-success/30" /> Channel
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm border border-warning/40" /> Cold-start
          </span>
        </div>
      </div>
    </AppShell>
  );
}
