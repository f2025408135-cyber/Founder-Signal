"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

const SOURCE_ANGLES: Record<string, number> = {
  github: -90, arxiv: -30, hackernews: 30, producthunt: 90,
  inbound: 150, pipeline: 210, outbound: 270,
};
const SOURCE_LABELS: Record<string, string> = {
  github: "GITHUB", arxiv: "ARXIV", hackernews: "HN", producthunt: "PH",
  inbound: "INBOUND", pipeline: "PIPELINE", outbound: "OUTBOUND",
};

interface RadarEvent {
  type: string;
  source: string;
  founder_id: string;
  text: string;
  timestamp: string;
  recommendation?: string;
  conviction?: number;
}

interface Blip {
  id: string;
  event: RadarEvent;
  angle: number;
  distance: number;
  age: number;
  pinged: boolean;
  pingIntensity: number;
}

const MAX_BLIPS = 30;
const SWEEP_DURATION = 4_000;
const RADAR_SIZE = 280;
const RADAR_RADIUS = RADAR_SIZE / 2 - 20;
const CENTER = RADAR_SIZE / 2;

function eventKey(event: RadarEvent) {
  return [event.timestamp, event.type, event.source, event.founder_id, event.text].join("|");
}

function stableUnit(input: string, salt: number) {
  let value = 2166136261 + salt;
  for (let i = 0; i < input.length; i += 1) value = Math.imul(value ^ input.charCodeAt(i), 16777619);
  return ((value >>> 0) % 10_000) / 10_000;
}

export function SignalRadar() {
  const router = useRouter();
  const [blips, setBlips] = useState<Blip[]>([]);
  const [logLines, setLogLines] = useState<RadarEvent[]>([]);
  const [sweepAngle, setSweepAngle] = useState(0);
  const [connection, setConnection] = useState<"live" | "connecting" | "offline">("connecting");
  const seenEvents = useRef(new Set<string>());
  const sweepRef = useRef(0);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    let closed = false;
    let eventSource: EventSource | undefined;

    const connect = () => {
      if (closed) return;
      setConnection("connecting");
      eventSource = new EventSource("/api/events/stream");
      eventSource.onopen = () => setConnection("live");
      eventSource.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as RadarEvent;
          const id = eventKey(event);
          if (seenEvents.current.has(id)) return;
          seenEvents.current.add(id);
          if (seenEvents.current.size > 120) seenEvents.current.delete(seenEvents.current.values().next().value as string);
          const source = event.source || "pipeline";
          const baseAngle = SOURCE_ANGLES[source] ?? SOURCE_ANGLES.pipeline;
          setBlips((current) => [
            ...current,
            {
              id,
              event,
              angle: baseAngle + (stableUnit(id, 1) - 0.5) * 20,
              distance: 0.78 + stableUnit(id, 2) * 0.16,
              age: 0,
              pinged: false,
              pingIntensity: 0,
            },
          ].slice(-MAX_BLIPS));
          setLogLines((current) => [...current, event].slice(-50));
        } catch {
          // Ignore malformed telemetry rather than interrupting the deal queue.
        }
      };
      eventSource.onerror = () => {
        eventSource?.close();
        setConnection("offline");
        reconnectTimer = setTimeout(connect, 5_000);
      };
    };

    connect();
    return () => {
      closed = true;
      eventSource?.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  useEffect(() => {
    let previous = 0;
    const animate = (timestamp: number) => {
      if (!previous) previous = timestamp;
      const delta = timestamp - previous;
      previous = timestamp;
      const nextAngle = (sweepRef.current + (delta / SWEEP_DURATION) * 360) % 360;
      sweepRef.current = nextAngle;
      setSweepAngle(nextAngle);
      setBlips((current) => current
        .map((blip) => {
          const age = blip.age + delta / 1_000;
          const distance = Math.abs((((blip.angle - nextAngle) + 540) % 360) - 180);
          const ping = !blip.pinged && distance < 9;
          return { ...blip, age, pinged: blip.pinged || ping, pingIntensity: ping ? 1 : Math.max(0, blip.pingIntensity - delta / 500) };
        })
        .filter((blip) => blip.age < 60)
        .slice(-MAX_BLIPS));
      animationRef.current = requestAnimationFrame(animate);
    };
    animationRef.current = requestAnimationFrame(animate);
    return () => { if (animationRef.current) cancelAnimationFrame(animationRef.current); };
  }, []);

  const polarToCart = (angle: number, distance: number) => {
    const radians = (angle - 90) * (Math.PI / 180);
    const radius = distance * RADAR_RADIUS;
    return { x: CENTER + radius * Math.cos(radians), y: CENTER + radius * Math.sin(radians) };
  };
  const todayCount = logLines.filter((event) => new Date(event.timestamp).toDateString() === new Date().toDateString()).length;
  const statusCopy = connection === "live" ? "LIVE STREAM" : connection === "connecting" ? "CONNECTING" : "STREAM OFFLINE · RETRYING";

  return (
    <section className="radar-console" aria-labelledby="signal-radar-title">
      <div className="radar-console__corner radar-console__corner--tl" aria-hidden="true" />
      <div className="radar-console__corner radar-console__corner--tr" aria-hidden="true" />
      <div className="radar-console__corner radar-console__corner--bl" aria-hidden="true" />
      <div className="radar-console__corner radar-console__corner--br" aria-hidden="true" />
      <header className="radar-console__header">
        <div><p className="technical-label">Pipeline telemetry</p><h2 id="signal-radar-title">Signal Radar</h2></div>
        <div className={`radar-console__status radar-console__status--${connection}`}>{statusCopy}</div>
      </header>
      <div className="radar-console__body">
        <div className="radar-console__scope"><span>SESSION EVENTS TODAY: {todayCount}</span><span>RECENT SIGNALS: {logLines.length}</span></div>
        <div className="radar-console__content">
          <div className="radar-console__scope-graphic">
            <svg className="radar-console__svg" viewBox={`0 0 ${RADAR_SIZE} ${RADAR_SIZE}`} role="img" aria-label="Recent evidence and pipeline event radar">
              <defs>
                <linearGradient id="radar-sweep" x1="0%" y1="50%" x2="100%" y2="50%"><stop offset="0%" stopColor="#f4d58d" stopOpacity="0" /><stop offset="70%" stopColor="#f4d58d" stopOpacity=".3" /><stop offset="95%" stopColor="#fff4d6" stopOpacity=".65" /><stop offset="100%" stopColor="#fff4d6" stopOpacity="0" /></linearGradient>
                <linearGradient id="radar-facet-a" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#f4d58d" stopOpacity=".04" /><stop offset="50%" stopColor="#fff4d6" stopOpacity=".08" /><stop offset="100%" stopColor="#f4d58d" stopOpacity="0" /></linearGradient>
                <linearGradient id="radar-facet-b" x1="100%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stopColor="#e8dcc0" stopOpacity=".03" /><stop offset="50%" stopColor="#f4d58d" stopOpacity=".06" /><stop offset="100%" stopColor="#e8dcc0" stopOpacity="0" /></linearGradient>
                <filter id="radar-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
                <radialGradient id="radar-bg"><stop offset="0%" stopColor="#1a1408" stopOpacity=".4" /><stop offset="100%" stopColor="#0a0908" stopOpacity="0" /></radialGradient>
              </defs>
              <circle cx={CENTER} cy={CENTER} r={RADAR_RADIUS} fill="url(#radar-bg)" />
              <rect width={RADAR_SIZE} height={RADAR_SIZE} fill="url(#radar-facet-a)" transform={`rotate(20 ${CENTER} ${CENTER})`} />
              <rect width={RADAR_SIZE} height={RADAR_SIZE} fill="url(#radar-facet-b)" transform={`rotate(-15 ${CENTER} ${CENTER})`} />
              {[0.25, 0.5, 0.75, 1].map((radius) => <circle key={radius} cx={CENTER} cy={CENTER} r={RADAR_RADIUS * radius} fill="none" stroke="#4a3a1a" strokeWidth="1" strokeOpacity=".3" />)}
              <line x1={CENTER} y1={CENTER - RADAR_RADIUS} x2={CENTER} y2={CENTER + RADAR_RADIUS} stroke="#4a3a1a" strokeWidth=".5" strokeOpacity=".2" />
              <line x1={CENTER - RADAR_RADIUS} y1={CENTER} x2={CENTER + RADAR_RADIUS} y2={CENTER} stroke="#4a3a1a" strokeWidth=".5" strokeOpacity=".2" />
              {Object.entries(SOURCE_ANGLES).map(([source, angle]) => { const point = polarToCart(angle, 1.03); return <text key={source} x={point.x} y={point.y} fill="#4a3a1a" fontSize="7" fontFamily="monospace" textAnchor="middle" dominantBaseline="middle">{SOURCE_LABELS[source]}</text>; })}
              <g transform={`rotate(${sweepAngle} ${CENTER} ${CENTER})`}><path d={`M ${CENTER} ${CENTER} L ${CENTER + RADAR_RADIUS} ${CENTER} A ${RADAR_RADIUS} ${RADAR_RADIUS} 0 0 0 ${CENTER + RADAR_RADIUS * Math.cos(-Math.PI / 6)} ${CENTER + RADAR_RADIUS * Math.sin(-Math.PI / 6)} Z`} fill="url(#radar-sweep)" /><line x1={CENTER} y1={CENTER} x2={CENTER + RADAR_RADIUS} y2={CENTER} stroke="#fff4d6" strokeWidth="1" strokeOpacity=".4" /></g>
              {blips.map((blip) => {
                const point = polarToCart(blip.angle, blip.distance);
                const color = blip.event.type === "aggregator_complete" ? "#e8dcc0" : "#d4af37";
                const label = `${blip.event.source || "pipeline"}: ${blip.event.text}. Open founder memo.`;
                return <g key={blip.id} role={blip.event.founder_id ? "button" : undefined} tabIndex={blip.event.founder_id ? 0 : undefined} aria-label={label} onClick={() => blip.event.founder_id && router.push(`/founders/${blip.event.founder_id}`)} onKeyDown={(event) => { if (blip.event.founder_id && (event.key === "Enter" || event.key === " ")) router.push(`/founders/${blip.event.founder_id}`); }} style={{ cursor: blip.event.founder_id ? "pointer" : "default" }}>
                  {blip.pingIntensity > .1 && <circle cx={point.x} cy={point.y} r={5 + blip.pingIntensity * 8} fill="none" stroke={color} strokeWidth="1" strokeOpacity={blip.pingIntensity * .5} />}
                  <circle cx={point.x} cy={point.y} r={3 + blip.pingIntensity * 2} fill={color} filter="url(#radar-glow)" opacity={Math.max(0, 1 - blip.age / 60)} />
                </g>;
              })}
              <circle cx={CENTER} cy={CENTER} r="2" fill="#d4af37" opacity=".7" />
            </svg>
          </div>
          <div className="radar-console__log"><p>ACTIVITY LOG</p><div>{logLines.length === 0 ? <span className="radar-console__waiting">Awaiting permitted pipeline events. This surface never manufactures activity.</span> : logLines.map((event) => <span key={eventKey(event)}><time>[{new Date(event.timestamp).toLocaleTimeString("en-US", { hour12: false })}]</time> <b>{(SOURCE_LABELS[event.source] || event.source || "PIPELINE").padEnd(8)}</b> {event.text}</span>)}</div></div>
        </div>
      </div>
    </section>
  );
}

export class SignalRadarErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() { return this.state.hasError ? <div className="radar-console radar-console--error">Signal Radar is unavailable. Deal review remains fully available.</div> : this.props.children; }
}
