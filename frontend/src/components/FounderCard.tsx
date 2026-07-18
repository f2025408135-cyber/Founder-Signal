/** Compact card for the inbox list view — spec §9.1.

Renders every field from §9.1's table:
- Company name, geography, sector tag, received time
- Founder axis (score, trend arrow, score bar, cold-start flag, trend text)
- Market axis (verdict)
- Idea↔Mkt axis (fit score)
- Thesis Fit
- Conviction, evidence coverage, open contradictions count
- Recommendation pill
- Action buttons: Open Memo (primary), Pass (ghost), Fast-Track (secondary, only if recommendation==fast_pass)

Cold-start visual treatment: 1px amber border + ❄ icon next to company name.
*/
import { Link } from "react-router-dom";
import { Snowflake } from "lucide-react";
import { Badge, Button, Card, Progress } from "./ui";
import type { InboxCard } from "../lib/api";
import {
  cn,
  countryFlag,
  evidenceChip,
  marketScoreColor,
  recommendationColor,
  timeAgo,
  trendSymbol,
} from "../lib/utils";

interface FounderCardProps {
  card: InboxCard;
  sourcingChannel?: string; // outbound badge
}

export default function FounderCard({ card, sourcingChannel }: FounderCardProps) {
  const trend = trendSymbol(card.trend);
  const founderTrend = trendSymbol(card.founder_trend);
  const recColor = recommendationColor(card.recommendation);
  const coldStart = card.cold_start === true;

  return (
    <Card
      className={cn(
        "p-4 transition-shadow hover:shadow-md cursor-pointer",
        coldStart && "border-[var(--color-cold-start)] border-2"
      )}
    >
      {/* Row 1: header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <h3 className="text-base font-semibold truncate">{card.company_name || "Unknown"}</h3>
          {coldStart && (
            <Snowflake className="w-3.5 h-3.5 text-[var(--color-cold-start)] shrink-0" aria-label="cold-start" />
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {card.geography && (
            <span className="text-xs text-[var(--color-muted-foreground)]" title={card.geography}>
              {countryFlag(card.geography)}
            </span>
          )}
          {card.sector && (
            <Badge variant="secondary" className="text-[10px]">
              {card.sector}
            </Badge>
          )}
          {sourcingChannel && (
            <Badge variant="outline" className="text-[10px] uppercase">
              {sourcingChannel}
            </Badge>
          )}
          <span className="text-xs text-[var(--color-muted-foreground)]">{timeAgo(card.received_at)}</span>
        </div>
      </div>

      <div className="border-t border-[var(--color-border)] my-3" />

      {/* Axes */}
      <div className="space-y-1.5">
        {/* Row 2: Founder */}
        <AxisRow
          label="Founder"
          score={card.founder_score}
          trend={founderTrend}
          scoreBarColor="text-[var(--color-primary)]"
          rightSlot={
            <>
              {coldStart && (
                <span className="text-[10px] text-[var(--color-cold-start)] font-medium ml-2">
                  cold-start⚠️
                </span>
              )}
              <span className="text-[10px] text-[var(--color-muted-foreground)] ml-2">
                trend: {card.founder_trend}
              </span>
            </>
          }
        />

        {/* Row 3: Market */}
        <AxisRow
          label="Market"
          score={
            card.market_score === "bullish"
              ? 100
              : card.market_score === "bear"
                ? 10
                : card.market_score === "neutral"
                  ? 50
                  : null
          }
          trend={trendSymbol("stable")}
          scoreBarColor={marketScoreColor(card.market_score)}
          rightSlot={
            <span className={cn("text-[10px] ml-2 font-medium", marketScoreColor(card.market_score))}>
              {card.market_score || "—"}
            </span>
          }
        />

        {/* Row 4: Idea↔Mkt */}
        <AxisRow
          label="Idea↔Mkt"
          score={card.idea_vs_market_score}
          trend={trendSymbol("stable")}
          scoreBarColor="text-[var(--color-deep-dive)]"
        />

        {/* Row 5: Thesis Fit */}
        <AxisRow
          label="Thesis Fit"
          score={card.thesis_fit_score}
          trend={trendSymbol("stable")}
          scoreBarColor="text-[var(--color-muted-foreground)]"
        />
      </div>

      <div className="border-t border-[var(--color-border)] my-3" />

      {/* Row 6: meta */}
      <div className="flex items-center gap-4 text-xs">
        <span>
          <span className="font-mono font-semibold">{card.conviction?.toFixed(0) ?? "—"}</span>
          <span className="text-[var(--color-muted-foreground)]">/100 conviction</span>
        </span>
        <span className="text-[var(--color-muted-foreground)]">
          evidence {(card.evidence_coverage ?? 0).toFixed(2)}
        </span>
        <span className={cn((card.open_contradictions ?? 0) > 0 && "text-[var(--color-contradicted)]")}>
          contradictions: {card.open_contradictions ?? 0}
        </span>
      </div>

      {/* Row 7: recommendation */}
      <div className="flex items-center mt-2">
        {card.recommendation && (
          <span
            className={cn(
              "inline-flex items-center px-2.5 py-1 rounded-full border text-[11px] font-medium",
              recColor
            )}
          >
            ▸ {card.recommendation}
          </span>
        )}
      </div>

      {/* Row 8: actions */}
      <div className="flex items-center gap-2 mt-3">
        <Link to={`/founders/${card.founder_id}`}>
          <Button size="sm">Open Memo</Button>
        </Link>
        <Button size="sm" variant="ghost">
          Pass
        </Button>
        {card.recommendation === "fast_pass" && (
          <Button size="sm" variant="secondary">
            Fast-Track
          </Button>
        )}
      </div>
    </Card>
  );
}

function AxisRow({
  label,
  score,
  trend,
  scoreBarColor,
  rightSlot,
}: {
  label: string;
  score: number | null;
  trend: { symbol: string; color: string };
  scoreBarColor: string;
  rightSlot?: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-[var(--color-muted-foreground)] w-20 shrink-0">{label}</span>
      <span className={cn("w-3 text-xs", trend.color)}>{trend.symbol}</span>
      <span className="font-mono text-sm w-8 text-right">
        {score != null ? score.toFixed(0) : "—"}
      </span>
      <Progress value={score ?? 0} color={scoreBarColor} />
      {rightSlot}
    </div>
  );
}

// re-export evidenceChip for downstream use
export { evidenceChip };
