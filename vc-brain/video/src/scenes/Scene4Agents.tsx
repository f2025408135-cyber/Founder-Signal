/** Scene 4 (0:12-0:15): Central node splits into six labeled agent nodes fanning outward. */
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";

const AGENTS = [
  { name: "INGESTION", angle: -90, color: "#5e6ad2" },
  { name: "FOUNDER", angle: -30, color: "#5e6ad2" },
  { name: "MARKET", angle: 30, color: "#5e6ad2" },
  { name: "IDEA-VS-MARKET", angle: 90, color: "#5e6ad2" },
  { name: "VALIDATOR", angle: 150, color: "#3ecf8e" },
  { name: "AGGREGATOR", angle: 210, color: "#d4a843" },
];

export const Scene4Agents: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fanOut = spring({ frame, fps, config: { damping: 14, stiffness: 60 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Central core */}
        <circle cx="960" cy="540" r="25" fill="#5e6ad2" opacity="0.8" />
        <circle cx="960" cy="540" r="40" fill="none" stroke="#5e6ad2" strokeWidth="1" opacity="0.3" />
        
        {/* Six agent nodes */}
        {AGENTS.map((agent, i) => {
          const rad = (agent.angle * Math.PI) / 180;
          const dist = 220 * fanOut;
          const x = 960 + Math.cos(rad - Math.PI / 2) * dist;
          const y = 540 + Math.sin(rad - Math.PI / 2) * dist;
          const labelOpacity = interpolate(frame, [20 + i * 3, 40 + i * 3], [0, 1], { extrapolateLeft: "clamp" });

          return (
            <g key={i}>
              {/* Connection line */}
              <line x1="960" y1="540" x2={x} y2={y} stroke="#4a3a1a" strokeWidth="1" opacity={0.4 * fanOut} />
              {/* Node circle */}
              <circle cx={x} cy={y} r="28" fill="#14151a" stroke={agent.color} strokeWidth="2" opacity={fanOut} />
              <circle cx={x} cy={y} r="8" fill={agent.color} opacity={fanOut * 0.6} />
              {/* Label */}
              <text
                x={x}
                y={y + 50}
                fill="#9ca3af"
                fontSize="14"
                fontFamily="monospace"
                textAnchor="middle"
                opacity={labelOpacity}
              >
                {agent.name}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
