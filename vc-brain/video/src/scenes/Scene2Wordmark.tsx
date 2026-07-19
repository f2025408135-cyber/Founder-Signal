/** Scene 2 (0:04-0:06): Wordmark appears — clean, centered, lavender accent. */
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

export const Scene2Wordmark: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 80 } });
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ transform: `scale(${scale})`, opacity, textAlign: "center" }}>
        <div style={{ fontSize: 72, fontWeight: 700, color: "#e6e6e6", letterSpacing: "-0.04em" }}>
          VC Brain
        </div>
        <div
          style={{
            fontSize: 24,
            fontWeight: 500,
            color: "#5e6ad2",
            marginTop: 12,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
          }}
        >
          Founder Signal
        </div>
        <div
          style={{
            width: 120,
            height: 3,
            background: "linear-gradient(90deg, transparent, #5e6ad2, transparent)",
            margin: "24px auto 0",
            borderRadius: 2,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
