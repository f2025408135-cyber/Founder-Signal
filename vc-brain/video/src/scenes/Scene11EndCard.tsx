/** Scene 11 (0:48-0:60): End card — wordmark held steady, breathing room, no motion. */
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

export const Scene11EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity, textAlign: "center" }}>
        <div style={{ fontSize: 56, fontWeight: 700, color: "#e6e6e6", letterSpacing: "-0.04em" }}>
          VC Brain
        </div>
        <div style={{ fontSize: 16, fontWeight: 500, color: "#5e6ad2", letterSpacing: "0.1em", marginTop: 8, textTransform: "uppercase" }}>
          Founder Signal
        </div>
        <div
          style={{
            width: 80,
            height: 2,
            background: "linear-gradient(90deg, transparent, #5e6ad2, transparent)",
            margin: "24px auto",
          }}
        />
        <div style={{ fontSize: 12, color: "#6b7280", fontFamily: "monospace", marginTop: 16 }}>
          Sourcing · Screening · Diligence · Decision
        </div>
      </div>
    </AbsoluteFill>
  );
};
