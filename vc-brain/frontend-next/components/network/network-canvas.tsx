"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Building, FileText, Github, Newspaper, Rocket, Snowflake, X, ArrowRight } from "lucide-react";
import { Badge, Button } from "@/components/ui/primitives";
import type { InboxResponse, OutboundCard } from "@/lib/types";
import { cn } from "@/lib/utils";

interface FounderNodeData {
  founderId: string;
  founderName: string;
  companyName: string | null;
  conviction: number | null;
  evidenceCoverage: number | null;
  recommendation: string | null;
  coldStart: boolean;
  sector: string | null;
  geography: string | null;
  [key: string]: unknown;
}

interface ChannelNodeData {
  channelType: string;
  signalCount: number;
  [key: string]: unknown;
}

const channelConfig: Record<string, { color: string; bg: string; icon: typeof Github; glow: string }> = {
  github: { color: "#3ecf8e", bg: "rgba(62,207,142,0.12)", icon: Github, glow: "rgba(62,207,142,0.15)" },
  arxiv: { color: "#5e6ad2", bg: "rgba(94,106,210,0.12)", icon: FileText, glow: "rgba(94,106,210,0.15)" },
  producthunt: { color: "#d4a843", bg: "rgba(212,168,67,0.12)", icon: Rocket, glow: "rgba(212,168,67,0.15)" },
  hackernews: { color: "#d4a843", bg: "rgba(212,168,67,0.12)", icon: Newspaper, glow: "rgba(212,168,67,0.15)" },
  accelerator: { color: "#5e6ad2", bg: "rgba(94,106,210,0.12)", icon: Building, glow: "rgba(94,106,210,0.15)" },
};

function FounderNodeComponent({ data, selected }: { data: FounderNodeData; selected?: boolean }) {
  const recColor = data.recommendation === "fast_pass" ? "#3ecf8e" : data.recommendation === "deep_dive" ? "#5e6ad2" : data.recommendation === "reject" ? "#d44a5c" : "#6b7280";

  return (
    <div
      className={cn("metal-panel min-w-[170px] max-w-[200px] rounded-md p-3 transition-all", selected && "ring-2 ring-accent/50")}
      style={data.coldStart ? { borderColor: "rgba(212,168,67,0.4)" } : undefined}
    >
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-0 !bg-accent" />

      {/* Avatar + name */}
      <div className="mb-2.5 flex items-center gap-2">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
          style={{ background: `linear-gradient(135deg, ${recColor}30, ${recColor}10)`, color: recColor, border: `1px solid ${recColor}40` }}
        >
          {data.founderName.charAt(0)}
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-bold text-text-primary">{data.founderName}</div>
          <div className="truncate text-xs text-text-muted">{data.companyName || "—"}</div>
        </div>
        {data.coldStart && <Snowflake className="h-3 w-3 shrink-0 text-warning" />}
      </div>

      {/* Stats grid */}
      <div className="space-y-1.5 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-text-muted">Conviction</span>
          <span className="font-mono font-bold text-text-primary" data-numeric>{data.conviction?.toFixed(0) ?? "—"}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-text-muted">Evidence</span>
          <span className="font-mono text-text-secondary" data-numeric>{data.evidenceCoverage?.toFixed(2) ?? "—"}</span>
        </div>
        {data.recommendation && (
          <div className="flex items-center justify-between">
            <span className="text-text-muted">Verdict</span>
            <span
              className="rounded-full px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase"
              style={{ color: recColor, background: `${recColor}15`, border: `1px solid ${recColor}30` }}
            >
              {data.recommendation}
            </span>
          </div>
        )}
      </div>

      {/* Geo + sector tags */}
      {(data.geography || data.sector) && (
        <div className="mt-2 flex flex-wrap gap-1">
          {data.geography && <span className="text-[8px] font-mono text-text-subtle">{data.geography}</span>}
          {data.sector && <span className="text-[8px] font-mono text-text-subtle">· {data.sector}</span>}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-0 !bg-accent" />
    </div>
  );
}

function ChannelNodeComponent({ data }: { data: ChannelNodeData }) {
  const config = channelConfig[data.channelType] ?? channelConfig.github;
  const Icon = config.icon;

  return (
    <div
      className="metal-panel flex min-w-[130px] items-center gap-2.5 rounded-md p-3"
      style={{ boxShadow: `0 0 20px ${config.glow}, inset 0 1px 0 rgba(240,244,248,0.12), inset 0 -1px 0 rgba(0,0,0,0.4)` }}
    >
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-0" style={{ background: config.color }} />

      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
        style={{ background: config.bg, border: `1px solid ${config.color}40` }}
      >
        <Icon className="h-4 w-4" style={{ color: config.color }} />
      </div>

      <div>
        <div className="text-xs font-bold capitalize text-text-primary">{data.channelType}</div>
        <div className="text-[10px] font-mono text-text-muted">{data.signalCount} signals</div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-0" style={{ background: config.color }} />
    </div>
  );
}

const nodeTypes = { founder: FounderNodeComponent, channel: ChannelNodeComponent };
const defaultEdgeOptions = {
  type: "smoothstep",
  style: { stroke: "rgba(94,106,210,0.2)", strokeWidth: 1.5 },
  animated: false,
};

export default function NetworkCanvas({ inbound, outbound }: { inbound: InboxResponse; outbound: OutboundCard[] }) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Channel nodes (top row)
    const channels = [...new Set(outbound.map((f) => f.sourcing_channel))];
    channels.forEach((channel, index) => {
      const count = outbound.filter((f) => f.sourcing_channel === channel).length;
      nodes.push({
        id: `channel-${channel}`,
        type: "channel",
        position: { x: 250 + index * 220, y: 0 },
        data: { channelType: channel, signalCount: count },
      });
    });

    // Outbound founders (middle area)
    outbound.forEach((founder, index) => {
      const id = `founder-${founder.founder_id}`;
      nodes.push({
        id,
        type: "founder",
        position: { x: 100 + (index % 5) * 220, y: 200 + Math.floor(index / 5) * 180 },
        data: founderData(founder),
      });
      edges.push({
        id: `edge-${founder.sourcing_channel}-${founder.founder_id}`,
        source: `channel-${founder.sourcing_channel}`,
        target: id,
        style: { stroke: channelConfig[founder.sourcing_channel]?.color || "#5e6ad2", strokeWidth: 1.5, opacity: 0.3 },
      });
    });

    // Inbound-only founders (lower area)
    const outboundIds = new Set(outbound.map((f) => f.founder_id));
    inbound.cards.filter((f) => !outboundIds.has(f.founder_id)).forEach((founder, index) => {
      nodes.push({
        id: `founder-${founder.founder_id}`,
        type: "founder",
        position: { x: 100 + (index % 5) * 220, y: 450 + Math.floor(index / 5) * 180 },
        data: founderData(founder),
      });
    });

    return { nodes, edges };
  }, [inbound, outbound]);

  const onNodeClick: NodeMouseHandler = useCallback((_, node) => setSelectedNode(node), []);

  return (
    <div className="flex min-h-[560px] flex-1">
      {/* React Flow canvas */}
      <div className="relative min-h-[560px] flex-1">
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
          fitViewOptions={{ padding: 0.15 }}
          proOptions={{ hideAttribution: true }}
          colorMode="dark"
        >
          <Background color="rgba(255,255,255,0.03)" gap={24} />
          <Controls className="!metal-panel !rounded-sm !border-border-strong" showInteractive={false} />
          <MiniMap
            className="!metal-panel !rounded-sm !border-border-strong"
            nodeColor={(node) => {
              if (node.type === "channel") return channelConfig[(node.data as ChannelNodeData).channelType]?.color || "#5e6ad2";
              return "#5e6ad2";
            }}
            maskColor="rgba(10, 9, 8, 0.7)"
            pannable
            zoomable
          />
        </ReactFlow>
      </div>

      {/* Detail sidebar */}
      {selectedNode && <NodeDetail node={selectedNode} onClose={() => setSelectedNode(null)} />}
    </div>
  );
}

function founderData(founder: OutboundCard | InboxResponse["cards"][number]): FounderNodeData {
  return {
    founderId: founder.founder_id,
    founderName: founder.founder_name,
    companyName: founder.company_name,
    conviction: founder.conviction,
    evidenceCoverage: founder.evidence_coverage,
    recommendation: founder.recommendation,
    coldStart: founder.cold_start === true,
    sector: founder.sector,
    geography: founder.geography,
  };
}

function NodeDetail({ node, onClose }: { node: Node; onClose: () => void }) {
  const data = node.data as FounderNodeData | ChannelNodeData;
  const isFounder = node.type === "founder";

  return (
    <aside className="metal-panel fixed inset-x-3 bottom-3 z-30 max-h-[55vh] w-auto overflow-auto rounded-md p-5 shadow-[0_20px_50px_-24px_rgba(0,0,0,.95)] lg:static lg:max-h-none lg:w-80 lg:rounded-none lg:shadow-none">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="technical-label">Inspect</p>
          <h2 className="text-sm font-bold text-text-primary">{isFounder ? "Founder Detail" : "Channel Detail"}</h2>
        </div>
        <button onClick={onClose} aria-label="Close" className="rounded-sm p-1 text-text-muted hover:bg-elevated hover:text-text-primary">
          <X className="h-4 w-4" />
        </button>
      </div>

      {isFounder ? (
        <div className="space-y-4">
          {/* Avatar + name */}
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-lg font-bold text-accent border border-accent/30">
              {(data as FounderNodeData).founderName.charAt(0)}
            </div>
            <div>
              <div className="text-base font-bold text-text-primary">{(data as FounderNodeData).founderName}</div>
              <div className="text-sm text-text-muted">{(data as FounderNodeData).companyName || "Company not disclosed"}</div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-md border border-border bg-canvas-base/40 p-3">
              <div className="text-[10px] uppercase tracking-wider text-text-muted">Conviction</div>
              <div className="font-mono text-xl font-bold text-text-primary" data-numeric>{(data as FounderNodeData).conviction?.toFixed(0) ?? "—"}</div>
            </div>
            <div className="rounded-md border border-border bg-canvas-base/40 p-3">
              <div className="text-[10px] uppercase tracking-wider text-text-muted">Evidence</div>
              <div className="font-mono text-xl font-bold text-text-primary" data-numeric>{(data as FounderNodeData).evidenceCoverage?.toFixed(2) ?? "—"}</div>
            </div>
          </div>

          {/* Tags */}
          <div className="flex flex-wrap gap-2">
            {(data as FounderNodeData).recommendation && (
              <Badge variant="outline" className="capitalize">{(data as FounderNodeData).recommendation}</Badge>
            )}
            {(data as FounderNodeData).coldStart && (
              <Badge variant="warning"><Snowflake className="mr-1 h-2.5 w-2.5" /> cold-start</Badge>
            )}
            {(data as FounderNodeData).geography && (
              <Badge variant="secondary">{(data as FounderNodeData).geography}</Badge>
            )}
            {(data as FounderNodeData).sector && (
              <Badge variant="secondary">{(data as FounderNodeData).sector}</Badge>
            )}
          </div>

          {/* Open memo button */}
          <Button asChild className="w-full">
            <Link href={`/founders/${(data as FounderNodeData).founderId}`}>
              Open Investment Memo <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-full"
              style={{ background: channelConfig[(data as ChannelNodeData).channelType]?.bg, border: `1px solid ${channelConfig[(data as ChannelNodeData).channelType]?.color}40` }}
            >
              {(() => {
                const Icon = channelConfig[(data as ChannelNodeData).channelType]?.icon || Github;
                return <Icon className="h-5 w-5" style={{ color: channelConfig[(data as ChannelNodeData).channelType]?.color }} />;
              })()}
            </div>
            <div>
              <div className="text-base font-bold capitalize text-text-primary">{(data as ChannelNodeData).channelType}</div>
              <div className="text-sm text-text-muted">Sourcing channel</div>
            </div>
          </div>

          <div className="rounded-md border border-border bg-canvas-base/40 p-3">
            <div className="text-[10px] uppercase tracking-wider text-text-muted">Signals Detected</div>
            <div className="font-mono text-2xl font-bold text-text-primary" data-numeric>{(data as ChannelNodeData).signalCount}</div>
          </div>
        </div>
      )}
    </aside>
  );
}
