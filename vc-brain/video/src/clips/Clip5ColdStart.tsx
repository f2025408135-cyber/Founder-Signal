/** CLIP 5: Cold-Start Rule & Wide Confidence (12s, 360 frames)
 * 
 * Shows: A cold-start founder (zero signals) gets a WIDE confidence band instead
 * of a falsely precise low score. Side-by-side comparison.
 * 
 * Animation: Left side shows "False Precision" (thin bar, score=35, red X).
 * Right side shows "Honest Wide Confidence" (wide band 25-85, green check).
 * The band physically widens on the right, emphasizing the difference.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing, spring, useVideoConfig } from "remotion";

const C = { bg: "#0a0908", card: "#14151a", accent: "#5e6ad2", text: "#e6e6e6", muted: "#9ca3af", subtle: "#6b7280", success: "#3ecf8e", warning: "#d4a843", error: "#d44a5c", border: "rgba(255,255,255,0.06)", borderStrong: "rgba(255,255,255,0.12)" };

export const Clip5ColdStart: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Phase 1 (0-60): "Cold-start founder" appears with zero signals
  const zeroSignals = ["✗ No GitHub", "✗ No arXiv", "✗ No Product Hunt", "✗ No Accelerator", "✗ No Prior VC"];
  
  // Phase 2 (60-120): False precision appears (left)
  const falsePrecisionScore = interpolate(frame, [60, 100], [0, 35], { extrapolateLeft: "clamp", easing: Easing.out(Easing.cubic) });
  
  // Phase 3 (120-240): Honest wide confidence appears (right) — band widens
  const bandWidth = interpolate(frame, [140, 220], [0, 60], { extrapolateLeft: "clamp", easing: Easing.out(Easing.cubic) });
  const bandLow = 25;
  const bandHigh = 25 + bandWidth;
  
  // Phase 4 (240-360): Recommendation comparison
  const recReveal = interpolate(frame, [260, 290], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Title */}
        <text x="960" y="100" fill={C.text} fontSize="28" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 20], [0, 1])}>
          The Cold-Start Rule
        </text>
        <text x="960" y="130" fill={C.warning} fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [0, 20], [0, 0.8])}>
          The system's single most important differentiator
        </text>

        {/* Cold-start founder — zero signals */}
        <g opacity={interpolate(frame, [10, 30], [0, 1])}>
          <rect x="660" y="170" width="600" height="70" rx="8" fill={`${C.warning}10`} stroke={C.warning} strokeWidth="1" opacity="0.6" />
          <text x="960" y="200" fill={C.warning} fontSize="16" fontFamily="monospace" textAnchor="middle" fontWeight="bold">❄ COLD-START FOUNDER</text>
          <text x="960" y="224" fill={C.muted} fontSize="11" fontFamily="monospace" textAnchor="middle">Zero funding · Zero GitHub · Zero network — just a deck</text>
        </g>

        {/* Zero signal tags */}
        {zeroSignals.map((sig, i) => (
          <g key={i} opacity={interpolate(frame, [20 + i * 8, 30 + i * 8], [0, 0.7], { extrapolateLeft: "clamp" })}>
            <rect x={430 + i * 220} y="270" width="180" height="28" rx="4" fill={C.card} stroke={C.error} strokeWidth="0.5" opacity="0.4" />
            <text x={520 + i * 220} y="289" fill={C.error} fontSize="11" fontFamily="monospace" textAnchor="middle">{sig}</text>
          </g>
        ))}

        {/* LEFT: False Precision */}
        <g transform="translate(300, 400)" opacity={interpolate(frame, [60, 80], [0, 1], { extrapolateLeft: "clamp" })}>
          <text x="200" y="0" fill={C.error} fontSize="16" fontFamily="mon-serif" textAnchor="middle" fontWeight="bold">FALSE PRECISION</text>
          <text x="200" y="25" fill={C.muted} fontSize="11" fontFamily="monospace" textAnchor="middle">"Score: 35 — pass on this founder"</text>
          
          {/* Thin precise bar */}
          <rect x="0" y="50" width="400" height="8" rx="4" fill={C.card} stroke={C.error} strokeWidth="0.5" />
          <rect x="0" y="50" width={400 * (falsePrecisionScore / 100)} height="8" rx="4" fill={C.error} opacity="0.5" />
          {/* Precision marker */}
          <line x1={400 * (falsePrecisionScore / 100)} y1="42" x2={400 * (falsePrecisionScore / 100)} y2="66" stroke={C.error} strokeWidth="2" />
          <text x={400 * (falsePrecisionScore / 100)} y="85" fill={C.error} fontSize="14" fontFamily="monospace" textAnchor="middle" fontWeight="bold">{Math.round(falsePrecisionScore)}</text>
          
          {/* Red X overlay */}
          {frame > 100 && (
            <g opacity={interpolate(frame, [100, 120], [0, 0.7])}>
              <line x1="20" y1="35" x2="60" y2="75" stroke={C.error} strokeWidth="4" />
              <line x1="60" y1="35" x2="20" y2="75" stroke={C.error} strokeWidth="4" />
              <text x="200" y="120" fill={C.error} fontSize="12" fontFamily="monospace" textAnchor="middle" fontStyle="italic">A false "no" — data is sparse, not bad</text>
            </g>
          )}
          
          {/* Recommendation */}
          {recReveal > 0 && (
            <g opacity={recReveal}>
              <rect x="120" y="160" width="160" height="28" rx="14" fill={`${C.error}15`} stroke={C.error} strokeWidth="0.5" />
              <text x="200" y="178" fill={C.error} fontSize="12" fontFamily="monospace" textAnchor="middle">✗ REJECT</text>
            </g>
          )}
        </g>

        {/* VS divider */}
        <text x="960" y="470" fill={C.subtle} fontSize="24" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [80, 100], [0, 0.4])}>VS</text>

        {/* RIGHT: Honest Wide Confidence */}
        <g transform="translate(1220, 400)" opacity={interpolate(frame, [120, 140], [0, 1], { extrapolateLeft: "clamp" })}>
          <text x="200" y="0" fill={C.success} fontSize="16" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold">HONEST WIDE CONFIDENCE</text>
          <text x="200" y="25" fill={C.muted} fontSize="11" fontFamily="monospace" textAnchor="middle">"Band: 25–85 — worth a closer look"</text>
          
          {/* Wide band bar — physically widens */}
          <rect x="0" y="50" width="400" height="24" rx="6" fill={C.card} stroke={C.success} strokeWidth="0.5" />
          <rect x={400 * (bandLow / 100)} y="50" width={400 * (bandWidth / 100)} height="24" rx="6" fill={`${C.success}30`} stroke={C.success} strokeWidth="1" opacity="0.8" />
          
          {/* Range markers */}
          <line x1={400 * (bandLow / 100)} y1="42" x2={400 * (bandLow / 100)} y2="82" stroke={C.success} strokeWidth="2" />
          <line x1={400 * (bandHigh / 100)} y1="42" x2={400 * (bandHigh / 100)} y2="82" stroke={C.success} strokeWidth="2" />
          <text x={400 * (bandLow / 100)} y="98" fill={C.success} fontSize="14" fontFamily="monospace" textAnchor="middle" fontWeight="bold">{bandLow}</text>
          <text x={400 * (bandHigh / 100)} y="98" fill={C.success} fontSize="14" fontFamily="monospace" textAnchor="middle" fontWeight="bold">{Math.round(bandHigh)}</text>
          
          {/* Width indicator */}
          {bandWidth > 30 && (
            <g opacity={interpolate(frame, [220, 240], [0, 0.6])}>
              <line x1={400 * (bandLow / 100)} y1="115" x2={400 * (bandHigh / 100)} y2="115" stroke={C.success} strokeWidth="1" />
              <text x={400 * ((bandLow + bandHigh) / 2 / 100)} y="132" fill={C.success} fontSize="12" fontFamily="monospace" textAnchor="middle">width: {Math.round(bandWidth)}</text>
            </g>
          )}
          
          {/* Green check */}
          {frame > 200 && (
            <g opacity={interpolate(frame, [200, 220], [0, 0.8])}>
              <circle cx="40" cy="65" r="14" fill={`${C.success}20`} stroke={C.success} strokeWidth="1.5" />
              <path d="M 32 65 L 38 71 L 50 59" stroke={C.success} strokeWidth="2.5" fill="none" />
              <text x="200" y="160" fill={C.success} fontSize="12" fontFamily="monospace" textAnchor="middle">Scored from what IS inferable — the deck itself</text>
            </g>
          )}
          
          {/* Recommendation */}
          {recReveal > 0 && (
            <g opacity={recReveal}>
              <rect x="100" y="190" width="200" height="28" rx="14" fill={`${C.accent}15`} stroke={C.accent} strokeWidth="0.5" />
              <text x="200" y="208" fill={C.accent} fontSize="12" fontFamily="monospace" textAnchor="middle">▸ DEEP_DIVE (never fast_pass)</text>
            </g>
          )}
        </g>

        {/* Bottom rule callout */}
        {frame > 300 && (
          <g opacity={interpolate(frame, [300, 330], [0, 0.7])}>
            <rect x="460" y="720" width="1000" height="50" rx="8" fill={`${C.warning}10`} stroke={C.warning} strokeWidth="0.5" />
            <text x="960" y="752" fill={C.warning} fontSize="14" fontFamily="monospace" textAnchor="middle">
              ❄ Cold-start rule: confidence_band width ≥ 50 · recommendation ≠ fast_pass · ALL 5 flags enumerated
            </text>
          </g>
        )}

        {/* Enforced-at-4-levels indicator */}
        {frame > 320 && (
          <g opacity={interpolate(frame, [320, 340], [0, 0.5])} transform="translate(960, 830)">
            <text x="0" y="0" fill={C.muted} fontSize="11" fontFamily="monospace" textAnchor="middle">ENFORCED AT: Schema · Ingestion Agent R3 · Founder Agent Rule · Aggregator Downgrade</text>
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
