/** Scene 5 (0:15-0:22): Three axes — Founder, Market, Idea — independent score bars, NEVER averaged. */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const AXES = [
  { label: "FOUNDER", color: "#5e6ad2", targetScore: 78, angle: -30 },
  { label: "MARKET", color: "#5e6ad2", targetScore: 52, angle: 30 },
  { label: "IDEA-VS-MARKET", color: "#5e6ad2", targetScore: 85, angle: 90 },
];

export const Scene5Axes: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Central core (smaller) */}
        <circle cx="960" cy="540" r="15" fill="#5e6ad2" opacity="0.4" />
        
        {/* "NEVER AVERAGED" label */}
        {frame > 60 && (
          <text x="960" y="300" fill="#d44a5c" fontSize="16" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [60, 80], [0, 0.7])}>
            NEVER AVERAGED — THE DISAGREEMENT IS THE SIGNAL
          </text>
        )}

        {/* Three parallel score bars */}
        {AXES.map((axis, i) => {
          const scoreProgress = interpolate(
            frame,
            [10 + i * 15, 60 + i * 15],
            [0, axis.targetScore],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }
          );
          const barY = 380 + i * 120;
          const barWidth = 500;
          const filledWidth = (scoreProgress / 100) * barWidth;
          const labelOpacity = interpolate(frame, [i * 10, i * 10 + 20], [0, 1], { extrapolateLeft: "clamp" });

          return (
            <g key={i}>
              {/* Label */}
              <text x={960 - barWidth / 2 - 20} y={barY + 20} fill="#9ca3af" fontSize="16" fontFamily="monospace" textAnchor="end" opacity={labelOpacity}>
                {axis.label}
              </text>
              
              {/* Bar background */}
              <rect x={960 - barWidth / 2} y={barY} width={barWidth} height="24" rx="4" fill="#14151a" stroke="#4a3a1a" strokeWidth="1" opacity={labelOpacity} />
              
              {/* Filled portion */}
              <rect x={960 - barWidth / 2} y={barY} width={filledWidth} height="24" rx="4" fill={axis.color} opacity={labelOpacity * 0.7} />
              
              {/* Score number */}
              <text x={960 + barWidth / 2 + 20} y={barY + 20} fill="#e6e6e6" fontSize="20" fontFamily="monospace" fontWeight="bold" opacity={labelOpacity}>
                {Math.round(scoreProgress)}
              </text>

              {/* "NOT MERGED" indicator — visual gap between bars */}
              {i < 2 && (
                <line x1={960 - barWidth / 2} y1={barY + 40} x2={960 + barWidth / 2} y2={barY + 40} stroke="#4a3a1a" strokeWidth="0.5" strokeDasharray="4 8" opacity="0.3" />
              )}
            </g>
          );
        })}

        {/* Contrast: a crossed-out single "average" bar at bottom */}
        {frame > 120 && (
          <g opacity={interpolate(frame, [120, 140], [0, 0.4])}>
            <rect x={960 - 250} y={740} width={500} height="20" rx="3" fill="#6b7280" opacity="0.2" />
            <text x="960" y="755" fill="#6b7280" fontSize="12" fontFamily="monospace" textAnchor="middle">AVERAGE</text>
            <line x1={960 - 280} y1="730" x2={960 + 280} y2="770" stroke="#d44a5c" strokeWidth="2" />
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
