/** Caption — bottom-third burned-in text overlay for narration. */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

export const Caption: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  
  // Fade in over first 10 frames, fade out over last 10 frames
  const opacity = interpolate(
    frame,
    [0, 10],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 80,
      }}
    >
      <div
        style={{
          opacity,
          maxWidth: "70%",
          textAlign: "center",
          padding: "16px 32px",
          borderRadius: 8,
          background: "rgba(10, 9, 8, 0.75)",
          backdropFilter: "blur(8px)",
          borderBottom: "2px solid rgba(94, 106, 210, 0.3)",
        }}
      >
        <span
          style={{
            color: "#e6e6e6",
            fontSize: 28,
            fontFamily: "'Geist Sans', 'SF Pro Display', system-ui, sans-serif",
            fontWeight: 500,
            letterSpacing: "-0.01em",
            lineHeight: 1.4,
          }}
        >
          {text}
        </span>
      </div>
    </AbsoluteFill>
  );
};
