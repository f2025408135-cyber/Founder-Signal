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
  return (
    <div className="space-y-1">
      <div className={coldStart ? "h-3 w-full bg-neutral-bg rounded-full relative" : "h-2 w-full bg-neutral-bg rounded-full relative"}>
        <div
          className={coldStart ? "h-full rounded-full border border-warning-border bg-warning/40" : "h-full rounded-full border border-border-accent bg-accent/55"}
          style={{
            marginLeft: `${low}%`,
            width: `${width}%`,
          }}
        />
      </div>
      <p className={coldStart ? "text-xs text-warning font-medium" : "text-xs text-text-muted font-medium"}>
        Confidence range: {low.toFixed(0)}–{high.toFixed(0)}
        {coldStart && ` (width: ${width.toFixed(0)}) — wide due to cold-start`}
      </p>
    </div>
  );
}
