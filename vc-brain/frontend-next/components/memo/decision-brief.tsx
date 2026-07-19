import { AlertTriangle, ArrowUpRight, CheckCircle2, CircleHelp, EyeOff, ShieldCheck } from "lucide-react";
import { ConfidenceBand } from "@/components/founder/confidence-band";
import { Badge } from "@/components/ui/primitives";
import type { ClaimRow, FounderMemo, ScoreSnapshotRow } from "@/lib/types";
import { claimEvidenceStatus, cn, formatPct, recommendationColor } from "@/lib/utils";

const STATUS_ORDER = ["verified", "contradicted", "unverifiable", "not_disclosed", "unvalidated"] as const;

const STATUS_ICON = {
  verified: CheckCircle2,
  contradicted: AlertTriangle,
  unverifiable: CircleHelp,
  not_disclosed: EyeOff,
  unvalidated: CircleHelp,
} as const;

export function DecisionBrief({ memo, latestSnapshot }: { memo: FounderMemo; latestSnapshot: ScoreSnapshotRow | null }) {
  const agg = memo.aggregator_output;
  const statusCounts = Object.fromEntries(STATUS_ORDER.map((status) => [status, 0])) as Record<typeof STATUS_ORDER[number], number>;
  for (const claim of memo.claims) {
    const status = claimEvidenceStatus(claim.validator_status, claim.flags.at(-1)?.flag);
    if (status in statusCounts) statusCounts[status as keyof typeof statusCounts] += 1;
  }
  const axes = [
    ["Founder", agg.axes.founder],
    ["Market", agg.axes.market],
    ["Idea / Market", agg.axes.idea_vs_market],
    ["Thesis fit", agg.thesis_fit_score],
  ] as const;

  return (
    <section className="decision-brief" aria-labelledby="decision-brief-title">
      <div className="decision-brief__topline">
        <div>
          <p className="technical-label">Investment committee readout</p>
          <h2 id="decision-brief-title">Decision Brief</h2>
        </div>
        <Badge className={cn("decision-brief__recommendation", recommendationColor(agg.overall_recommendation))}>
          {agg.overall_recommendation.replace("_", " ")}
        </Badge>
      </div>

      <div className="decision-brief__metrics">
        <div className="decision-brief__conviction">
          <span className="technical-label">Conviction</span>
          <strong data-numeric>{agg.overall_conviction.toFixed(0)}<small>/100</small></strong>
          <span>{formatPct(agg.evidence_coverage)} evidence verified</span>
        </div>
        <div className="decision-brief__axes">
          {axes.map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong data-numeric>{typeof value === "number" ? value.toFixed(0) : "—"}</strong>
            </div>
          ))}
        </div>
      </div>

      {latestSnapshot && (
        <div className="decision-brief__confidence">
          <div>
            <span className="technical-label">Decision uncertainty</span>
            <p>{latestSnapshot.cold_start ? "External validation is limited; treat the score as directional." : "Confidence range from the latest evidence snapshot."}</p>
          </div>
          <ConfidenceBand low={latestSnapshot.confidence_band[0]} high={latestSnapshot.confidence_band[1]} coldStart={latestSnapshot.cold_start} />
        </div>
      )}

      <div className="decision-brief__lower">
        <div>
          <span className="technical-label">Evidence ledger</span>
          <div className="decision-brief__ledger">
            {STATUS_ORDER.map((status) => {
              const Icon = STATUS_ICON[status];
              return <span key={status}><Icon aria-hidden="true" /> {statusCounts[status]} {status.replace("_", " ")}</span>;
            })}
          </div>
        </div>
        <div>
          <span className="technical-label">Immediate next actions</span>
          <ul>
            {agg.next_actions.slice(0, 2).map((action) => <li key={action}><ArrowUpRight aria-hidden="true" /> {action}</li>)}
          </ul>
        </div>
        <div className="decision-brief__risks">
          <span className="technical-label">Diligence flags</span>
          <p><AlertTriangle aria-hidden="true" /> {agg.open_contradictions.length} contradictions · {agg.missing_required_sections.length + agg.missing_optional_sections.length} information gaps</p>
        </div>
      </div>
      <div className="decision-brief__provenance"><ShieldCheck aria-hidden="true" /> Built from validator statuses, scoring outputs, and the latest saved snapshot.</div>
    </section>
  );
}
