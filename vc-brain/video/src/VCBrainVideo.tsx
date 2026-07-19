/**
 * VC Brain — 60-Second Architecture Demo Video
 * 
 * 1800 frames at 30fps = exactly 60 seconds.
 * 11 scenes matching the timestamped script precisely.
 * 
 * Color palette (reused from product):
 * - Background: #0a0908 (graphite black)
 * - Accent: #5e6ad2 (lavender-blue)
 * - Verified: #3ecf8e (emerald)
 * - Unverifiable: #d4a843 (amber)
 * - Contradicted: #d44a5c (crimson)
 * - Text: #e6e6e6 (off-white)
 * - Muted: #6b7280
 */
import { AbsoluteFill, Sequence, useCurrentFrame, interpolate, Easing } from "remotion";
import { Scene1Silence } from "./scenes/Scene1Silence";
import { Scene2Wordmark } from "./scenes/Scene2Wordmark";
import { Scene3Memory } from "./scenes/Scene3Memory";
import { Scene4Agents } from "./scenes/Scene4Agents";
import { Scene5Axes } from "./scenes/Scene5Axes";
import { Scene6Validator } from "./scenes/Scene6Validator";
import { Scene7ColdStart } from "./scenes/Scene7ColdStart";
import { Scene8Aggregator } from "./scenes/Scene8Aggregator";
import { Scene9Memo } from "./scenes/Scene9Memo";
import { Scene10Closing } from "./scenes/Scene10Closing";
import { Scene11EndCard } from "./scenes/Scene11EndCard";
import { Caption } from "./Caption";

// Script lines with exact timestamps (frame = seconds * 30)
const SCRIPT = [
  { start: 0, end: 120, text: "Founders are dying in silence — not for lack of merit, but because nobody's looking in time." },
  { start: 120, end: 180, text: "This is the VC Brain." },
  { start: 180, end: 360, text: "Every signal — a GitHub commit, a launch, an application — flows into one memory layer that never forgets." },
  { start: 360, end: 450, text: "From there, six specialized agents take over." },
  { start: 450, end: 660, text: "Three score independently — the founder, the market, the idea itself — never averaged, because the disagreement IS the signal." },
  { start: 660, end: 840, text: "A Validator agent cross-checks every single claim against real evidence, and flags what it can't verify." },
  { start: 840, end: 1020, text: "Even with zero track record, the system scores fairly — a wide, honest confidence instead of a false \"no.\"" },
  { start: 1020, end: 1170, text: "An Aggregator brings it together — never inventing a fact, only citing what's proven." },
  { start: 1170, end: 1320, text: "The result: a fully evidenced investment memo, ready in minutes, not weeks." },
  { start: 1320, end: 1440, text: "This is capital, moving at the speed of merit." },
  { start: 1440, end: 1800, text: "" }, // End card — no caption
];

export const VCBrainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0908", fontFamily: "'Geist Sans', 'SF Pro Display', system-ui, sans-serif" }}>
      {/* Scene 1: 0:00-0:04 (frames 0-120) — Founders dying in silence */}
      <Sequence from={0} durationInFrames={120}>
        <Scene1Silence />
      </Sequence>

      {/* Scene 2: 0:04-0:06 (frames 120-180) — This is the VC Brain */}
      <Sequence from={120} durationInFrames={60}>
        <Scene2Wordmark />
      </Sequence>

      {/* Scene 3: 0:06-0:12 (frames 180-360) — Memory layer */}
      <Sequence from={180} durationInFrames={180}>
        <Scene3Memory />
      </Sequence>

      {/* Scene 4: 0:12-0:15 (frames 360-450) — Six agents */}
      <Sequence from={360} durationInFrames={90}>
        <Scene4Agents />
      </Sequence>

      {/* Scene 5: 0:15-0:22 (frames 450-660) — Three axes, never averaged */}
      <Sequence from={450} durationInFrames={210}>
        <Scene5Axes />
      </Sequence>

      {/* Scene 6: 0:22-0:28 (frames 660-840) — Validator */}
      <Sequence from={660} durationInFrames={180}>
        <Scene6Validator />
      </Sequence>

      {/* Scene 7: 0:28-0:34 (frames 840-1020) — Cold-start */}
      <Sequence from={840} durationInFrames={180}>
        <Scene7ColdStart />
      </Sequence>

      {/* Scene 8: 0:34-0:39 (frames 1020-1170) — Aggregator */}
      <Sequence from={1020} durationInFrames={150}>
        <Scene8Aggregator />
      </Sequence>

      {/* Scene 9: 0:39-0:44 (frames 1170-1320) — Final memo */}
      <Sequence from={1170} durationInFrames={150}>
        <Scene9Memo />
      </Sequence>

      {/* Scene 10: 0:44-0:48 (frames 1320-1440) — Closing line */}
      <Sequence from={1320} durationInFrames={120}>
        <Scene10Closing />
      </Sequence>

      {/* Scene 11: 0:48-0:60 (frames 1440-1800) — End card */}
      <Sequence from={1440} durationInFrames={360}>
        <Scene11EndCard />
      </Sequence>

      {/* Captions — burn in on every scene except end card */}
      {SCRIPT.map((line, i) => {
        if (!line.text) return null;
        return (
          <Sequence key={i} from={line.start} durationInFrames={line.end - line.start}>
            <Caption text={line.text} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
