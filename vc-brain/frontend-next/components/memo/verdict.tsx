"use client";

import { EvidenceChip } from "./evidence-chip";
import type { ClaimRow } from "@/lib/types";
import { claimEvidenceStatus } from "@/lib/utils";

const BEAR_PRIORITY: Record<string, number> = {
  contradicted: 0,
  unverifiable: 1,
  not_disclosed: 2,
};

function claimStatus(claim: ClaimRow): string {
  return claimEvidenceStatus(claim.validator_status, claim.flags.at(-1)?.flag);
}

function tally(claims: ClaimRow[], status: string): number {
  return claims.filter((claim) => claimStatus(claim) === status).length;
}

export function Verdict({
  founderId,
  founderName,
  claims,
  memoMarkdown,
}: {
  founderId: string;
  founderName: string;
  claims: ClaimRow[];
  memoMarkdown: string;
}) {
  const bullSwotClaimIds = swotClaimIds(memoMarkdown, ["Strengths", "Opportunities"]);
  const bearSwotClaimIds = swotClaimIds(memoMarkdown, ["Weaknesses", "Threats"]);
  const bullClaims = claims
    .filter((claim) => claimStatus(claim) === "verified")
    .sort((a, b) => Number(bullSwotClaimIds.has(b.id)) - Number(bullSwotClaimIds.has(a.id)) || b.confidence - a.confidence)
    .slice(0, 4);
  const bearClaims = claims
    .filter((claim) => claimStatus(claim) in BEAR_PRIORITY)
    .sort((a, b) => {
      const swotPriority = Number(bearSwotClaimIds.has(b.id)) - Number(bearSwotClaimIds.has(a.id));
      if (swotPriority) return swotPriority;
      const priority = BEAR_PRIORITY[claimStatus(a)] - BEAR_PRIORITY[claimStatus(b)];
      return priority || a.confidence - b.confidence;
    })
    .slice(0, 4);
  const verified = tally(claims, "verified");
  const contradicted = tally(claims, "contradicted");
  const unverifiable = tally(claims, "unverifiable");
  const missing = tally(claims, "not_disclosed");
  const unvalidated = tally(claims, "unvalidated");

  return (
    <section key={founderId} className="verdict" aria-labelledby={`verdict-title-${founderId}`}>
      <header className="verdict__header">
        <div>
          <p className="verdict__eyebrow">Adversarial evidence view</p>
          <h2 id={`verdict-title-${founderId}`} className="verdict__title">The Verdict: {founderName}</h2>
        </div>
        <p className="verdict__tally" aria-label={`${verified} supporting, ${contradicted} contradicting, ${unverifiable} unverifiable, ${missing} not disclosed, ${unvalidated} unvalidated claims`}>
          <span>{verified} supporting</span>
          <span>{contradicted} contradicting</span>
          <span>{unverifiable} unverifiable</span>
          {missing > 0 && <span>{missing} missing</span>}
          {unvalidated > 0 && <span>{unvalidated} unvalidated</span>}
        </p>
      </header>

      <div className="verdict__panels">
        <CasePanel tone="bull" title="The Bull Case" marker="▲" claims={bullClaims} />
        <div className="verdict__seam" aria-hidden="true" />
        <CasePanel tone="bear" title="The Bear Case" marker="▼" claims={bearClaims} />
      </div>
    </section>
  );
}

function swotClaimIds(markdown: string, headings: string[]): Set<string> {
  const swot = markdown.match(/## SWOT\s*([\s\S]*?)(?=\n## |$)/i)?.[1] || "";
  const ids = new Set<string>();
  for (const heading of headings) {
    const block = swot.match(new RegExp(`\\*\\*${heading}:\\*\\*([\\s\\S]*?)(?=\\*\\*[A-Za-z ]+:\\*\\*|$)`, "i"))?.[1] || "";
    for (const match of block.matchAll(/\[\^([^\]]+)\]/g)) ids.add(match[1]);
  }
  return ids;
}

function CasePanel({
  tone,
  title,
  marker,
  claims,
}: {
  tone: "bull" | "bear";
  title: string;
  marker: string;
  claims: ClaimRow[];
}) {
  const emptyMessage = tone === "bull"
    ? "No verified supporting claims surfaced yet."
    : "No material contradictions or risk flags surfaced.";

  return (
    <section className={`verdict__panel verdict__panel--${tone}`} aria-label={title}>
      <div className="verdict__panel-heading">
        <span className="verdict__direction" aria-hidden="true">{marker}</span>
        <h3>{title}</h3>
      </div>
      {claims.length === 0 ? (
        <p className="verdict__empty">{emptyMessage}</p>
      ) : (
        <ul className="verdict__list">
          {claims.map((claim) => (
            <li key={claim.id} className="verdict__item">
              <span className="verdict__diamond" aria-hidden="true" />
              <span className="verdict__claim">{claim.text}</span>
              <EvidenceChip claim={claim} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
