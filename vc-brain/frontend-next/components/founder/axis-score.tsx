import { cn, trendSymbol } from "@/lib/utils";
import { Progress } from "@/components/ui/primitives";

export function AxisScore({
  label,
  score,
  trend,
  barColor = "text-accent",
  rightSlot,
}: {
  label: string;
  score: number | null;
  trend: string;
  barColor?: string;
  rightSlot?: React.ReactNode;
}) {
  const t = trendSymbol(trend);
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-text-muted w-20 shrink-0">{label}</span>
      <span className={cn("w-3 text-xs", t.color)}>{t.symbol}</span>
      <span className="font-mono text-sm w-8 text-right" data-numeric>
        {score != null ? score.toFixed(0) : "—"}
      </span>
      <Progress value={score ?? 0} color={barColor} />
      {rightSlot}
    </div>
  );
}
