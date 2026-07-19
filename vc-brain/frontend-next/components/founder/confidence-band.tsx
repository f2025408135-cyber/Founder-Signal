import { cn } from "@/lib/utils";

export function ConfidenceBand({
  low,
  high,
  coldStart,
}: {
  low: number;
  high: number;
  coldStart: boolean;
}) {
  const width = high - low;
  if (!coldStart) {
    return (
      <div className="h-1 w-full bg-neutral-bg rounded-full">
        <div
          className="h-full bg-accent rounded-full"
          style={{ marginLeft: `${low}%`, width: `${width}%` }}
        />
      </div>
    );
  }
  return (
    <div className="space-y-1">
      <div className="h-3 w-full bg-neutral-bg rounded-full relative">
        <div
          className="h-full rounded-full border border-warning/60"
          style={{
            marginLeft: `${low}%`,
            width: `${width}%`,
            background: "linear-gradient(to right, rgba(212,168,67,0.4), rgba(212,168,67,0.8))",
          }}
        />
      </div>
      <p className="text-xs text-warning font-medium">
        Confidence band: {low.toFixed(0)}–{high.toFixed(0)} (width: {width.toFixed(0)}) — wide due to cold-start
      </p>
    </div>
  );
}
