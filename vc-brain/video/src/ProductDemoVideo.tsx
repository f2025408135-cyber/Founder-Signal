/**
 * VC Brain — 60-Second Product Demo Video
 * 
 * Shows WHAT the product does for an investor and WHY it matters.
 * Emotional core: the cold-start founder story.
 * Uses SVG-recreated product UI mockups (not screen recordings) for frame-accuracy.
 * 
 * 1800 frames at 30fps = exactly 60 seconds.
 */
import { AbsoluteFill, Sequence, useCurrentFrame, interpolate, Easing, spring, useVideoConfig } from "remotion";

// Script lines with exact timestamps
const SCRIPT = [
  { start: 0, end: 120, text: "Right now, the best founders are invisible — buried in decks nobody reads, and code nobody's watching." },
  { start: 120, end: 180, text: "Meet the VC Brain." },
  { start: 180, end: 330, text: "Just tell it what you're looking for — in plain English. No forms. No dropdowns." },
  { start: 330, end: 420, text: "Fin asks the right follow-up questions, then gets straight to work." },
  { start: 420, end: 570, text: "Live, right now — it's already scanning GitHub, launches, and applications for a match." },
  { start: 570, end: 780, text: "Here's a founder with zero funding, zero network — just a great idea. The old system would have missed her completely." },
  { start: 780, end: 960, text: "The VC Brain doesn't. It scores her fairly, honestly, and tells you exactly how confident it is." },
  { start: 960, end: 1110, text: "Every claim, every number — traced straight back to its source. Nothing invented. Nothing hidden." },
  { start: 1110, end: 1290, text: "The bull case. The bear case. Side by side — before you even have to ask." },
  { start: 1290, end: 1440, text: "What used to take weeks now takes minutes." },
  { start: 1440, end: 1590, text: "This isn't just faster investing." },
  { start: 1590, end: 1800, text: "It's investing in who you'd never have found — and now, can't miss." },
];

const COLORS = {
  bg: "#0a0908",
  card: "#14151a",
  accent: "#5e6ad2",
  text: "#e6e6e6",
  muted: "#9ca3af",
  subtle: "#6b7280",
  border: "rgba(255,255,255,0.06)",
  borderStrong: "rgba(255,255,255,0.12)",
  success: "#3ecf8e",
  warning: "#d4a843",
  error: "#d44a5c",
};

export const ProductDemoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg, fontFamily: "'Geist Sans', system-ui, sans-serif" }}>
      {/* Scene 1: 0:00-0:04 — Invisible founders */}
      <Sequence from={0} durationInFrames={120}>
        <Scene1Invisible />
      </Sequence>

      {/* Scene 2: 0:04-0:06 — Meet the VC Brain */}
      <Sequence from={120} durationInFrames={60}>
        <Scene2Meet />
      </Sequence>

      {/* Scene 3: 0:06-0:11 — Fin interface, typing plain English */}
      <Sequence from={180} durationInFrames={150}>
        <Scene3FinType />
      </Sequence>

      {/* Scene 4: 0:11-0:14 — Fin asking follow-up */}
      <Sequence from={330} durationInFrames={90}>
        <Scene4FinFollowup />
      </Sequence>

      {/* Scene 5: 0:14-0:19 — Signal Radar live */}
      <Sequence from={420} durationInFrames={150}>
        <Scene5Radar />
      </Sequence>

      {/* Scene 6: 0:19-0:26 — Cold-start founder card with wide confidence band */}
      <Sequence from={570} durationInFrames={210}>
        <Scene6ColdStartCard />
      </Sequence>

      {/* Scene 7: 0:26-0:32 — Score + honest confidence */}
      <Sequence from={780} durationInFrames={180}>
        <Scene7ScoreConfidence />
      </Sequence>

      {/* Scene 8: 0:32-0:37 — Memo with evidence chips */}
      <Sequence from={960} durationInFrames={150}>
        <Scene8EvidenceChips />
      </Sequence>

      {/* Scene 9: 0:37-0:43 — Verdict bull/bear view */}
      <Sequence from={1110} durationInFrames={180}>
        <Scene9Verdict />
      </Sequence>

      {/* Scene 10: 0:43-0:48 — Dashboard quick cut */}
      <Sequence from={1290} durationInFrames={150}>
        <Scene10Dashboard />
      </Sequence>

      {/* Scene 11: 0:48-0:53 — Wide dashboard */}
      <Sequence from={1440} durationInFrames={150}>
        <Scene11WideDash />
      </Sequence>

      {/* Scene 12: 0:53-0:60 — End card */}
      <Sequence from={1590} durationInFrames={210}>
        <Scene12EndCard />
      </Sequence>

      {/* Captions */}
      {SCRIPT.map((line, i) => (
        <Sequence key={i} from={line.start} durationInFrames={line.end - line.start}>
          <Caption text={line.text} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

// ============= CAPTION =============
const Caption: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 60 }}>
      <div style={{
        opacity,
        maxWidth: "75%",
        textAlign: "center",
        padding: "14px 28px",
        borderRadius: 8,
        background: "rgba(10, 9, 8, 0.8)",
        backdropFilter: "blur(8px)",
        borderBottom: "2px solid rgba(94, 106, 210, 0.3)",
      }}>
        <span style={{ color: COLORS.text, fontSize: 26, fontWeight: 500, letterSpacing: "-0.01em", lineHeight: 1.4 }}>
          {text}
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ============= SCENE 1: Invisible founders =============
const Scene1Invisible: React.FC = () => {
  const frame = useCurrentFrame();
  const dots = Array.from({ length: 35 }, (_, i) => ({
    x: 200 + Math.random() * 1520,
    y: 100 + Math.random() * 880,
    vx: (Math.random() - 0.5) * 0.6,
    vy: (Math.random() - 0.5) * 0.6,
    size: 2 + Math.random() * 3,
    delay: Math.random() * 30,
  }));
  const opacity = interpolate(frame, [0, 30, 90, 120], [0, 0.25, 0.25, 0]);
  return (
    <AbsoluteFill>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {dots.map((d, i) => {
          const x = d.x + d.vx * frame;
          const y = d.y + d.vy * frame;
          const dotOp = interpolate(frame, [d.delay, d.delay + 20], [0, opacity], { extrapolateLeft: "clamp" });
          return <circle key={i} cx={x} cy={y} r={d.size} fill={COLORS.subtle} opacity={dotOp} />;
        })}
        {/* Faint deck pile silhouette */}
        {frame > 40 && (
          <g opacity={interpolate(frame, [40, 70, 100, 120], [0, 0.08, 0.08, 0])}>
            <rect x="760" y="400" width="400" height="280" rx="8" fill={COLORS.subtle} transform="rotate(-3 960 540)" />
            <rect x="780" y="420" width="360" height="240" rx="6" fill={COLORS.bg} transform="rotate(-3 960 540)" />
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};

// ============= SCENE 2: Meet the VC Brain =============
const Scene2Meet: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 80 } });
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ transform: `scale(${scale})`, opacity, textAlign: "center" }}>
        <div style={{ fontSize: 68, fontWeight: 700, color: COLORS.text, letterSpacing: "-0.04em" }}>VC Brain</div>
        <div style={{ fontSize: 22, fontWeight: 500, color: COLORS.accent, marginTop: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>Founder Signal</div>
        <div style={{ width: 100, height: 2, background: `linear-gradient(90deg, transparent, ${COLORS.accent}, transparent)`, margin: "20px auto" }} />
      </div>
    </AbsoluteFill>
  );
};

// ============= SCENE 3: Fin interface — typing plain English =============
const Scene3FinType: React.FC = () => {
  const frame = useCurrentFrame();
  const typedText = "pre-seed AI infra founders in Berlin";
  const charCount = Math.min(Math.floor(frame / 4), typedText.length);
  const showText = typedText.slice(0, charCount);
  const showCursor = frame % 30 < 15;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* Mock hero interface */}
      <div style={{ width: 800, opacity: interpolate(frame, [0, 15], [0, 1]) }}>
        {/* Greeting */}
        <div style={{ textAlign: "center", marginBottom: 30 }}>
          <div style={{ fontSize: 36, fontWeight: 700, color: COLORS.text, letterSpacing: "-0.04em" }}>Ask the VC Brain anything.</div>
          <div style={{ fontSize: 16, color: COLORS.muted, marginTop: 8 }}>Tell Fin what you're looking for — sector, stage, geography...</div>
        </div>
        {/* Input bar */}
        <div style={{ position: "relative", height: 56, borderRadius: 12, background: "rgba(20,21,26,0.6)", border: `1px solid rgba(61,90,128,0.2)`, backdropFilter: "blur(8px)" }}>
          <div style={{ position: "absolute", left: 20, top: "50%", transform: "translateY(-50%)" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={COLORS.subtle} strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
            </svg>
          </div>
          <div style={{ position: "absolute", left: 48, top: "50%", transform: "translateY(-50%)", fontSize: 18, color: COLORS.text, fontFamily: "monospace" }}>
            {showText}{showCursor && charCount < typedText.length ? "|" : ""}
          </div>
          {charCount >= typedText.length && (
            <div style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", padding: "8px 16px", borderRadius: 8, background: COLORS.accent, color: "#fff", fontSize: 14, fontWeight: 500, opacity: interpolate(frame, [120, 135], [0, 1]) }}>
              Talk to Fin →
            </div>
          )}
        </div>
        {/* Suggestion chips */}
        <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16, flexWrap: "wrap" }}>
          {["Cold-start technical founders", "Climate tech, remote-friendly", "No prior VC, YC or Antler"].map((chip, i) => (
            <div key={i} style={{ padding: "6px 12px", borderRadius: 999, fontSize: 12, border: "1px solid rgba(61,90,128,0.3)", background: "rgba(26,36,56,0.4)", color: COLORS.muted }}>
              {chip}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============= SCENE 4: Fin follow-up =============
const Scene4FinFollowup: React.FC = () => {
  const frame = useCurrentFrame();
  const msgOpacity = (delay: number) => interpolate(frame, [delay, delay + 10], [0, 1], { extrapolateLeft: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: 600, opacity: interpolate(frame, [0, 10], [0, 1]) }}>
        {/* Fin avatar + message */}
        <div style={{ display: "flex", gap: 12, marginBottom: 16, opacity: msgOpacity(5) }}>
          <div style={{ width: 32, height: 32, borderRadius: "50%", background: `linear-gradient(135deg, ${COLORS.accent}, #3d5a80)`, flexShrink: 0 }} />
          <div style={{ background: COLORS.card, borderRadius: 12, padding: "12px 16px", border: "1px solid rgba(61,90,128,0.2)" }}>
            <div style={{ fontSize: 14, color: COLORS.text }}>Any geographic focus, or fully remote-friendly?</div>
          </div>
        </div>
        {/* User response */}
        <div style={{ display: "flex", gap: 12, marginBottom: 16, justifyContent: "flex-end", opacity: msgOpacity(30) }}>
          <div style={{ background: COLORS.accent, borderRadius: 12, padding: "12px 16px" }}>
            <div style={{ fontSize: 14, color: "#fff" }}>Berlin and remote EU</div>
          </div>
        </div>
        {/* Fin response */}
        <div style={{ display: "flex", gap: 12, opacity: msgOpacity(55) }}>
          <div style={{ width: 32, height: 32, borderRadius: "50%", background: `linear-gradient(135deg, ${COLORS.accent}, #3d5a80)`, flexShrink: 0 }} />
          <div style={{ background: COLORS.card, borderRadius: 12, padding: "12px 16px", border: "1px solid rgba(61,90,128,0.2)" }}>
            <div style={{ fontSize: 14, color: COLORS.text }}>Got it. Let me scan for matches now.</div>
            <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 4 }}>▶ Starting pipeline...</div>
          </div>
        </div>
        {/* Thesis summary on right */}
        {frame > 70 && (
          <div style={{ position: "absolute", right: 200, top: 200, opacity: interpolate(frame, [70, 85], [0, 1]), background: COLORS.card, borderRadius: 8, padding: 16, border: `1px solid ${COLORS.border}`, width: 200 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: COLORS.text, marginBottom: 8 }}>Thesis Summary</div>
            {[
              ["Sectors", "AI infra"],
              ["Stage", "pre-seed"],
              ["Geography", "DE, remote EU"],
              ["Check", "$100K"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 11, color: COLORS.muted }}>{k}</span>
                <span style={{ fontSize: 11, color: COLORS.success }}>✓ {v}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============= SCENE 5: Signal Radar live =============
const Scene5Radar: React.FC = () => {
  const frame = useCurrentFrame();
  const sweepAngle = (frame * 6) % 360;
  const blips = [
    { angle: -85, dist: 0.7, delay: 10 },
    { angle: -25, dist: 0.5, delay: 30 },
    { angle: 35, dist: 0.8, delay: 50 },
    { angle: 95, dist: 0.6, delay: 70 },
    { angle: 155, dist: 0.75, delay: 90 },
    { angle: 215, dist: 0.65, delay: 110 },
  ];
  const cx = 960, cy = 480, r = 180;
  const polar = (a: number, d: number) => ({ x: cx + Math.cos((a - 90) * Math.PI / 180) * r * d, y: cy + Math.sin((a - 90) * Math.PI / 180) * r * d });

  return (
    <AbsoluteFill>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Radar background */}
        <rect x="780" y="300" width="360" height="360" rx="12" fill="#0a0908" stroke="#4a3a1a33" />
        {/* Corner brackets */}
        {[[780,300],[1140,300],[780,660],[1140,660]].map(([x,y],i)=>(
          <g key={i}>
            <line x1={x} y1={y} x2={x+(i%2===0?20:-20)} y2={y} stroke="#4a3a1a" strokeWidth="2" opacity="0.5" />
            <line x1={x} y1={y} x2={x} y2={y+(i<2?20:-20)} stroke="#4a3a1a" strokeWidth="2" opacity="0.5" />
          </g>
        ))}
        {/* HUD readouts */}
        <text x="800" y="325" fill="#d4af37" fontSize="11" fontFamily="monospace">SIGNALS TODAY: 34</text>
        <text x="1120" y="325" fill="#d4af37" fontSize="11" fontFamily="monospace" textAnchor="end">● LIVE</text>
        {/* Rings */}
        {[0.33, 0.66, 1.0].map((rr, i) => (
          <circle key={i} cx={cx} cy={cy} r={r * rr} fill="none" stroke="#4a3a1a" strokeWidth="1" opacity="0.3" />
        ))}
        {/* Sweep */}
        <g transform={`rotate(${sweepAngle} ${cx} ${cy})`}>
          <path d={`M ${cx} ${cy} L ${cx + r} ${cy} A ${r} ${r} 0 0 0 ${cx + r * Math.cos(-Math.PI/8)} ${cy + r * Math.sin(-Math.PI/8)} Z`} fill="url(#sweepGrad2)" opacity="0.4" />
          <line x1={cx} y1={cy} x2={cx + r} y2={cy} stroke="#fff4d6" strokeWidth="1" opacity="0.4" />
        </g>
        <defs>
          <linearGradient id="sweepGrad2" x1="0%" y1="50%" x2="100%" y2="50%">
            <stop offset="0%" stopColor="#f4d58d" stopOpacity="0" />
            <stop offset="95%" stopColor="#fff4d6" stopOpacity="0.6" />
          </linearGradient>
        </defs>
        {/* Blips */}
        {blips.map((b, i) => {
          const pos = polar(b.angle, b.dist);
          const showFrame = frame > b.delay;
          const pingPhase = ((frame - b.delay) % 60) / 60;
          return showFrame ? (
            <g key={i}>
              <circle cx={pos.x} cy={pos.y} r={4 + pingPhase * 6} fill="none" stroke="#d4af37" strokeWidth="1" opacity={(1 - pingPhase) * 0.5} />
              <circle cx={pos.x} cy={pos.y} r="4" fill="#d4af37" opacity="0.9" />
            </g>
          ) : null;
        })}
        {/* Log lines */}
        {[
          { t: 14, text: "[14:32:07] GITHUB   new commit detected", delay: 15 },
          { t: 14, text: "[14:32:11] FOUNDER  scoring...", delay: 35 },
          { t: 14, text: "[14:32:14] MARKET   scoring...", delay: 55 },
          { t: 14, text: "[14:32:19] VALIDATE 4 claims cross-checked", delay: 75 },
          { t: 14, text: "[14:32:21] SCORED   82 Founder / 61 Market", delay: 95 },
        ].map((log, i) => (
          frame > log.delay ? (
            <text key={i} x="1180" y={380 + i * 22} fill={i === 4 ? "#e8dcc0" : "#d4af37"} fontSize="12" fontFamily="monospace" opacity={interpolate(frame, [log.delay, log.delay + 10], [0, 1])}>
              {log.text}
            </text>
          ) : null
        ))}
        <text x="1180" y="350" fill="#4a3a1a" fontSize="10" fontFamily="monospace">ACTIVITY LOG</text>
      </svg>
    </AbsoluteFill>
  );
};

// ============= SCENE 6: Cold-start founder card — THE MONEY SHOT =============
const Scene6ColdStartCard: React.FC = () => {
  const frame = useCurrentFrame();
  const cardScale = interpolate(frame, [0, 20], [0.9, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const cardOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const bandHighlight = interpolate(frame, [60, 80, 140, 160], [0, 1, 1, 0.8]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ transform: `scale(${cardScale})`, opacity: cardOpacity, width: 520 }}>
        {/* Founder Card mockup */}
        <div style={{ background: COLORS.card, borderRadius: 8, border: `1px solid ${COLORS.warning}66`, padding: 20 }}>
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 18, fontWeight: 700, color: COLORS.text }}>StealthCo</span>
              <span style={{ fontSize: 14 }}>❄</span>
            </div>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <span style={{ fontSize: 12, color: COLORS.muted }}>🇩🇪 DE</span>
              <span style={{ padding: "2px 8px", borderRadius: 999, fontSize: 10, background: COLORS.card, border: `1px solid ${COLORS.borderStrong}`, color: COLORS.muted }}>AI infra</span>
              <span style={{ fontSize: 12, color: COLORS.muted }}>2h ago</span>
            </div>
          </div>
          <div style={{ height: 1, background: COLORS.border, marginBottom: 12 }} />
          {/* Axes */}
          {[
            { label: "Founder", score: 62, trend: "⊘", color: COLORS.accent, extra: "❄ cold-start" },
            { label: "Market", score: 50, trend: "●", color: COLORS.warning, extra: "neutral" },
            { label: "Idea↔Mkt", score: 55, trend: "●", color: COLORS.accent },
            { label: "Thesis Fit", score: 74, trend: "●", color: COLORS.muted },
          ].map((axis, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: 13, color: COLORS.muted, width: 80 }}>{axis.label}</span>
              <span style={{ fontSize: 12, color: COLORS.muted }}>{axis.trend}</span>
              <span style={{ fontSize: 14, fontFamily: "monospace", color: COLORS.text, width: 32, textAlign: "right" }}>{axis.score}</span>
              {/* 10-segment bar */}
              <div style={{ display: "flex", gap: 2 }}>
                {Array.from({ length: 10 }).map((_, j) => (
                  <div key={j} style={{ width: 6, height: 10, borderRadius: 1, background: j < Math.round(axis.score / 10) ? axis.color : COLORS.card, opacity: j < Math.round(axis.score / 10) ? 0.7 : 1 }} />
                ))}
              </div>
              {axis.extra && <span style={{ fontSize: 10, color: COLORS.warning, marginLeft: 4 }}>{axis.extra}</span>}
            </div>
          ))}
          <div style={{ height: 1, background: COLORS.border, margin: "12px 0" }} />
          {/* Confidence band — THE KEY VISUAL */}
          <div style={{ marginBottom: 8, opacity: bandHighlight }}>
            <div style={{ fontSize: 11, color: COLORS.warning, fontWeight: 600, marginBottom: 4 }}>
              Confidence band: 25–85 (width: 60) — wide due to cold-start
            </div>
            {/* Wide band visualization */}
            <div style={{ position: "relative", height: 24, background: COLORS.card, borderRadius: 6, overflow: "hidden" }}>
              <div style={{ position: "absolute", left: "25%", width: "60%", height: "100%", borderRadius: 6, background: `linear-gradient(90deg, ${COLORS.warning}40, ${COLORS.warning}80)`, border: `1px solid ${COLORS.warning}99` }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 2, padding: "0 25%" }}>
              <span style={{ fontSize: 10, color: COLORS.warning }}>25</span>
              <span style={{ fontSize: 10, color: COLORS.warning }}>85</span>
            </div>
          </div>
          {/* Conviction + recommendation */}
          <div style={{ display: "flex", gap: 16, fontSize: 12, marginBottom: 8 }}>
            <span><span style={{ fontFamily: "monospace", fontWeight: 700, color: COLORS.text }}>35</span><span style={{ color: COLORS.muted }}>/100 conviction</span></span>
            <span style={{ color: COLORS.muted }}>evidence 0.00</span>
          </div>
          <div style={{ display: "inline-block", padding: "4px 10px", borderRadius: 999, border: `1px solid ${COLORS.warning}40`, fontSize: 11, color: COLORS.warning }}>▸ deep_dive</div>
        </div>
        {/* "The old system would have missed her" emphasis */}
        {frame > 100 && (
          <div style={{ textAlign: "center", marginTop: 20, opacity: interpolate(frame, [100, 120], [0, 1]) }}>
            <span style={{ fontSize: 16, color: COLORS.error, fontStyle: "italic" }}>The old system would have missed her completely.</span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============= SCENE 7: Score + honest confidence =============
const Scene7ScoreConfidence: React.FC = () => {
  const frame = useCurrentFrame();
  const revealScore = interpolate(frame, [0, 30], [0, 62], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <text x="960" y="320" fill={COLORS.muted} fontSize="16" fontFamily="monospace" textAnchor="middle">SCORED FAIRLY — HONEST CONFIDENCE</text>
        {/* Score number */}
        <text x="960" y="440" fill={COLORS.text} fontSize="72" fontFamily="monospace" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 20], [0, 1])}>
          {Math.round(revealScore)}
        </text>
        <text x="960" y="470" fill={COLORS.muted} fontSize="14" fontFamily="monospace" textAnchor="middle">/ 100 conviction</text>
        {/* Wide confidence band */}
        <g opacity={interpolate(frame, [20, 40], [0, 1])}>
          <rect x="660" y="520" width="600" height="24" rx="6" fill={COLORS.card} />
          <rect x="810" y="520" width="360" height="24" rx="6" fill={`${COLORS.warning}33`} stroke={`${COLORS.warning}99`} strokeWidth="1" />
          <line x1="810" y1="515" x2="810" y2="550" stroke={COLORS.warning} strokeWidth="2" />
          <line x1="1170" y1="515" x2="1170" y2="550" stroke={COLORS.warning} strokeWidth="2" />
          <text x="810" y="565" fill={COLORS.warning} fontSize="12" fontFamily="monospace" textAnchor="middle">25</text>
          <text x="1170" y="565" fill={COLORS.warning} fontSize="12" fontFamily="monospace" textAnchor="middle">85</text>
        </g>
        {/* Honest framing text */}
        {frame > 60 && (
          <text x="960" y="620" fill={COLORS.success} fontSize="14" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [60, 80], [0, 0.8])}>
            ✓ WIDE BAND, NOT A FALSE "NO" — THE DIFFERENTIATOR
          </text>
        )}
        {/* Component scores */}
        {frame > 80 && (
          <g opacity={interpolate(frame, [80, 100], [0, 1])} transform="translate(960, 680)">
            {["Technical: 62", "Market Fit: 50", "Network: 0", "Momentum: 0"].map((s, i) => (
              <text key={i} x={-150 + i * 100} y="0" fill={COLORS.muted} fontSize="11" fontFamily="monospace" textAnchor="middle">{s}</text>
            ))}
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};

// ============= SCENE 8: Memo with evidence chips =============
const Scene8EvidenceChips: React.FC = () => {
  const frame = useCurrentFrame();
  const claims = [
    { text: "Repository has 850 stars on GitHub", status: "verified", color: COLORS.success, delay: 10 },
    { text: "Market is $5B in 2026", status: "contradicted", color: COLORS.error, delay: 30 },
    { text: "50 enterprise customers", status: "unverifiable", color: COLORS.warning, delay: 50 },
    { text: "YC W24 cohort member", status: "verified", color: COLORS.success, delay: 70 },
    { text: "Founded in 2024", status: "verified", color: COLORS.success, delay: 90 },
  ];
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: 700, opacity: interpolate(frame, [0, 15], [0, 1]) }}>
        {/* Memo header */}
        <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, marginBottom: 4 }}>Investment Memo: StealthCo</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 16 }}>DUE DILIGENCE LOG</div>
        {/* Claims with chips */}
        {claims.map((claim, i) => {
          const showFrame = frame > claim.delay;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, opacity: showFrame ? interpolate(frame, [claim.delay, claim.delay + 10], [0, 1]) : 0 }}>
              <span style={{ fontSize: 13, color: COLORS.text }}>{claim.text}</span>
              <span style={{
                display: "inline-flex", alignItems: "center", gap: 4,
                padding: "2px 6px", borderRadius: 4, fontSize: 10, fontFamily: "monospace",
                color: claim.color, background: `${claim.color}15`, border: `1px solid ${claim.color}40`,
              }}>
                [{claim.status}]
              </span>
            </div>
          );
        })}
        {/* Source trace popup */}
        {frame > 110 && (
          <div style={{ marginTop: 20, padding: 12, borderRadius: 8, background: COLORS.card, border: `1px solid ${COLORS.borderStrong}`, opacity: interpolate(frame, [110, 125], [0, 1]) }}>
            <div style={{ fontSize: 10, color: COLORS.muted, textTransform: "uppercase", marginBottom: 4 }}>SOURCE TRACE</div>
            <div style={{ fontSize: 12, color: COLORS.text }}>github.com/founder/repo — retrieved by github.fetch_github_signals</div>
            <div style={{ fontSize: 11, color: COLORS.success, marginTop: 4 }}>✓ Verified via external corroboration</div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============= SCENE 9: Verdict bull/bear view =============
const Scene9Verdict: React.FC = () => {
  const frame = useCurrentFrame();
  const splitPos = interpolate(frame, [20, 50], [50, 45], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <text x="960" y="320" fill={COLORS.text} fontSize="28" fontFamily="sans-serif" textAnchor="middle" fontWeight="bold" opacity={interpolate(frame, [0, 15], [0, 1])}>The Verdict</text>
        {/* Bull side (left) */}
        <g opacity={interpolate(frame, [15, 30], [0, 1])}>
          <rect x="360" y="380" width={540 * (splitPos / 100)} height="280" rx="8" fill={`${COLORS.success}15`} stroke={COLORS.success} strokeWidth="1" />
          <text x="420" y="430" fill={COLORS.success} fontSize="20" fontFamily="monospace" fontWeight="bold">▲ BULL CASE</text>
          {["Strong technical depth (850★ repo)", "YC W24 accelerator backing", "Active commit cadence (28/30d)", "arxiv paper on core method"].map((point, i) => (
            <text key={i} x="420" y={470 + i * 30} fill={COLORS.text} fontSize="13" fontFamily="monospace">+ {point}</text>
          ))}
        </g>
        {/* Bear side (right) */}
        <g opacity={interpolate(frame, [30, 45], [0, 1])}>
          <rect x={360 + 540 * (splitPos / 100) + 10} y="380" width={540 * (1 - splitPos / 100) - 10} height="280" rx="8" fill={`${COLORS.error}15`} stroke={COLORS.error} strokeWidth="1" />
          <text x={960 + 60} y="430" fill={COLORS.error} fontSize="20" fontFamily="monospace" fontWeight="bold">▼ BEAR CASE</text>
          {["Market size contradicted ($5B vs $500M)", "50 enterprise customers unverifiable", "No prior VC backing", "Cold-start: zero network signals"].map((point, i) => (
            <text key={i} x={960 + 60} y={470 + i * 30} fill={COLORS.text} fontSize="13" fontFamily="monospace">− {point}</text>
          ))}
        </g>
        {/* Divider */}
        <line x1={360 + 540 * (splitPos / 100)} y1="370" x2={360 + 540 * (splitPos / 100)} y2="670" stroke={COLORS.muted} strokeWidth="1" strokeDasharray="4 4" opacity="0.3" />
        {/* Recommendation */}
        {frame > 80 && (
          <g opacity={interpolate(frame, [80, 100], [0, 1])}>
            <rect x="810" y="720" width="300" height="40" rx="20" fill={`${COLORS.accent}20`} stroke={COLORS.accent} strokeWidth="1" />
            <text x="960" y="745" fill={COLORS.accent} fontSize="16" fontFamily="monospace" textAnchor="middle" fontWeight="bold">▸ DEEP_DIVE</text>
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};

// ============= SCENE 10: Dashboard quick cut =============
const Scene10Dashboard: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {/* Sidebar */}
        <rect x="0" y="0" width="200" height="1080" fill={COLORS.card} />
        {["Fin", "Inbox", "Network", "Funnel", "Thesis"].map((item, i) => (
          <text key={i} x="30" y={100 + i * 40} fill={i === 1 ? COLORS.text : COLORS.muted} fontSize="14" fontFamily="sans-serif" opacity={interpolate(frame, [0, 10], [0, 0.8])}>{item}</text>
        ))}
        {/* Founder cards (mini) */}
        {[0, 1, 2, 3].map((i) => {
          const cardX = 240 + (i % 2) * 440;
          const cardY = 100 + Math.floor(i / 2) * 280;
          const cardDelay = i * 8;
          return (
            <g key={i} opacity={interpolate(frame, [cardDelay, cardDelay + 10], [0, 1], { extrapolateLeft: "clamp" })}>
              <rect x={cardX} y={cardY} width="400" height="240" rx="8" fill={COLORS.card} stroke={COLORS.border} />
              <text x={cardX + 16} y={cardY + 30} fill={COLORS.text} fontSize="16" fontWeight="bold">Founder {i + 1}</text>
              {/* Mini score bars */}
              {[0, 1, 2, 3].map((j) => (
                <g key={j}>
                  <rect x={cardX + 16} y={cardY + 50 + j * 22} width="200" height="6" rx="3" fill={COLORS.bg} />
                  <rect x={cardX + 16} y={cardY + 50 + j * 22} width={50 + j * 30 + i * 10} height="6" rx="3" fill={COLORS.accent} opacity="0.6" />
                </g>
              ))}
              {/* Recommendation pill */}
              <rect x={cardX + 16} y={cardY + 160} width="80" height="20" rx="10" fill={i === 0 ? `${COLORS.success}20` : `${COLORS.accent}20`} />
              <text x={cardX + 56} y={cardY + 174} fill={i === 0 ? COLORS.success : COLORS.accent} fontSize="10" fontFamily="monospace" textAnchor="middle">{i === 0 ? "fast_pass" : "deep_dive"}</text>
            </g>
          );
        })}
        {/* Time-lapse indicator */}
        <text x="960" y="60" fill={COLORS.accent} fontSize="12" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [0, 10, 130, 150], [0, 0.6, 0.6, 0])}>
          ⚡ NEW → SCORED IN 47 SECONDS
        </text>
      </svg>
    </AbsoluteFill>
  );
};

// ============= SCENE 11: Wide dashboard =============
const Scene11WideDash: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080" opacity={interpolate(frame, [0, 15], [0, 1])}>
        {/* Sidebar */}
        <rect x="0" y="0" width="200" height="1080" fill={COLORS.card} />
        {/* Main content area */}
        <rect x="200" y="0" width="1720" height="1080" fill={COLORS.bg} />
        {/* Header */}
        <text x="240" y="60" fill={COLORS.text} fontSize="24" fontWeight="bold">Inbox</text>
        <text x="240" y="84" fill={COLORS.muted} fontSize="14">Sorted by overall conviction. 12 founders.</text>
        {/* Search bar */}
        <rect x="240" y="100" width="600" height="36" rx="6" fill={COLORS.card} stroke={COLORS.borderStrong} />
        <text x="260" y="123" fill={COLORS.subtle} fontSize="13">Ask me anything about your pipeline...</text>
        {/* Founder cards grid */}
        {[0, 1, 2, 3, 4, 5].map((i) => {
          const col = i % 2;
          const row = Math.floor(i / 2);
          const x = 240 + col * 440;
          const y = 170 + row * 200;
          return (
            <g key={i}>
              <rect x={x} y={y} width="400" height="170" rx="8" fill={COLORS.card} stroke={i === 0 ? `${COLORS.warning}40` : COLORS.border} strokeWidth={i === 0 ? "1" : "1"} />
              <text x={x + 16} y={y + 28} fill={COLORS.text} fontSize="16" fontWeight="bold">Acme {i + 1}</text>
              {i === 0 && <text x={x + 100} y={y + 28} fill={COLORS.warning} fontSize="14">❄</text>}
              {/* Mini bars */}
              {[0, 1, 2, 3].map((j) => (
                <g key={j}>
                  <rect x={x + 16} y={y + 44 + j * 18} width="180" height="5" rx="2" fill={COLORS.bg} />
                  <rect x={x + 16} y={y + 44 + j * 18} width={40 + j * 25 + i * 15} height="5" rx="2" fill={j === 0 ? COLORS.accent : j === 1 ? COLORS.warning : COLORS.accent} opacity="0.5" />
                </g>
              ))}
              {/* Pill */}
              <rect x={x + 16} y={y + 130} width="70" height="18" rx="9" fill={`${COLORS.accent}15`} stroke={`${COLORS.accent}40`} />
              <text x={x + 51} y={y + 142} fill={COLORS.accent} fontSize="9" fontFamily="monospace" textAnchor="middle">deep_dive</text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ============= SCENE 12: End card =============
const Scene12EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateLeft: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity, textAlign: "center" }}>
        <div style={{ fontSize: 52, fontWeight: 700, color: COLORS.text, letterSpacing: "-0.04em" }}>VC Brain</div>
        <div style={{ fontSize: 16, fontWeight: 500, color: COLORS.accent, letterSpacing: "0.1em", marginTop: 8, textTransform: "uppercase" }}>Founder Signal</div>
        <div style={{ width: 80, height: 2, background: `linear-gradient(90deg, transparent, ${COLORS.accent}, transparent)`, margin: "24px auto" }} />
        <div style={{ fontSize: 14, color: COLORS.muted, fontFamily: "monospace", marginTop: 16 }}>
          Sourcing · Screening · Diligence · Decision
        </div>
        <div style={{ fontSize: 12, color: COLORS.subtle, marginTop: 24 }}>
          It's investing in who you'd never have found — and now, can't miss.
        </div>
      </div>
    </AbsoluteFill>
  );
};
