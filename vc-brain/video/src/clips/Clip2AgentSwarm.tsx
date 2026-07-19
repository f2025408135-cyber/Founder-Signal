/** CLIP 2: Six-Agent Swarm Architecture (12s, 360 frames)
 * 
 * Shows: The 8-node LangGraph pipeline — ingestion → [fetch_evidence || thesis_fit] → 
 * validator → [founder || market] → idea_vs_market → aggregator.
 * 
 * Animation: Nodes appear sequentially with connection lines, then "activate" with
 * flowing data particles showing parallel execution paths. The graph topology is
 * the star — viewers see exactly which nodes run in parallel vs sequential.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const C = { bg: "#0a0908", card: "#14151a", accent: "#5e6ad2", text: "#e6e6e6", muted: "#9ca3af", subtle: "#6b7280", success: "#3ecf8e", warning: "#d4a843", error: "#d44a5c", border: "rgba(255,255,255,0.06)", borderStrong: "rgba(255,255,255,0.12)" };

// Node positions (graph layout)
const NODES = [
  { id: "ingestion", label: "INGESTION", x: 960, y: 180, color: C.accent, appear: 0 },
  { id: "fetch_evidence", label: "FETCH\nEVIDENCE", x: 760, y: 360, color: C.accent, appear: 20 },
  { id: "thesis_fit", label: "THESIS\nFIT", x: 1160, y: 360, color: C.accent, appear: 25 },
  { id: "validator", label: "VALIDATOR", x: 960, y: 540, color: C.success, appear: 50 },
  { id: "founder", label: "FOUNDER", x: 760, y: 720, color: C.accent, appear: 80 },
  { id: "market", label: "MARKET", x: 1160, y: 720, color: C.accent, appear: 85 },
  { id: "idea_vs_market", label: "IDEA↔\nMARKET", x: 1160, y: 860, color: C.accent, appear: 120 },
  { id: "aggregator", label: "AGGREGATOR", x: 960, y: 960, color: C.warning, appear: 160 },
];

const EDGES = [
  { from: "ingestion", to: "fetch_evidence", parallel: true },
  { from: "ingestion", to: "thesis_fit", parallel: true },
  { from: "fetch_evidence", to: "validator", parallel: false },
  { from: "thesis_fit", to: "aggregator", parallel: false, dashed: true },
  { from: "validator", to: "founder", parallel: true },
  { from: "validator", to: "market", parallel: true },
  { from: "market", to: "idea_vs_market", parallel: false },
  { from: "founder", to: "aggregator", parallel: false },
  { from: "idea_vs_market", to: "aggregator", parallel: false },
];

const PARTICLES = Array.from({ length: 30 }, (_, i) => ({
  edgeIdx: i % EDGES.length,
  delay: 100 + i * 12,
  speed: 0.6 + Math.random() * 0.3,
}));

export const Clip2AgentSwarm: React.FC = () => {
  const frame = useCurrentFrame();

  const getNode = (id: string) => NODES.find(n => n.id === id)!;

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Title */}
        <text x="960" y="80" fill={C.text} fontSize="28" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 20], [0, 1])}>
          LangGraph Pipeline — 8 Nodes, Parallel Execution
        </text>

        {/* Edges (connection lines) */}
        {EDGES.map((edge, i) => {
          const from = getNode(edge.from);
          const to = getNode(edge.to);
          const edgeAppear = interpolate(frame, [from.appear + 10, from.appear + 25], [0, 1], { extrapolateLeft: "clamp" });
          
          return (
            <g key={i} opacity={edgeAppear}>
              <line
                x1={from.x} y1={from.y + 30}
                x2={to.x} y2={to.y - 30}
                stroke={edge.parallel ? C.success : C.accent}
                strokeWidth="1.5"
                opacity="0.3"
                strokeDasharray={edge.dashed ? "6 4" : "none"}
              />
              {/* Parallel indicator */}
              {edge.parallel && (
                <text
                  x={(from.x + to.x) / 2 + 15}
                  y={(from.y + to.y) / 2}
                  fill={C.success}
                  fontSize="9"
                  fontFamily="monospace"
                  opacity="0.4"
                >
                  ∥
                </text>
              )}
            </g>
          );
        })}

        {/* Data particles flowing along edges */}
        {PARTICLES.map((p, i) => {
          const edge = EDGES[p.edgeIdx];
          const from = getNode(edge.from);
          const to = getNode(edge.to);
          
          const progress = interpolate(frame, [p.delay, p.delay + 60], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          });
          
          if (progress <= 0 || progress >= 1) return null;
          
          const x = from.x + (to.x - from.x) * progress;
          const y = (from.y + 30) + ((to.y - 30) - (from.y + 30)) * progress;
          
          return (
            <circle key={i} cx={x} cy={y} r="3" fill={edge.parallel ? C.success : C.accent} opacity="0.8" />
          );
        })}

        {/* Nodes */}
        {NODES.map((node, i) => {
          const nodeAppear = interpolate(frame, [node.appear, node.appear + 15], [0, 1], { extrapolateLeft: "clamp" });
          const isActive = frame > node.appear + 20;
          const pulseScale = isActive ? 1 + Math.sin(frame * 0.08 + i) * 0.03 : 1;
          
          return (
            <g key={i} opacity={nodeAppear} transform={`translate(${node.x} ${node.y}) scale(${pulseScale})`}>
              {/* Glow when active */}
              {isActive && (
                <circle cx="0" cy="0" r="45" fill={node.color} opacity="0.08" />
              )}
              {/* Node body */}
              <rect x="-50" y="-28" width="100" height="56" rx="8" fill={C.card} stroke={node.color} strokeWidth="2" />
              {/* Node label (multi-line) */}
              {node.label.split("\n").map((line, j) => (
                <text key={j} x="0" y={-4 + j * 14} fill={node.color} fontSize="11" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
                  {line}
                </text>
              ))}
              {/* Active indicator dot */}
              {isActive && (
                <circle cx="38" cy="-18" r="4" fill={C.success} opacity="0.8">
                  <animate attributeName="opacity" values="0.4;1;0.4" dur="1s" repeatCount="indefinite" />
                </circle>
              )}
            </g>
          );
        })}

        {/* Parallel execution label */}
        {frame > 120 && (
          <g opacity={interpolate(frame, [120, 140], [0, 0.6])}>
            <rect x="200" y="350" width="180" height="24" rx="4" fill={C.card} stroke={C.success} strokeWidth="0.5" opacity="0.6" />
            <text x="290" y="366" fill={C.success} fontSize="11" fontFamily="monospace" textAnchor="middle">∥ PARALLEL EXECUTION</text>
          </g>
        )}

        {/* Legend */}
        {frame > 200 && (
          <g opacity={interpolate(frame, [200, 220], [0, 0.5])} transform="translate(100, 950)">
            <circle cx="0" cy="0" r="5" fill={C.accent} /><text x="15" y="4" fill={C.muted} fontSize="11" fontFamily="monospace">Worker Agent</text>
            <circle cx="160" cy="0" r="5" fill={C.success} /><text x="175" y="4" fill={C.muted} fontSize="11" fontFamily="monospace">Validator</text>
            <circle cx="300" cy="0" r="5" fill={C.warning} /><text x="315" y="4" fill={C.muted} fontSize="11" fontFamily="monospace">Aggregator (tool-less)</text>
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
