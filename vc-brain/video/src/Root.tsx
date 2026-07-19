import { Composition } from "remotion";
import { VCBrainVideo } from "./VCBrainVideo";
import { ProductDemoVideo } from "./ProductDemoVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="VCBrainVideo"
        component={VCBrainVideo}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="ProductDemoVideo"
        component={ProductDemoVideo}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
