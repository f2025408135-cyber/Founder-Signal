/** CLIP 1: Memory Layer & Ingestion Pipeline (15s, 450 frames)
 * 
 * Shows: Raw signals (GitHub commits, arXiv papers, PH launches, applications) 
 * flowing from external sources → Ingestion Agent → atomic Claims → Memory Layer (Postgres).
 * 
 * Animation: Multiple signal particles streaming in from 4 directions, converging through
 * the Ingestion Agent (which splits them into atomic claims), then settling into the 
 * persistent memory layer with a "never forgets" pulse.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing, spring, useVideoConfig } from "remotion";

const C = { bg: "#0a0908", card: "#14151a", accent: "#5e6ad2", text: "#e6e6e6", muted: "#9ca3af", subtle: "#6b7280", success: "#3ecf8e", warning: "#d4a843", border: "rgba(255,255,255,0.06)", borderStrong: "rgba(255,255,255,0.12)" };

const SOURCES = [
  { label: "GITHUB", angle: -135, color: "#3ecf8e", icon: "⌥" },
  { label: "ARXIV", angle: -45, color: "#5e6ad2", icon: "📄" },
  { label: "PRODUCTHUNT", angle: 45, color: "#d4a843", icon: "▲" },
  { label: "APPLICATIONS", angle: 135, color: "#5e6ad2", icon: "📋" },
];

const SIGNAL_PARTICLES = Array.from({ length: 40 }, (_, i) => ({
  sourceIdx: i % 4,
  delay: i * 8,
  speed: 0.8 + Math.random() * 0.3,
  offset: (Math.random() - 0.5) * 60,
}));

const CLAIMS = [
  "850 GitHub stars", "28 commits in 30d", "12 contributors",
  "arxiv: Efficient Inference", "Published Jan 2026",
  "PH launch: 320 upvotes", "YC W24 cohort",
  "Founder: ex-DeepMind", "Market: $2B by 2028",
  "Product: LLM eval harness", "Berlin, DE", "Pre-seed stage",
];

export const Clip1MemoryIngestion: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cx = 960, cy = 540;

  // Phase 1 (0-120): Sources appear
  const sourceOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  
  // Phase 2 (30-250): Signals stream toward ingestion agent
  const ingestionAgentX = 960, ingestionAgentY = 540;
  const agentPulse = 1 + Math.sin(frame * 0.1) * 0.05;

  // Phase 3 (200-350): Atomic claims burst out from agent
  const claimsPhase = interpolate(frame, [200, 250], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Phase 4 (300-450): Claims settle into memory layer
  const memoryReveal = interpolate(frame, [300, 350], [0, 1], { extrapolateLeft: "clamp" });
  const memoryPulse = interpolate(frame, [350, 400, 440], [0, 1, 0.8]);

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <defs>
          <radialGradient id="agentGlow">
            <stop offset="0%" stopColor={C.accent} stopOpacity="0.6" />
            <stop offset="50%" stopColor={C.accent} stopOpacity="0.15" />
            <stop offset="100%" stopColor={C.accent} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="memoryGlow">
            <stop offset="0%" stopColor={C.accent} stopOpacity="0.4" />
            <stop offset="100%" stopColor={C.accent} stopOpacity="0" />
          </radialGradient>
          <linearGradient id="trailGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={C.accent} stopOpacity="0" />
            <stop offset="100%" stopColor={C.accent} stopOpacity="0.4" />
          </linearGradient>
        </defs>

        {/* Title */}
        <text x={cx} y="120" fill={C.text} fontSize="32" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 20], [0, 1])}>
          Memory Layer & Ingestion Pipeline
        </text>
        <text x={cx} y="150" fill={C.muted} fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [0, 20], [0, 0.6])}>
          Every signal → atomic claims → persistent memory that never forgets
        </text>

        {/* Source nodes at corners */}
        {SOURCES.map((src, i) => {
          const rad = (src.angle * Math.PI) / 180;
          const dist = 400;
          const x = cx + Math.cos(rad) * dist;
          const y = cy + Math.sin(rad) * dist;
          const srcReveal = interpolate(frame, [10 + i * 8, 25 + i * 8], [0, 1], { extrapolateLeft: "clamp" });
          
          return (
            <g key={i} opacity={sourceOpacity * srcReveal}>
              {/* Source node */}
              <circle cx={x} cy={y} r="35" fill={C.card} stroke={src.color} strokeWidth="2" />
              <circle cx={x} cy={y} r="12" fill={src.color} opacity="0.4" />
              <text x={x} y={y + 55} fill={C.muted} fontSize="12" fontFamily="monospace" textAnchor="middle">{src.label}</text>
              
              {/* Connection line to center */}
              <line x1={x} y1={y} x2={ingestionAgentX} y2={ingestionAgentY} stroke={src.color} strokeWidth="1" opacity="0.15" strokeDasharray="4 6" />
            </g>
          );
        })}

        {/* Signal particles streaming inward */}
        {SIGNAL_PARTICLES.map((p, i) => {
          const src = SOURCES[p.sourceIdx];
          const rad = (src.angle * Math.PI) / 180;
          const dist = 400;
          const startX = cx + Math.cos(rad) * dist + p.offset;
          const startY = cy + Math.sin(rad) * dist + p.offset;
          
          const progress = interpolate(frame, [p.delay, p.delay + 80], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          });
          
          if (progress <= 0 || progress >= 1) return null;
          
          const x = startX + (ingestionAgentX - startX) * progress;
          const y = startY + (ingestionAgentY - startY) * progress;
          const opacity = interpolate(progress, [0, 0.1, 0.85, 1], [0, 1, 1, 0]);
          
          // Trail
          const trailX = startX + (ingestionAgentX - startX) * Math.max(0, progress - 0.08);
          const trailY = startY + (ingestionAgentY - startY) * Math.max(0, progress - 0.08);
          
          return (
            <g key={i} opacity={opacity}>
              <line x1={trailX} y1={trailY} x2={x} y2={y} stroke={src.color} strokeWidth="1.5" opacity="0.3" />
              <circle cx={x} cy={y} r="3" fill={src.color} />
            </g>
          );
        })}

        {/* Ingestion Agent — central processing node */}
        <g>
          {/* Glow */}
          <circle cx={ingestionAgentX} cy={ingestionAgentY} r="80" fill="url(#agentGlow)" opacity={agentPulse} />
          {/* Outer ring */}
          <circle cx={ingestionAgentX} cy={ingestionAgentY} r="50" fill="none" stroke={C.accent} strokeWidth="1.5" opacity="0.4" />
          {/* Core */}
          <rect x={ingestionAgentX - 40} y={ingestionAgentY - 25} width="80" height="50" rx="8" fill={C.card} stroke={C.accent} strokeWidth="2" />
          <text x={ingestionAgentX} y={ingestionAgentY - 5} fill={C.accent} fontSize="12" fontFamily="monospace" textAnchor="middle" fontWeight="bold">INGESTION</text>
          <text x={ingestionAgentX} y={ingestionAgentY + 12} fill={C.muted} fontSize="10" fontFamily="monospace" textAnchor="middle">AGENT</text>
          
          {/* Processing sparks */}
          {frame > 100 && frame < 250 && (
            <g>
              {[0, 1, 2, 3, 4, 5].map((i) => {
                const sparkAngle = (i / 6) * Math.PI * 2 + frame * 0.05;
                const sparkR = 55 + Math.sin(frame * 0.1 + i) * 8;
                const sx = ingestionAgentX + Math.cos(sparkAngle) * sparkR;
                const sy = ingestionAgentY + Math.sin(sparkAngle) * sparkR;
                return <circle key={i} cx={sx} cy={sy} r="2" fill={C.accent} opacity="0.6" />;
              })}
            </g>
          )}
        </g>

        {/* Atomic Claims bursting outward (Phase 3) */}
        {claimsPhase > 0 && CLAIMS.map((claimText, i) => {
          const angle = (i / CLAIMS.length) * Math.PI * 2;
          const burstDist = 180 * claimsPhase;
          const x = ingestionAgentX + Math.cos(angle) * burstDist;
          const y = ingestionAgentY + Math.sin(angle) * burstDist;
          const claimOpacity = interpolate(claimsPhase, [0, 0.3, 0.8, 1], [0, 1, 1, 0.7]);
          
          return (
            <g key={i} opacity={claimOpacity}>
              <rect x={x - 60} y={y - 10} width="120" height="20" rx="4" fill={C.card} stroke={C.borderStrong} strokeWidth="0.5" />
              <text x={x} y={y + 4} fill={C.text} fontSize="9" fontFamily="monospace" textAnchor="middle">{claimText}</text>
              {/* Claim → Memory connection */}
              <line x1={x} y1={y + 10} x2={ingestionAgentX} y2={ingestionAgentY + 60} stroke={C.accent} strokeWidth="0.5" opacity="0.2" />
            </g>
          );
        })}

        {/* Memory Layer — persistent store (Phase 4) */}
        {memoryReveal > 0 && (
          <g opacity={memoryReveal}>
            {/* Database cylinder */}
            <ellipse cx={cx} cy={750} rx="160" ry="30" fill={C.card} stroke={C.accent} strokeWidth="2" opacity={memoryPulse} />
            <rect x={cx - 160} y={750} width="320" height="80" fill={C.card} stroke={C.accent} strokeWidth="2" opacity={memoryPulse} />
            <ellipse cx={cx} cy={830} rx="160" ry="30" fill={C.card} stroke={C.accent} strokeWidth="2" opacity={memoryPulse} />
            {/* Inner lines (data rows) */}
            {[0, 1, 2, 3].map((i) => (
              <ellipse key={i} cx={cx} cy={770 + i * 18} rx="150" ry="6" fill="none" stroke={C.accent} strokeWidth="0.5" opacity="0.2" />
            ))}
            {/* Label */}
            <text x={cx} y="880" fill={C.accent} fontSize="16" fontFamily="monospace" textAnchor="middle" fontWeight="bold" opacity={memoryPulse}>
              MEMORY LAYER — POSTGRES + PGVECTOR
            </text>
            <text x={cx} y="905" fill={C.muted} fontSize="12" fontFamily="monospace" textAnchor="middle" opacity={memoryPulse * 0.7}>
              Never discards data · Never resets founder history · Append-only score_history
            </text>
            
            {/* "Never forgets" pulse effect */}
            {frame > 380 && (
              <circle cx={cx} cy={790} r={interpolate(frame, [380, 440], [50, 200])} fill="none" stroke={C.accent} strokeWidth="1" opacity={interpolate(frame, [380, 440], [0.5, 0])} />
            )}
          </g>
        )}

        {/* Flow arrows from agent to memory */}
        {memoryReveal > 0.3 && (
          <g opacity={memoryReveal * 0.4}>
            <line x1={cx} y1={ingestionAgentY + 50} x2={cx} y2={720} stroke={C.accent} strokeWidth="1.5" strokeDasharray="6 4" />
            <polygon points={`${cx - 6},715 ${cx + 6},715 ${cx},725`} fill={C.accent} />
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};
