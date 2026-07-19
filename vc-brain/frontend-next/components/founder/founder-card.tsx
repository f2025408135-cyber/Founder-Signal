"use client";
import Link from "next/link";
import { Snowflake } from "lucide-react";
import { Badge, Button, Card } from "@/components/ui/primitives";
import { AxisScore } from "./axis-score";
import { ConfidenceBand } from "./confidence-band";
import type { InboxCard } from "@/lib/types";
import {
  cn,
  countryFlag,
  marketScoreColor,
  recommendationColor,
  timeAgo,
  trendSymbol,
} from "@/lib/utils";

export function FounderCard({
  card,
  sourcingChannel,
}: {
  card: InboxCard;
  sourcingChannel?: string;
}) {
  const founderTrend = trendSymbol(card.founder_trend);
  const recColor = recommendationColor(card.recommendation);
  const coldStart = card.cold_start === true;

  return (
    <Card
      className={cn(
        "p-4 transition-shadow hover:shadow-md cursor-pointer",
        coldStart ? "border-warning/40" : "border-border"
      )}
    >
      {/* Row 1: header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <h3 className="text-base font-bold truncate text-text-primary">
            {card.company_name || "Unknown"}
          </h3>
          {coldStart && (
            <Snowflake className="w-3.5 h-3.5 text-warning shrink-0" aria-label="cold-start" />
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {card.geography && (
            <span className="text-xs text-text-muted" title={card.geography}>
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
          <span className="text-xs text-text-muted">{timeAgo(card.received_at)}</span>
        </div>
      </div>

      <div className="border-t border-border my-3" />

      {/* Axes */}
      <div className="space-y-1.5">
        <AxisScore
          label="Founder"
          score={card.founder_score}
          trend={card.founder_trend}
          barColor="text-accent"
          rightSlot={
            <>
              {coldStart && (
                <span className="text-[10px] text-warning font-medium ml-2">
                  ❄ cold-start
                </span>
              )}
              <span className="text-[10px] text-text-muted ml-2">
                trend: {card.founder_trend}
              </span>
            </>
          }
        />
        <AxisScore
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
          trend="stable"
          barColor={marketScoreColor(card.market_score)}
          rightSlot={
            <span className={cn("text-[10px] ml-2 font-medium", marketScoreColor(card.market_score))}>
              {card.market_score || "—"}
            </span>
          }
        />
        <AxisScore
          label="Idea↔Mkt"
          score={card.idea_vs_market_score}
          trend="stable"
          barColor="text-accent"
        />
        <AxisScore
          label="Thesis Fit"
          score={card.thesis_fit_score}
          trend="stable"
          barColor="text-text-muted"
        />
      </div>

      <div className="border-t border-border my-3" />

      {/* Row 6: meta */}
      <div className="flex items-center gap-4 text-xs">
        <span>
          <span className="font-mono font-bold" data-numeric>
            {card.conviction?.toFixed(0) ?? "—"}
          </span>
          <span className="text-text-muted">/100 conviction</span>
        </span>
        <span className="text-text-muted">
          evidence {(card.evidence_coverage ?? 0).toFixed(2)}
        </span>
        <span className={cn((card.open_contradictions ?? 0) > 0 && "text-error")}>
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
        <Link href={`/founders/${card.founder_id}`}>
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
