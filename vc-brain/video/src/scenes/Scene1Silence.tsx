/** Scene 1 (0:00-0:04): Scattered, disconnected faint dots drifting apart — invisible founders. */
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

const DOTS = Array.from({ length: 40 }, (_, i) => ({
  x: (Math.random() - 0.5) * 1600,
  y: (Math.random() - 0.5) * 900,
  vx: (Math.random() - 0.5) * 0.8,
  vy: (Math.random() - 0.5) * 0.8,
  size: 2 + Math.random() * 3,
  delay: Math.random() * 30,
}));

export const Scene1Silence: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30, 90, 120], [0, 0.3, 0.3, 0]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {DOTS.map((dot, i) => {
          const x = 960 + dot.x + dot.vx * frame;
          const y = 540 + dot.y + dot.vy * frame;
          const dotOpacity = interpolate(frame, [dot.delay, dot.delay + 20], [0, opacity], { extrapolateLeft: "clamp" });
          return (
            <circle key={i} cx={x} cy={y} r={dot.size} fill="#6b7280" opacity={dotOpacity} />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
