/** Scene 6 (0:22-0:28): Validator — claim fragments flow through, tagged with colored flags. */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const CLAIMS = [
  { text: "850 GitHub stars", flag: "verified", color: "#3ecf8e", delay: 0 },
  { text: "$5B market", flag: "contradicted", color: "#d44a5c", delay: 25 },
  { text: "YC W24 cohort", flag: "verified", color: "#3ecf8e", delay: 50 },
  { text: "50 enterprise customers", flag: "unverifiable", color: "#d4a843", delay: 75 },
  { text: "Founded 2024", flag: "verified", color: "#3ecf8e", delay: 100 },
  { text: "$10M ARR", flag: "unverifiable", color: "#d4a843", delay: 125 },
];

const FLAG_LABELS = {
  verified: "VERIFIED",
  contradicted: "CONTRADICTED",
  unverifiable: "UNVERIFIABLE",
};

export const Scene6Validator: React.FC = () => {
  const frame = useCurrentFrame();
  const validatorX = 960;
  const validatorY = 540;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Validator node */}
        <circle cx={validatorX} cy={validatorY} r="50" fill="#14151a" stroke="#3ecf8e" strokeWidth="2" />
        <circle cx={validatorX} cy={validatorY} r="20" fill="#3ecf8e" opacity="0.3" />
        <text x={validatorX} y={validatorY + 80} fill="#3ecf8e" fontSize="14" fontFamily="monospace" textAnchor="middle">VALIDATOR</text>

        {/* Claims flowing through */}
        {CLAIMS.map((claim, i) => {
          const progress = interpolate(
            frame,
            [claim.delay, claim.delay + 40],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) }
          );
          const startX = 400;
          const endX = 1400;
          const x = startX + (endX - startX) * progress;
          const y = validatorY - 60 + i * 25;
          const opacity = interpolate(progress, [0, 0.1, 0.9, 1], [0, 1, 1, 0.5]);

          // Flag appears after passing through validator
          const flagOpacity = progress > 0.45 ? interpolate(progress, [0.45, 0.6], [0, 1], { extrapolateLeft: "clamp" }) : 0;

          return (
            <g key={i}>
              {/* Claim text */}
              <text x={x} y={y} fill="#e6e6e6" fontSize="13" fontFamily="monospace" opacity={opacity}>
                {claim.text}
              </text>
              {/* Flag tag */}
              {flagOpacity > 0 && (
                <g opacity={flagOpacity}>
                  <rect x={x + 180} y={y - 12} width="100" height="18" rx="3" fill={claim.color} opacity="0.15" />
                  <rect x={x + 180} y={y - 12} width="100" height="18" rx="3" fill="none" stroke={claim.color} strokeWidth="1" opacity="0.5" />
                  <text x={x + 230} y={y + 1} fill={claim.color} fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
                    {FLAG_LABELS[claim.flag as keyof typeof FLAG_LABELS]}
                  </text>
                </g>
              )}
            </g>
          );
        })}

        {/* Legend */}
        {frame > 60 && (
          <g opacity={interpolate(frame, [60, 80], [0, 0.6])} transform="translate(960, 900)">
            <rect x="-200" y="-15" width="120" height="18" rx="3" fill="#3ecf8e" opacity="0.15" stroke="#3ecf8e" strokeWidth="0.5" />
            <text x="-140" y="-2" fill="#3ecf8e" fontSize="10" fontFamily="monospace" textAnchor="middle">VERIFIED</text>
            <rect x="-60" y="-15" width="120" height="18" rx="3" fill="#d4a843" opacity="0.15" stroke="#d4a843" strokeWidth="0.5" />
            <text x="0" y="-2" fill="#d4a843" fontSize="10" fontFamily="monospace" textAnchor="middle">UNVERIFIABLE</text>
            <rect x="80" y="-15" width="120" height="18" rx="3" fill="#d44a5c" opacity="0.15" stroke="#d44a5c" strokeWidth="0.5" />
            <text x="140" y="-2" fill="#d44a5c" fontSize="10" fontFamily="monospace" textAnchor="middle">CONTRADICTED</text>
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
