/** Scene 10 (0:44-0:48): Return to wordmark, calm, confident. */
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

export const Scene10Closing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 14, stiffness: 70 } });
  const opacity = interpolate(frame, [0, 15, 100, 120], [0, 1, 1, 0.8]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ transform: `scale(${scale})`, opacity, textAlign: "center" }}>
        <div style={{ fontSize: 64, fontWeight: 700, color: "#e6e6e6", letterSpacing: "-0.04em" }}>
          VC Brain
        </div>
        <div
          style={{
            width: 100,
            height: 2,
            background: "linear-gradient(90deg, transparent, #5e6ad2, transparent)",
            margin: "20px auto",
          }}
        />
        <div style={{ fontSize: 20, fontWeight: 500, color: "#5e6ad2", letterSpacing: "0.05em" }}>
          Capital, moving at the speed of merit.
        </div>
      </div>
    </AbsoluteFill>
  );
};
