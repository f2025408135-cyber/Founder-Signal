/** CLIP 3: Three Independent Axes — Never Averaged (12s, 360 frames)
 * 
 * Shows: Founder / Market / Idea-vs-Market scores as three completely independent bars
 * that deliberately DON'T converge. The "disagreement IS the signal" concept.
 * 
 * Animation: Three bars animate independently with different target scores, then
 * a crossed-out "AVERAGE" bar appears and gets rejected. The geometric mean
 * formula appears at the end.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const C = { bg: "#0a0908", card: "#14151a", accent: "#5e6ad2", text: "#e6e6e6", muted: "#9ca3af", subtle: "#6b7280", success: "#3ecf8e", warning: "#d4a843", error: "#d44a5c", border: "rgba(255,255,255,0.06)", borderStrong: "rgba(255,255,255,0.12)" };

const AXES = [
  { label: "FOUNDER", target: 82, color: C.accent, y: 300 },
  { label: "MARKET", target: 38, color: C.warning, y: 420 },
  { label: "IDEA-VS-MARKET", target: 75, color: C.success, y: 540 },
];

export const Clip3ThreeAxes: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Title */}
        <text x="960" y="150" fill={C.text} fontSize="28" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 20], [0, 1])}>
          Three Independent Axes — NEVER Averaged
        </text>
        <text x="960" y="180" fill={C.muted} fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [0, 20], [0, 0.6])}>
          The disagreement IS the signal
        </text>

        {/* Three independent score bars */}
        {AXES.map((axis, i) => {
          const score = interpolate(frame, [30 + i * 20, 100 + i * 20], [0, axis.target], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
          const barWidth = 600;
          const filledWidth = (score / 100) * barWidth;
          const barX = 660;
          const labelOpacity = interpolate(frame, [20 + i * 15, 35 + i * 15], [0, 1], { extrapolateLeft: "clamp" });

          return (
            <g key={i} opacity={labelOpacity}>
              {/* Axis label */}
              <text x={barX - 20} y={axis.y + 20} fill={axis.color} fontSize="16" fontFamily="monospace" textAnchor="end" fontWeight="bold">{axis.label}</text>
              
              {/* Bar background */}
              <rect x={barX} y={axis.y} width={barWidth} height="28" rx="4" fill={C.card} stroke={C.borderStrong} strokeWidth="1" />
              
              {/* Filled portion */}
              <rect x={barX} y={axis.y} width={filledWidth} height="28" rx="4" fill={axis.color} opacity="0.6" />
              
              {/* 10-segment dividers */}
              {Array.from({ length: 9 }).map((_, j) => (
                <line key={j} x1={barX + (j + 1) * (barWidth / 10)} y1={axis.y} x2={barX + (j + 1) * (barWidth / 10)} y2={axis.y + 28} stroke={C.bg} strokeWidth="1" opacity="0.5" />
              ))}
              
              {/* Score number */}
              <text x={barX + barWidth + 20} y={axis.y + 20} fill={C.text} fontSize="24" fontFamily="monospace" fontWeight="bold" data-numeric>
                {Math.round(score)}
              </text>

              {/* "INDEPENDENT" label */}
              <text x={barX + barWidth / 2} y={axis.y - 8} fill={C.subtle} fontSize="9" fontFamily="monospace" textAnchor="middle" opacity="0.5">INDEPENDENT</text>
              
              {/* Visual gap between bars (NOT merged) */}
              {i < 2 && (
                <g opacity="0.3">
                  <line x1={barX} y1={axis.y + 40} x2={barX + barWidth} y2={axis.y + 40} stroke={C.border} strokeWidth="0.5" strokeDasharray="2 6" />
                  <text x={barX + barWidth / 2} y={axis.y + 50} fill={C.subtle} fontSize="8" fontFamily="monospace" textAnchor="middle">NOT MERGED</text>
                </g>
              )}
            </g>
          );
        })}

        {/* "NEVER AVERAGE" callout */}
        {frame > 120 && (
          <g opacity={interpolate(frame, [120, 140], [0, 1])}>
            <rect x="760" y="640" width="400" height="50" rx="8" fill={`${C.error}15`} stroke={C.error} strokeWidth="1" />
            <text x="960" y="672" fill={C.error} fontSize="16" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
              ✗ NEVER AVERAGE — THE DISAGREEMENT IS THE SIGNAL
            </text>
          </g>
        )}

        {/* Crossed-out "average" bar */}
        {frame > 160 && (
          <g opacity={interpolate(frame, [160, 180], [0, 0.4])}>
            <text x="640" y="780" fill={C.subtle} fontSize="12" fontFamily="monospace" textAnchor="end">AVERAGE</text>
            <rect x="660" y="760" width="600" height="20" rx="3" fill={C.subtle} opacity="0.15" />
            <rect x="660" y="760" width="380" height="20" rx="3" fill={C.subtle} opacity="0.3" />
            <text x="1290" y="775" fill={C.subtle} fontSize="16" fontFamily="monospace">65</text>
            {/* Big red X */}
            <line x1="640" y1="745" x2="1290" y2="795" stroke={C.error} strokeWidth="3" />
            <line x1="1290" y1="745" x2="640" y2="795" stroke={C.error} strokeWidth="3" />
          </g>
        )}

        {/* Geometric mean formula (the actual aggregation method) */}
        {frame > 220 && (
          <g opacity={interpolate(frame, [220, 250], [0, 1])}>
            <rect x="660" y="860" width="600" height="60" rx="8" fill={`${C.accent}10`} stroke={C.accent} strokeWidth="0.5" />
            <text x="960" y="888" fill={C.accent} fontSize="14" fontFamily="monospace" textAnchor="middle">
              CONVICTION = (founder × market × idea × thesis_fit) ^ 0.25
            </text>
            <text x="960" y="908" fill={C.muted} fontSize="11" fontFamily="monospace" textAnchor="middle">
              Geometric mean — reveals weakness arithmetic mean hides
            </text>
          </g>
        )}

        {/* Arrow showing the hidden weakness */}
        {frame > 260 && (
          <g opacity={interpolate(frame, [260, 280], [0, 0.6])}>
            <text x="1280" y="420" fill={C.error} fontSize="12" fontFamily="monospace">← Market weakness</text>
            <text x="1280" y="438" fill={C.error} fontSize="10" fontFamily="monospace" opacity="0.6">hidden by avg=65</text>
            <line x1="1270" y1="430" x2="1180" y2="430" stroke={C.error} strokeWidth="1" strokeDasharray="3 3" />
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
