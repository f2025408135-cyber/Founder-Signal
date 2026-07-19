/** Scene 9 (0:39-0:44): Final memo expands, shows citation tags, settles. */
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";

const CITATIONS = [
  { x: 890, y: 500, color: "#3ecf8e", label: "verified", delay: 30 },
  { x: 1030, y: 510, color: "#3ecf8e", label: "verified", delay: 40 },
  { x: 885, y: 540, color: "#d4a843", label: "unverifiable", delay: 50 },
  { x: 1035, y: 560, color: "#3ecf8e", label: "verified", delay: 60 },
  { x: 890, y: 580, color: "#d44a5c", label: "contradicted", delay: 70 },
  { x: 1030, y: 590, color: "#3ecf8e", label: "verified", delay: 80 },
];

export const Scene9Memo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 60 } });
  const memoOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <g transform={`translate(960, 540) scale(${scale}) translate(-960, -540)`} opacity={memoOpacity}>
          {/* Memo document */}
          <rect x="800" y="340" width="320" height="400" rx="8" fill="#14151a" stroke="#5e6ad2" strokeWidth="1.5" opacity="0.9" />
          
          {/* Header bar */}
          <rect x="800" y="340" width="320" height="40" rx="8" fill="#5e6ad2" opacity="0.15" />
          <text x="960" y="366" fill="#5e6ad2" fontSize="14" fontFamily="monospace" textAnchor="middle" fontWeight="bold">INVESTMENT MEMO</text>

          {/* Content lines */}
          {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
            <rect key={i} x="820" y={400 + i * 25} width={i % 3 === 0 ? 240 : 180} height="6" rx="2" fill="#e6e6e6" opacity="0.2" />
          ))}

          {/* Section headings */}
          <text x="820" y="410" fill="#9ca3af" fontSize="9" fontFamily="monospace">COMPANY SNAPSHOT</text>
          <text x="820" y="460" fill="#9ca3af" fontSize="9" fontFamily="monospace">TRACTION & KPIs</text>
          <text x="820" y="510" fill="#9ca3af" fontSize="9" fontFamily="monospace">DUE DILIGENCE LOG</text>

          {/* Citation tags along edges */}
          {CITATIONS.map((cit, i) => {
            const citOpacity = interpolate(frame, [cit.delay, cit.delay + 15], [0, 1], { extrapolateLeft: "clamp" });
            return (
              <g key={i} opacity={citOpacity}>
                <circle cx={cit.x} cy={cit.y} r="5" fill={cit.color} opacity="0.8" />
                <circle cx={cit.x} cy={cit.y} r="8" fill="none" stroke={cit.color} strokeWidth="1" opacity="0.3" />
              </g>
            );
          })}

          {/* "Every claim traceable" label */}
          {frame > 90 && (
            <text x="960" y="800" fill="#3ecf8e" fontSize="12" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [90, 110], [0, 0.8])}>
              EVERY CLAIM TRACEABLE TO ITS SOURCE
            </text>
          )}
          {frame > 100 && (
            <text x="960" y="830" fill="#9ca3af" fontSize="11" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [100, 120], [0, 0.6])}>
              READY IN MINUTES, NOT WEEKS
            </text>
          )}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
