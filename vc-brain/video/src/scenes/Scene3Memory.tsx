/** Scene 3 (0:06-0:12): Scattered dots flow inward into one central glowing node — convergence. */
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

const SIGNALS = Array.from({ length: 30 }, (_, i) => {
  const angle = (i / 30) * Math.PI * 2;
  const dist = 400 + Math.random() * 200;
  return {
    startX: Math.cos(angle) * dist,
    startY: Math.sin(angle) * dist,
    delay: Math.random() * 60,
    speed: 0.8 + Math.random() * 0.4,
    size: 2 + Math.random() * 3,
    color: ["#5e6ad2", "#3d5a80", "#e0e6ed"][i % 3],
  };
});

export const Scene3Memory: React.FC = () => {
  const frame = useCurrentFrame();
  const coreScale = interpolate(frame, [60, 120], [0.5, 1.2], { extrapolateLeft: "clamp" });
  const coreOpacity = interpolate(frame, [30, 90], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <defs>
          <radialGradient id="coreGlow">
            <stop offset="0%" stopColor="#5e6ad2" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#5e6ad2" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#5e6ad2" stopOpacity="0" />
          </radialGradient>
        </defs>
        {/* Central glowing node */}
        <circle cx="960" cy="540" r={80 * coreScale} fill="url(#coreGlow)" opacity={coreOpacity} />
        <circle cx="960" cy="540" r={30 * coreScale} fill="#5e6ad2" opacity={coreOpacity * 0.6} />
        <circle cx="960" cy="540" r={12 * coreScale} fill="#e0e6ed" opacity={coreOpacity} />
        
        {/* Label */}
        {frame > 90 && (
          <text x="960" y="660" fill="#9ca3af" fontSize="18" fontFamily="monospace" textAnchor="middle" opacity={interpolate(frame, [90, 120], [0, 1])}>
            MEMORY LAYER
          </text>
        )}

        {/* Signals flowing inward */}
        {SIGNALS.map((sig, i) => {
          const progress = interpolate(
            frame,
            [sig.delay, sig.delay + 60],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) }
          );
          const x = 960 + sig.startX * (1 - progress);
          const y = 540 + sig.startY * (1 - progress);
          const opacity = interpolate(progress, [0, 0.2, 0.8, 1], [0, 0.8, 0.8, 0]);
          return (
            <g key={i}>
              {/* Trail */}
              <line
                x1={960 + sig.startX * (1 - Math.max(0, progress - 0.1))}
                y1={540 + sig.startY * (1 - Math.max(0, progress - 0.1))}
                x2={x}
                y2={y}
                stroke={sig.color}
                strokeWidth="1"
                opacity={opacity * 0.3}
              />
              {/* Dot */}
              <circle cx={x} cy={y} r={sig.size} fill={sig.color} opacity={opacity} />
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
