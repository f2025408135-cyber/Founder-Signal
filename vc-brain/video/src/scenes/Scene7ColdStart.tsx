/** Scene 7 (0:28-0:34): Cold-start — thin precise bar vs wide honest confidence band. */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

export const Scene7ColdStart: React.FC = () => {
  const frame = useCurrentFrame();
  const revealCold = interpolate(frame, [30, 60], [0, 1], { extrapolateLeft: "clamp", easing: Easing.out(Easing.cubic) });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Title */}
        <text x="960" y="280" fill="#9ca3af" fontSize="18" fontFamily="monospace" textAnchor="middle">
          COLD-START FOUNDER — ZERO TRACK RECORD
        </text>

        {/* False precision (left) — thin, precise, red X */}
        <g transform="translate(560, 420)">
          <text x="0" y="-20" fill="#d44a5c" fontSize="14" fontFamily="monospace">FALSE PRECISION</text>
          <text x="0" y="0" fill="#6b7280" fontSize="12" fontFamily="monospace">score: 35</text>
          {/* Thin precise bar */}
          <rect x="0" y="10" width="400" height="6" rx="3" fill="#14151a" />
          <rect x="0" y="10" width="140" height="6" rx="3" fill="#d44a5c" opacity="0.6" />
          {/* Marker line at 35 */}
          <line x1="140" y1="5" x2="140" y2="25" stroke="#d44a5c" strokeWidth="2" />
          {/* Red X */}
          {frame > 20 && (
            <g opacity={interpolate(frame, [20, 40], [0, 0.8])}>
              <line x1="-30" y1="-30" x2="-10" y2="-10" stroke="#d44a5c" strokeWidth="3" />
              <line x1="-10" y1="-30" x2="-30" y2="-10" stroke="#d44a5c" strokeWidth="3" />
            </g>
          )}
          <text x="0" y="50" fill="#6b7280" fontSize="11" fontFamily="monospace">A false "no" — data is sparse</text>
        </g>

        {/* VS divider */}
        <text x="960" y="440" fill="#4a3a1a" fontSize="20" fontFamily="monospace" textAnchor="middle">VS</text>

        {/* Honest wide confidence (right) — wide band, green check */}
        <g transform="translate(960, 420)" opacity={revealCold}>
          <text x="0" y="-20" fill="#3ecf8e" fontSize="14" fontFamily="monospace">HONEST WIDE CONFIDENCE</text>
          <text x="0" y="0" fill="#e6e6e6" fontSize="12" fontFamily="monospace">band: 25–85 (width: 60)</text>
          {/* Wide band bar */}
          <rect x="0" y="10" width="400" height="20" rx="6" fill="#14151a" />
          <rect x="100" y="10" width="240" height="20" rx="6" fill="#3ecf8e" opacity="0.2" stroke="#3ecf8e" strokeWidth="1" opacity="0.4" />
          {/* Range markers */}
          <line x1="100" y1="5" x2="100" y2="40" stroke="#3ecf8e" strokeWidth="1.5" />
          <line x1="340" y1="5" x2="340" y2="40" stroke="#3ecf8e" strokeWidth="1.5" />
          <text x="100" y="55" fill="#3ecf8e" fontSize="11" fontFamily="monospace" textAnchor="middle">25</text>
          <text x="340" y="55" fill="#3ecf8e" fontSize="11" fontFamily="monospace" textAnchor="middle">85</text>
          {/* Green check */}
          <g transform="translate(-30, -20)">
            <circle cx="0" cy="0" r="12" fill="#3ecf8e" opacity="0.2" stroke="#3ecf8e" strokeWidth="1.5" />
            <path d="M -5 0 L -2 3 L 5 -4" stroke="#3ecf8e" strokeWidth="2" fill="none" />
          </g>
          <text x="0" y="80" fill="#9ca3af" fontSize="11" fontFamily="monospace">Score from what IS inferable — the deck itself</text>
        </g>

        {/* Bottom note */}
        {frame > 90 && (
          <text x="960" y="700" fill="#5e6ad2" fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [90, 110], [0, 0.8])}>
            WIDE BAND, NOT A FALSE "NO" — THE DIFFERENTIATOR
          </text>
        )}
      </svg>
    </AbsoluteFill>
  );
};
