import { Composition } from "remotion";
import { VCBrainVideo } from "./VCBrainVideo";

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
    </>
  );
};
