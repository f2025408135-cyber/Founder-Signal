/** CLIP 4: Validator & Evidence Chain (15s, 450 frames)
 * 
 * Shows: Per-claim verification flow — each claim enters the Validator, gets
 * cross-checked against external evidence, and exits with one of 4 status flags.
 * 
 * Animation: Claims flow left-to-right through a Validator node. As each passes
 * through, evidence particles converge on it. Each claim exits with a colored
 * flag tag. The "ONLY agent that writes flags" rule is emphasized.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const C = { bg: "#0a0908", card: "#14151a", accent: "#5e6ad2", text: "#e6e6e6", muted: "#9ca3af", subtle: "#6b7280", success: "#3ecf8e", warning: "#d4a843", error: "#d44a5c", neutral: "#6b7280", border: "rgba(255,255,255,0.06)", borderStrong: "rgba(255,255,255,0.12)" };

const CLAIMS = [
  { text: "850 GitHub stars", source: "deck", status: "verified", evidence: "github.com/founder/repo", color: C.success, delay: 20 },
  { text: "Market is $5B", source: "deck", status: "contradicted", evidence: "crunchbase: $500M", color: C.error, delay: 60 },
  { text: "50 enterprise customers", source: "deck", status: "unverifiable", evidence: "no external data", color: C.warning, delay: 100 },
  { text: "YC W24 cohort", source: "application", status: "verified", evidence: "yc.com/companies", color: C.success, delay: 140 },
  { text: "Cap table disclosed", source: "—", status: "not_disclosed", evidence: "missing entirely", color: C.neutral, delay: 180 },
  { text: "28 commits in 30d", source: "github", status: "verified", evidence: "github.com/commits", color: C.success, delay: 220 },
];

const EVIDENCE_PARTICLES = Array.from({ length: 20 }, (_, i) => ({
  delay: 30 + i * 15,
  angle: (i / 20) * Math.PI * 2,
  dist: 120 + Math.random() * 40,
}));

export const Clip4Validator: React.FC = () => {
  const frame = useCurrentFrame();
  const vx = 960, vy = 540;

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Title */}
        <text x="960" y="100" fill={C.text} fontSize="28" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 20], [0, 1])}>
          Validator Agent — Per-Claim Evidence Chain
        </text>
        <text x="960" y="130" fill={C.muted} fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [0, 20], [0, 0.6])}>
          The ONLY agent that writes claim.flags and claim.confidence
        </text>

        {/* Input label */}
        <text x="300" y="350" fill={C.subtle} fontSize="11" fontFamily="monospace" opacity="0.5">INCOMING CLAIMS →</text>

        {/* Output label */}
        <text x="1500" y="350" fill={C.subtle} fontSize="11" fontFamily="monospace" opacity="0.5">→ TAGGED CLAIMS</text>

        {/* Validator node — central hexagon shape */}
        <g>
          {/* Glow */}
          <circle cx={vx} cy={vy} r="90" fill={C.success} opacity="0.05" />
          <circle cx={vx} cy={vy} r="70" fill={C.success} opacity="0.08" />
          
          {/* Hexagon body */}
          <polygon
            points={`${vx},${vy - 55} ${vx + 48},${vy - 28} ${vx + 48},${vy + 28} ${vx},${vy + 55} ${vx - 48},${vy + 28} ${vx - 48},${vy - 28}`}
            fill={C.card}
            stroke={C.success}
            strokeWidth="2.5"
          />
          
          {/* Inner icon */}
          <text x={vx} y={vy - 5} fill={C.success} fontSize="14" fontFamily="monospace" textAnchor="middle" fontWeight="bold">VALIDATOR</text>
          <text x={vx} y={vy + 15} fill={C.muted} fontSize="10" fontFamily="monospace" textAnchor="middle">GPT-5.6 Sol</text>
          
          {/* Pulsing ring */}
          <circle cx={vx} cy={vy} r={55 + Math.sin(frame * 0.08) * 5} fill="none" stroke={C.success} strokeWidth="1" opacity={0.3 + Math.sin(frame * 0.08) * 0.1} />
        </g>

        {/* Evidence particles converging on validator */}
        {EVIDENCE_PARTICLES.map((p, i) => {
          const progress = interpolate(frame, [p.delay, p.delay + 30], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          });
          if (progress <= 0 || progress >= 1) return null;
          
          const startX = vx + Math.cos(p.angle) * p.dist;
          const startY = vy + Math.sin(p.angle) * p.dist;
          const x = startX + (vx - startX) * progress;
          const y = startY + (vy - startY) * progress;
          const opacity = interpolate(progress, [0, 0.2, 0.8, 1], [0, 0.6, 0.6, 0]);
          
          return <circle key={i} cx={x} cy={y} r="2" fill={C.success} opacity={opacity} />;
        })}

        {/* Claims flowing through */}
        {CLAIMS.map((claim, i) => {
          const progress = interpolate(frame, [claim.delay, claim.delay + 60], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          });
          
          if (progress <= 0) return null;
          
          // Path: left → through validator → right
          const startX = 300;
          const endX = 1500;
          const x = startX + (endX - startX) * progress;
          const y = 380 + i * 55;
          
          // Claim visible, but flag only appears after passing through validator
          const claimOpacity = interpolate(progress, [0, 0.1, 0.9, 1], [0, 1, 1, 0.8]);
          const flagOpacity = progress > 0.45 ? interpolate(progress, [0.45, 0.6], [0, 1], { extrapolateLeft: "clamp" }) : 0;
          const claimColor = progress > 0.45 ? claim.color : C.text;
          
          return (
            <g key={i} opacity={claimOpacity}>
              {/* Source tag */}
              <text x={startX - 10} y={y + 4} fill={C.subtle} fontSize="9" fontFamily="monospace" textAnchor="end" opacity="0.4">[{claim.source}]</text>
              
              {/* Claim text */}
              <text x={x} y={y + 4} fill={claimColor} fontSize="13" fontFamily="monospace" textAnchor="middle">{claim.text}</text>
              
              {/* Status flag (appears after validation) */}
              {flagOpacity > 0 && (
                <g opacity={flagOpacity}>
                  <rect x={x + 100} y={y - 10} width="110" height="20" rx="4" fill={`${claim.color}15`} stroke={claim.color} strokeWidth="0.5" />
                  <text x={x + 155} y={y + 4} fill={claim.color} fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
                    [{claim.status.toUpperCase()}]
                  </text>
                  {/* Evidence source */}
                  <text x={x + 230} y={y + 4} fill={C.muted} fontSize="9" fontFamily="monospace" opacity="0.5">← {claim.evidence}</text>
                </g>
              )}
              
              {/* "Ping" flash when passing through validator */}
              {progress > 0.4 && progress < 0.5 && (
                <circle cx={vx} cy={vy} r={30 + (progress - 0.4) * 200} fill="none" stroke={claim.color} strokeWidth="1" opacity={(0.5 - progress) * 4} />
              )}
            </g>
          );
        })}

        {/* Legend — 4 status types */}
        {frame > 280 && (
          <g opacity={interpolate(frame, [280, 310], [0, 0.7])} transform="translate(960, 920)">
            {[
              { label: "VERIFIED", color: C.success, desc: "external corroboration found" },
              { label: "UNVERIFIABLE", color: C.warning, desc: "no external data" },
              { label: "CONTRADICTED", color: C.error, desc: "evidence disputes claim" },
              { label: "NOT_DISCLOSED", color: C.neutral, desc: "missing entirely" },
            ].map((item, i) => (
              <g key={i} transform={`translate(${-360 + i * 200}, 0)`}>
                <rect x="-70" y="-12" width="140" height="24" rx="4" fill={`${item.color}15`} stroke={item.color} strokeWidth="0.5" />
                <text x="0" y="4" fill={item.color} fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">{item.label}</text>
                <text x="0" y="28" fill={C.subtle} fontSize="8" fontFamily="monospace" textAnchor="middle">{item.desc}</text>
              </g>
            ))}
          </g>
        )}

        {/* Rule callout */}
        {frame > 350 && (
          <g opacity={interpolate(frame, [350, 380], [0, 0.6])}>
            <rect x="660" y="830" width="600" height="36" rx="6" fill={`${C.success}10`} stroke={C.success} strokeWidth="0.5" />
            <text x="960" y="853" fill={C.success} fontSize="12" fontFamily="monospace" textAnchor="middle">
              ✓ R2: Self-reported claims (deck/application_form) can NEVER be "verified"
            </text>
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
