/** CLIP 6: Tool-less Synthesizer Boundary (13s, 390 frames)
 * 
 * Shows: The Aggregator receives ONLY pre-verified structured facts — no URLs,
 * no raw_inputs, no external_evidence. NO new facts can enter. Visual: a wall
 * that only lets verified data through.
 * 
 * Animation: Unverified facts approach the boundary from outside and bounce off.
 * Only verified facts pass through to the Aggregator, which assembles them into
 * a memo. The "YOU HAVE NO TOOLS" prompt is visually enforced.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const C = { bg: "#0a0908", card: "#14151a", accent: "#5e6ad2", text: "#e6e6e6", muted: "#9ca3af", subtle: "#6b7280", success: "#3ecf8e", warning: "#d4a843", error: "#d44a5c", border: "rgba(255,255,255,0.06)", borderStrong: "rgba(255,255,255,0.12)" };

const INCOMING_FACTS = [
  { text: "850 GitHub stars", verified: true, delay: 20 },
  { text: "Unverified rumor: 'acquisition talks'", verified: false, delay: 50 },
  { text: "Market: $2B by 2028", verified: true, delay: 80 },
  { text: "Web search result: competitor X", verified: false, delay: 110 },
  { text: "YC W24 cohort member", verified: true, delay: 140 },
  { text: "External URL: techcrunch.com/...", verified: false, delay: 170 },
  { text: "28 commits in last 30 days", verified: true, delay: 200 },
  { text: "Invented: 'raised $10M Series A'", verified: false, delay: 230 },
];

export const Clip6Toolless: React.FC = () => {
  const frame = useCurrentFrame();
  const wallX = 760; // The boundary wall position
  const aggX = 1100, aggY = 540;

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Title */}
        <text x="960" y="100" fill={C.text} fontSize="28" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 20], [0, 1])}>
          Tool-less Synthesizer Boundary
        </text>
        <text x="960" y="130" fill={C.muted} fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [0, 20], [0, 0.6])}>
          The Aggregator can NEVER introduce a new unverified fact
        </text>

        {/* The boundary wall — a vertical energy barrier */}
        <g>
          {/* Wall glow */}
          <rect x={wallX - 8} y="200" width="16" height="600" fill={C.warning} opacity="0.08" />
          <rect x={wallX - 3} y="200" width="6" height="600" fill={C.warning} opacity="0.15" />
          
          {/* Wall shimmer */}
          {Array.from({ length: 15 }).map((_, i) => {
            const shimmerY = 200 + i * 43 + (frame * 2 % 43);
            return <line key={i} x1={wallX - 5} y1={shimmerY} x2={wallX + 5} y2={shimmerY} stroke={C.warning} strokeWidth="1" opacity="0.2" />;
          })}
          
          {/* Wall label */}
          <text x={wallX} y="185" fill={C.warning} fontSize="11" fontFamily="monospace" textAnchor="middle" opacity="0.6">BOUNDARY</text>
          <text x={wallX} y="830" fill={C.warning} fontSize="10" fontFamily="monospace" textAnchor="middle" opacity="0.4">no tools · no URLs · no raw_inputs</text>
        </g>

        {/* Left side: "External World" label */}
        <text x="400" y="250" fill={C.subtle} fontSize="12" fontFamily="monospace" textAnchor="middle" opacity="0.4">EXTERNAL WORLD (tools, web, URLs)</text>

        {/* Right side: "Aggregator" label */}
        <text x="1300" y="250" fill={C.warning} fontSize="12" fontFamily="monospace" textAnchor="middle" opacity="0.5">AGGREGATOR (tool-less)</text>

        {/* Incoming facts approaching the wall */}
        {INCOMING_FACTS.map((fact, i) => {
          const progress = interpolate(frame, [fact.delay, fact.delay + 50], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          });
          
          if (progress <= 0) return null;
          
          const startX = 200;
          const factY = 320 + i * 65;
          
          if (fact.verified) {
            // Verified facts pass through the wall
            const passX = startX + (aggX - startX) * progress;
            const passedWall = progress > 0.55;
            const opacity = interpolate(progress, [0, 0.1, 0.95, 1], [0, 1, 1, 0.7]);
            
            return (
              <g key={i} opacity={opacity}>
                {/* Fact text */}
                <rect x={passX - 80} y={factY - 12} width="160" height="24" rx="4" fill={C.card} stroke={C.success} strokeWidth="0.5" opacity="0.6" />
                <text x={passX} y={factY + 4} fill={C.success} fontSize="11" fontFamily="monospace" textAnchor="middle">{fact.text}</text>
                
                {/* Verified checkmark */}
                <circle cx={passX + 85} cy={factY} r="6" fill={C.success} opacity="0.2" />
                <path d={`M ${passX + 82} ${factY} L ${passX + 85} ${factY + 3} L ${passX + 90} ${factY - 3}`} stroke={C.success} strokeWidth="1.5" fill="none" />
                
                {/* "Passes through" flash at wall */}
                {progress > 0.5 && progress < 0.6 && (
                  <circle cx={wallX} cy={factY} r={20 + (progress - 0.5) * 100} fill="none" stroke={C.success} strokeWidth="1" opacity={(0.6 - progress) * 5} />
                )}
              </g>
            );
          } else {
            // Unverified facts bounce off the wall
            const approachProgress = Math.min(progress * 1.5, 0.55);
            const bounceProgress = progress > 0.55 ? interpolate(progress, [0.55, 0.9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
            
            const x = startX + (wallX - startX - 80) * approachProgress - bounceProgress * 100;
            const opacity = interpolate(progress, [0, 0.1, 0.85, 1], [0, 1, 1, 0]);
            
            return (
              <g key={i} opacity={opacity}>
                {/* Fact text */}
                <rect x={x - 80} y={factY - 12} width="160" height="24" rx="4" fill={C.card} stroke={C.error} strokeWidth="0.5" opacity="0.4" />
                <text x={x} y={factY + 4} fill={C.error} fontSize="11" fontFamily="monospace" textAnchor="middle">{fact.text}</text>
                
                {/* Bounce effect at wall */}
                {progress > 0.5 && progress < 0.65 && (
                  <g>
                    <circle cx={wallX} cy={factY} r={15 + (progress - 0.5) * 80} fill="none" stroke={C.error} strokeWidth="1.5" opacity={(0.65 - progress) * 4} />
                    <text x={wallX} y={factY - 20} fill={C.error} fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold" opacity={(0.65 - progress) * 4}>BLOCKED</text>
                  </g>
                )}
                
                {/* ✗ symbol */}
                <text x={x + 85} y={factY + 4} fill={C.error} fontSize="14" textAnchor="middle">✗</text>
              </g>
            );
          }
        })}

        {/* Aggregator node */}
        <g>
          {/* Glow */}
          <circle cx={aggX} cy={aggY} r="70" fill={C.warning} opacity="0.05" />
          
          {/* Body */}
          <rect x={aggX - 70} y={aggY - 40} width="140" height="80" rx="10" fill={C.card} stroke={C.warning} strokeWidth="2.5" />
          <text x={aggX} y={aggY - 10} fill={C.warning} fontSize="14" fontFamily="monospace" textAnchor="middle" fontWeight="bold">AGGREGATOR</text>
          <text x={aggX} y={aggY + 10} fill={C.muted} fontSize="10" fontFamily="monospace" textAnchor="middle">GPT-5.6 Sol</text>
          <text x={aggX} y={aggY + 28} fill={C.error} fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">NO TOOLS</text>
          
          {/* Lock icon */}
          <g transform={`translate(${aggX + 50}, ${aggY - 25})`}>
            <rect x="-6" y="-4" width="12" height="10" rx="2" fill={C.error} opacity="0.3" />
            <path d="M -4 -4 L -4 -8 A 4 4 0 0 1 4 -8 L 4 -4" fill="none" stroke={C.error} strokeWidth="1.5" />
          </g>
        </g>

        {/* Memo output */}
        {frame > 280 && (
          <g opacity={interpolate(frame, [280, 310], [0, 1])}>
            <rect x="1280" y="420" width="200" height="240" rx="8" fill={C.card} stroke={C.warning} strokeWidth="1" opacity="0.7" />
            <rect x="1280" y="420" width="200" height="30" rx="8" fill={C.warning} opacity="0.1" />
            <text x="1380" y="440" fill={C.warning} fontSize="11" fontFamily="monospace" textAnchor="middle">INVESTMENT MEMO</text>
            {/* Memo content lines */}
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <rect key={i} x="1300" y={465 + i * 22} width={i % 3 === 0 ? 160 : 120} height="4" rx="2" fill={C.text} opacity="0.15" />
            ))}
            {/* Citation tags */}
            {[
              { y: 490, color: C.success },
              { y: 540, color: C.success },
              { y: 580, color: C.warning },
              { y: 620, color: C.success },
            ].map((tag, i) => (
              <circle key={i} cx="1470" cy={tag.y} r="4" fill={tag.color} opacity="0.7" />
            ))}
            <text x="1380" y="690" fill={C.muted} fontSize="10" fontFamily="monospace" textAnchor="middle">every fact cited [^claim_id]</text>
          </g>
        )}

        {/* Arrow from aggregator to memo */}
        {frame > 290 && (
          <line x1="1180" y1={aggY} x2="1270" y2={aggY} stroke={C.warning} strokeWidth="1.5" strokeDasharray="4 3" opacity={interpolate(frame, [290, 310], [0, 0.4])} />
        )}

        {/* 3-level enforcement callout */}
        {frame > 330 && (
          <g opacity={interpolate(frame, [330, 360], [0, 0.6])}>
            <rect x="400" y="880" width="1120" height="70" rx="8" fill={`${C.warning}08`} stroke={C.warning} strokeWidth="0.5" />
            <text x="960" y="910" fill={C.warning} fontSize="13" fontFamily="monospace" textAnchor="middle" fontWeight="bold">ENFORCED AT 3 LEVELS:</text>
            <text x="960" y="932" fill={C.muted} fontSize="11" fontFamily="monospace" textAnchor="middle">
              ① Code: no bind_tools() · no tools= argument ② Prompt: "YOU HAVE NO TOOLS" ③ Input: AggregatorAgentInput excludes raw_inputs/URLs
            </text>
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
