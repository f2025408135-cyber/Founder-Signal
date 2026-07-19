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
import { Building, FileText, Github, Newspaper, Rocket, Snowflake } from "lucide-react";
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
    <div className={cn("min-w-[160px] rounded-lg border bg-card p-3", data.coldStart ? "border-warning-border" : "border-border-strong")}>
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !bg-accent" />
      <div className="mb-2 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-neutral-bg text-xs font-bold text-text-primary">
          {data.founderName.charAt(0)}
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-bold text-text-primary">{data.founderName}</div>
          <div className="truncate text-xs text-text-muted">{data.companyName || "Company not disclosed"}</div>
        </div>
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between"><span className="text-text-muted">Conviction</span><span className="font-mono text-text-primary">{data.conviction?.toFixed(0) ?? "pending"}</span></div>
        <div className="flex justify-between"><span className="text-text-muted">Evidence</span><span className="font-mono text-text-primary">{data.evidenceCoverage?.toFixed(2) ?? "pending"}</span></div>
        {data.coldStart && <div className="flex items-center gap-1 text-warning"><Snowflake className="h-3 w-3" /><span className="text-[10px]">cold-start</span></div>}
      </div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !bg-accent" />
    </div>
  );
}

function ChannelNodeComponent({ data }: { data: ChannelNodeData }) {
  const config = channelConfig[data.channelType] ?? channelConfig.github;
  const Icon = config.icon;
  return (
    <div className="flex min-w-[120px] items-center gap-2 rounded-full border border-border-strong bg-card p-3">
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !bg-accent" />
      <div className={cn("flex h-6 w-6 items-center justify-center rounded-full", config.bg, config.color)}><Icon className="h-3.5 w-3.5" /></div>
      <div><div className="text-xs font-bold capitalize text-text-primary">{data.channelType}</div><div className="text-[10px] text-text-muted">{data.signalCount} signals</div></div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !bg-accent" />
    </div>
  );
}

const nodeTypes = { founder: FounderNodeComponent, channel: ChannelNodeComponent };
const defaultEdgeOptions = { type: "smoothstep", style: { stroke: "var(--color-border-strong)", strokeWidth: 1.5 } };

export default function NetworkCanvas({ inbound, outbound }: { inbound: InboxResponse; outbound: OutboundCard[] }) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const channels = [...new Set(outbound.map((founder) => founder.sourcing_channel))];
    channels.forEach((channel, index) => {
      nodes.push({ id: `channel-${channel}`, type: "channel", position: { x: 200 + index * 200, y: 0 }, data: { channelType: channel, signalCount: outbound.filter((founder) => founder.sourcing_channel === channel).length } });
    });
    outbound.forEach((founder, index) => {
      const id = `founder-${founder.founder_id}`;
      nodes.push({ id, type: "founder", position: { x: 100 + (index % 5) * 200, y: 200 + Math.floor(index / 5) * 160 }, data: founderData(founder) });
      edges.push({ id: `edge-${founder.sourcing_channel}-${founder.founder_id}`, source: `channel-${founder.sourcing_channel}`, target: id });
    });
    const outboundIds = new Set(outbound.map((founder) => founder.founder_id));
    inbound.cards.filter((founder) => !outboundIds.has(founder.founder_id)).forEach((founder, index) => {
      nodes.push({ id: `founder-${founder.founder_id}`, type: "founder", position: { x: 100 + (index % 5) * 200, y: 400 + Math.floor(index / 5) * 160 }, data: founderData(founder) });
    });
    return { nodes, edges };
  }, [inbound, outbound]);
  const onNodeClick: NodeMouseHandler = useCallback((_, node) => setSelectedNode(node), []);

  return (
    <div className="flex min-h-[560px] flex-1">
      <div className="relative min-h-[560px] flex-1">
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodeClick={onNodeClick} defaultEdgeOptions={defaultEdgeOptions} nodesDraggable nodesConnectable={false} onlyRenderVisibleElements minZoom={0.2} maxZoom={2} fitView fitViewOptions={{ padding: 0.2 }} proOptions={{ hideAttribution: true }} colorMode="dark">
          <Background color="var(--color-border)" gap={20} />
          <Controls className="!border-border !bg-card" />
          <MiniMap className="!border-border !bg-card" nodeColor={(node) => node.type === "channel" ? "var(--color-success)" : "var(--color-accent)"} maskColor="var(--color-canvas-base)" />
        </ReactFlow>
      </div>
      {selectedNode && <NodeDetail node={selectedNode} onClose={() => setSelectedNode(null)} />}
    </div>
  );
}

function founderData(founder: OutboundCard | InboxResponse["cards"][number]): FounderNodeData {
  return { founderId: founder.founder_id, founderName: founder.founder_name, companyName: founder.company_name, conviction: founder.conviction, evidenceCoverage: founder.evidence_coverage, recommendation: founder.recommendation, coldStart: founder.cold_start === true };
}

function NodeDetail({ node, onClose }: { node: Node; onClose: () => void }) {
  const data = node.data as FounderNodeData | ChannelNodeData;
  const isFounder = node.type === "founder";
  return <aside className="w-80 overflow-auto border-l border-border bg-card p-4"><div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-bold text-text-primary">Node Detail</h2><button type="button" onClick={onClose} aria-label="Close node detail" className="rounded-sm text-text-muted hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40">Close</button></div>{isFounder ? <div className="space-y-3 text-xs"><div><div className="text-text-muted">Name</div><div className="font-bold text-text-primary">{(data as FounderNodeData).founderName}</div></div><div><div className="text-text-muted">Company</div><div className="text-text-secondary">{(data as FounderNodeData).companyName || "Not disclosed"}</div></div><div><div className="text-text-muted">Recommendation</div><Badge variant="outline">{(data as FounderNodeData).recommendation || "Still processing"}</Badge></div><Button asChild size="sm"><Link href={`/founders/${(data as FounderNodeData).founderId}`}>Open Memo</Link></Button></div> : <div className="space-y-3 text-xs"><div><div className="text-text-muted">Channel</div><div className="font-bold capitalize text-text-primary">{(data as ChannelNodeData).channelType}</div></div><div><div className="text-text-muted">Signal count</div><div className="font-mono text-text-primary">{(data as ChannelNodeData).signalCount}</div></div></div>}</aside>;
}
