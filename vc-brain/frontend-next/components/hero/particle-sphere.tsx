"use client";
import { useRef, useMemo, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

/**
 * ParticleSphere — a point-cloud sphere with density falloff + slow rotation + breathing pulse.
 *
 * Per spec:
 * - BufferGeometry + PointsMaterial (NOT solid mesh)
 * - Spherical distribution with denser core, sparser edges
 * - Silver-metallic palette: graphite edges → crystalline core.
 * - Slow rotation (few deg/sec) + subtle breathing scale pulse
 * - Particle count: 2000-4000 (capped for 60fps on mid-range laptop)
 * - Bloom post-processing on core particles only
 */

const PARTICLE_COUNT = 3000;

interface ParticleData {
  positions: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
}

function generateParticleData(): ParticleData {
  const positions = new Float32Array(PARTICLE_COUNT * 3);
  const colors = new Float32Array(PARTICLE_COUNT * 3);
  const sizes = new Float32Array(PARTICLE_COUNT);

  // Color palette
  const colorCore = new THREE.Color("#f0f4f8");
  const colorMid = new THREE.Color("#c8cdd4");
  const colorEdge = new THREE.Color("#1a1e24");
  const colorSilver = new THREE.Color("#8e96a0");

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const i3 = i * 3;
    // Spherical distribution with density falloff toward edges
    // Use rejection sampling: generate random point in sphere, accept with probability
    // proportional to (1 - r/R)^2 for denser core
    let x = 0, y = 0, z = 0, r = 0;
    let attempts = 0;
    while (attempts < 10) {
      // Random point in unit sphere
      const u = Math.random();
      const v = Math.random();
      const theta = 2 * Math.PI * u;
      const phi = Math.acos(2 * v - 1);
      const rad = Math.cbrt(Math.random()); // cube root for uniform volume distribution
      x = rad * Math.sin(phi) * Math.cos(theta);
      y = rad * Math.sin(phi) * Math.sin(theta);
      z = rad * Math.cos(phi);
      r = Math.sqrt(x * x + y * y + z * z);

      // Density falloff: accept more particles near center
      const acceptProb = Math.pow(1 - r, 1.5); // strong falloff
      if (Math.random() < acceptProb || attempts === 9) break;
      attempts++;
    }

    // Scale to sphere radius
    const sphereRadius = 2.0;
    positions[i3] = x * sphereRadius;
    positions[i3 + 1] = y * sphereRadius;
    positions[i3 + 2] = z * sphereRadius;

    // Color based on distance from center
    const normalizedR = r; // 0 = center, 1 = edge
    let color: THREE.Color;
    if (normalizedR < 0.3) {
      // Core: crystalline silver
      color = colorCore.clone().lerp(colorSilver, Math.random() * 0.3);
    } else if (normalizedR < 0.6) {
      // Mid: brushed silver
      color = colorMid.clone().lerp(colorSilver, Math.random() * 0.5);
    } else {
      // Edge: graphite steel
      color = colorEdge.clone().lerp(colorMid, Math.random() * 0.4);
    }

    colors[i3] = color.r;
    colors[i3 + 1] = color.g;
    colors[i3 + 2] = color.b;

    // Size: larger near center, smaller at edges
    sizes[i] = (1 - normalizedR * 0.7) * (0.02 + Math.random() * 0.03);
  }

  return { positions, colors, sizes };
}

function ParticlePoints() {
  const pointsRef = useRef<THREE.Points>(null);
  const data = useMemo(() => generateParticleData(), []);

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(data.positions, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(data.colors, 3));
    return geo;
  }, [data]);

  const material = useMemo(() => {
    return new THREE.PointsMaterial({
      size: 0.035,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
  }, []);

  useFrame((state, delta) => {
    if (pointsRef.current) {
      // Very slow rotation — a few degrees per second
      pointsRef.current.rotation.y += delta * 0.15; // ~8.6 deg/sec
      pointsRef.current.rotation.x += delta * 0.03; // ~1.7 deg/sec

      // Subtle breathing scale pulse (very small amplitude)
      const time = state.clock.elapsedTime;
      const pulse = 1 + Math.sin(time * 0.5) * 0.015; // ±1.5% scale
      pointsRef.current.scale.setScalar(pulse);
    }
  });

  return <points ref={pointsRef} geometry={geometry} material={material} />;
}

function GlowCore() {
  const meshRef = useRef<THREE.Mesh>(null);
  useFrame((state) => {
    if (meshRef.current) {
      const time = state.clock.elapsedTime;
      const pulse = 1 + Math.sin(time * 0.5) * 0.05;
      meshRef.current.scale.setScalar(pulse);
    }
  });
  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.3, 32, 32]} />
      <meshBasicMaterial color="#f0f4f8" transparent opacity={0.15} />
    </mesh>
  );
}

export function ParticleSphere() {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 60 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.3} />
          <ParticlePoints />
          <GlowCore />
        </Suspense>
      </Canvas>
    </div>
  );
}

/**
 * Static gradient fallback for environments where WebGL is not available.
 */
export function ParticleSphereFallback() {
  return (
    <div
      className="w-full h-full flex items-center justify-center"
      style={{
        background:
          "radial-gradient(circle at center, #f0f4f8 0%, #c8cdd4 30%, #1a1e24 60%, #06070a 100%)",
      }}
    >
      <div
        className="w-48 h-48 rounded-full"
        style={{
          background: "radial-gradient(circle, #f0f4f8 0%, #c8cdd4 50%, transparent 80%)",
          filter: "blur(20px)",
          opacity: 0.6,
        }}
      />
    </div>
  );
}

/**
 * Wrapper that detects WebGL support and lazy-loads the Three.js component.
 */
export function ParticleSphereWithFallback() {
  const { hasWebGL, mounted } = useWebGLSupport();

  if (!mounted) {
    return <ParticleSphereFallback />;
  }

  if (!hasWebGL) {
    return <ParticleSphereFallback />;
  }

  return (
    <Suspense fallback={<ParticleSphereFallback />}>
      <ParticleSphere />
    </Suspense>
  );
}

function useWebGLSupport() {
  const [hasWebGL, setHasWebGL] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      setHasWebGL(!!gl);
    } catch {
      setHasWebGL(false);
    }
  }, []);

  return { hasWebGL, mounted };
}

import { useState, useEffect } from "react";
