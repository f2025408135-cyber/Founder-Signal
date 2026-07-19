/** Scene 8 (0:34-0:39): Aggregator — six outputs flow in, NO new external arrows, memo forms. */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const NODES = [
  { angle: -90, label: "INGESTION", color: "#5e6ad2" },
  { angle: -30, label: "FOUNDER", color: "#5e6ad2" },
  { angle: 30, label: "MARKET", color: "#5e6ad2" },
  { angle: 90, label: "IDEA", color: "#5e6ad2" },
  { angle: 150, label: "VALIDATOR", color: "#3ecf8e" },
  { angle: 210, label: "AGGREGATOR", color: "#d4a843" },
];

export const Scene8Aggregator: React.FC = () => {
  const frame = useCurrentFrame();
  const converge = interpolate(frame, [30, 90], [0, 1], { extrapolateLeft: "clamp", easing: Easing.inOut(Easing.cubic) });
  const memoForm = interpolate(frame, [80, 120], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* "NO NEW FACTS ENTER HERE" label */}
        <text x="960" y="280" fill="#d4a843" fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [0, 20], [0, 0.6])}>
          TOOL-LESS SYNTHESIZER — NO NEW FACTS ENTER HERE
        </text>

        {/* Source nodes converging */}
        {NODES.map((node, i) => {
          const rad = (node.angle * Math.PI) / 180;
          const startDist = 250;
          const endDist = 250 * (1 - converge * 0.85);
          const x1 = 960 + Math.cos(rad - Math.PI / 2) * startDist;
          const y1 = 540 + Math.sin(rad - Math.PI / 2) * startDist;
          const x2 = 960 + Math.cos(rad - Math.PI / 2) * endDist;
          const y2 = 540 + Math.sin(rad - Math.PI / 2) * endDist;
          
          return (
            <g key={i}>
              {/* Connection line — only from existing nodes, NO external arrows */}
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={node.color} strokeWidth="1.5" opacity={0.4 * (1 - converge * 0.5)} />
              {/* Moving dot along the line */}
              <circle cx={x2} cy={y2} r="6" fill={node.color} opacity={(1 - converge * 0.7)} />
              {/* Node label */}
              <text x={x1} y={y1 + (node.angle > 0 ? 25 : -15)} fill="#9ca3af" fontSize="11" fontFamily="monospace" textAnchor="middle" opacity={1 - converge}>
                {node.label}
              </text>
            </g>
          );
        })}

        {/* No-external-arrows indicator — crossed out incoming arrow */}
        {frame > 20 && frame < 80 && (
          <g opacity={interpolate(frame, [20, 30, 70, 80], [0, 0.5, 0.5, 0])}>
            <line x1="960" y1="200" x2="960" y2="400" stroke="#6b7280" strokeWidth="1" strokeDasharray="4 4" />
            <line x1="940" y1="250" x2="980" y2="210" stroke="#d44a5c" strokeWidth="2" />
            <line x1="980" y1="250" x2="940" y2="210" stroke="#d44a5c" strokeWidth="2" />
            <text x="960" y="190" fill="#d44a5c" fontSize="10" fontFamily="monospace" textAnchor="middle">NO EXTERNAL INPUT</text>
          </g>
        )}

        {/* Central memo forming */}
        {memoForm > 0 && (
          <g opacity={memoForm}>
            <rect x="890" y="490" width="140" height="100" rx="4" fill="#14151a" stroke="#d4a843" strokeWidth="2" />
            <rect x="905" y="510" width="110" height="4" rx="2" fill="#d4a843" opacity="0.4" />
            <rect x="905" y="520" width="90" height="3" rx="1.5" fill="#e6e6e6" opacity="0.3" />
            <rect x="905" y="530" width="100" height="3" rx="1.5" fill="#e6e6e6" opacity="0.3" />
            <rect x="905" y="540" width="80" height="3" rx="1.5" fill="#e6e6e6" opacity="0.3" />
            <rect x="905" y="550" width="95" height="3" rx="1.5" fill="#e6e6e6" opacity="0.3" />
            <text x="960" y="580" fill="#d4a843" fontSize="10" fontFamily="monospace" textAnchor="middle">MEMO</text>
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
