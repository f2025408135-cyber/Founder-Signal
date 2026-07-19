/**
 * 6 Architectural Clips — hyper-animated, 10-15s each.
 * Each focuses on a different area of the VC Brain architecture.
 * 
 * Clip 1: Memory Layer & Ingestion Pipeline (15s, 450 frames)
 * Clip 2: Six-Agent Swarm Architecture (12s, 360 frames)
 * Clip 3: Three Independent Axes — Never Averaged (12s, 360 frames)
 * Clip 4: Validator & Evidence Chain (15s, 450 frames)
 * Clip 5: Cold-Start Rule & Wide Confidence (12s, 360 frames)
 * Clip 6: Tool-less Synthesizer Boundary (13s, 390 frames)
 */
import { Composition } from "remotion";
import { Clip1MemoryIngestion } from "./clips/Clip1MemoryIngestion";
import { Clip2AgentSwarm } from "./clips/Clip2AgentSwarm";
import { Clip3ThreeAxes } from "./clips/Clip3ThreeAxes";
import { Clip4Validator } from "./clips/Clip4Validator";
import { Clip5ColdStart } from "./clips/Clip5ColdStart";
import { Clip6Toolless } from "./clips/Clip6Toolless";
import { VCBrainVideo } from "./VCBrainVideo";
import { ProductDemoVideo } from "./ProductDemoVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="VCBrainVideo" component={VCBrainVideo} durationInFrames={1800} fps={30} width={1920} height={1080} />
      <Composition id="ProductDemoVideo" component={ProductDemoVideo} durationInFrames={1800} fps={30} width={1920} height={1080} />
      <Composition id="Clip1MemoryIngestion" component={Clip1MemoryIngestion} durationInFrames={450} fps={30} width={1920} height={1080} />
      <Composition id="Clip2AgentSwarm" component={Clip2AgentSwarm} durationInFrames={360} fps={30} width={1920} height={1080} />
      <Composition id="Clip3ThreeAxes" component={Clip3ThreeAxes} durationInFrames={360} fps={30} width={1920} height={1080} />
      <Composition id="Clip4Validator" component={Clip4Validator} durationInFrames={450} fps={30} width={1920} height={1080} />
      <Composition id="Clip5ColdStart" component={Clip5ColdStart} durationInFrames={360} fps={30} width={1920} height={1080} />
      <Composition id="Clip6Toolless" component={Clip6Toolless} durationInFrames={390} fps={30} width={1920} height={1080} />
    </>
  );
};
