/** MemoView — renders the memo_markdown from AggregatorOutput.

Per spec §9.2:
- Single-column scrollable document, max-width 760px, centered.
- Every [^claim_id] citation renders as an inline EvidenceChip.
- Cold-start banner at the very top if cold_start==true.
- Due Diligence Log section: markdown table.
- Recommendation section: structured.

The memo_markdown is already structured by the backend's _build_memo_markdown;
we just need to:
1. Extract [^claim_id] citations and substitute with EvidenceChip components.
2. Render the rest as markdown (we use a minimal markdown renderer).
*/
import { Fragment, type ReactNode } from "react";
import EvidenceChip from "./EvidenceChip";
import type { ClaimRow } from "../lib/api";

interface MemoViewProps {
  markdown: string;
  claims: ClaimRow[];
}

export default function MemoView({ markdown, claims }: MemoViewProps) {
  const claimsById = new Map(claims.map((c) => [c.id, c]));

  // Split into lines and render markdown elements
  const lines = markdown.split("\n");

  return (
    <div className="prose prose-sm max-w-none">
      {lines.map((line, i) => (
        <Line key={i} line={line} claimsById={claimsById} />
      ))}
    </div>
  );
}

function Line({ line, claimsById }: { line: string; claimsById: Map<string, ClaimRow> }) {
  // Cold-start banner (blockquote at the top) — per spec §9.2: RED border.
  // The backend embeds this as "> ⚠️ Cold-start founder..." in memo_markdown.
  if (line.startsWith("> ⚠️") || line.startsWith("> ⚠")) {
    return (
      <div className="my-4 p-3 rounded-md border-2 border-[var(--color-contradicted)] bg-[var(--color-contradicted)]/5 text-sm">
        {renderInline(line.replace(/^>\s*/, ""), claimsById)}
      </div>
    );
  }

  // Headings
  if (line.startsWith("# ")) {
    return <h1 className="text-2xl font-bold mt-6 mb-3">{renderInline(line.slice(2), claimsById)}</h1>;
  }
  if (line.startsWith("## ")) {
    return <h2 className="text-lg font-semibold mt-6 mb-2 pb-1 border-b border-[var(--color-border)]">{renderInline(line.slice(3), claimsById)}</h2>;
  }
  if (line.startsWith("### ")) {
    return <h3 className="text-base font-semibold mt-4 mb-1">{renderInline(line.slice(4), claimsById)}</h3>;
  }

  // Bold subheadings (e.g. "**Strengths:**")
  if (line.startsWith("**") && line.endsWith(":**")) {
    return <div className="font-semibold mt-3 mb-1 text-sm">{renderInline(line, claimsById)}</div>;
  }

  // Markdown table (Due Diligence Log)
  if (line.startsWith("|")) {
    // Collect the table block — but here we render line-by-line so we just render one row
    if (line.startsWith("|--") || line.startsWith("|-")) {
      return null; // skip the separator
    }
    const cells = line.split("|").slice(1, -1).map((c) => c.trim());
    // If first row is the header (Claim, Status, Confidence, Source), bold it
    const isHeader = cells[0] === "Claim";
    return (
      <table className="w-full my-2 text-xs border border-[var(--color-border)]">
        <tbody>
          <tr className={isHeader ? "bg-[var(--color-muted)] font-semibold" : ""}>
            {cells.map((cell, i) => (
              <td key={i} className="px-2 py-1 border-r border-[var(--color-border)] last:border-r-0">
                {renderInline(cell, claimsById)}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    );
  }

  // Bullets
  if (line.startsWith("- ")) {
    return (
      <div className="flex gap-2 my-0.5 text-sm">
        <span className="text-[var(--color-muted-foreground)]">•</span>
        <div className="flex-1">{renderInline(line.slice(2), claimsById)}</div>
      </div>
    );
  }

  // Empty line
  if (!line.trim()) {
    return <div className="h-2" />;
  }

  // Default paragraph
  return <p className="text-sm my-1 leading-relaxed">{renderInline(line, claimsById)}</p>;
}

/** Render a line with inline [^claim_id] citations as EvidenceChip components. */
function renderInline(text: string, claimsById: Map<string, ClaimRow>): ReactNode {
  // Match [^uuid] citations
  const parts = text.split(/(\[\^[^\]]+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const m = part.match(/^\[\^([^\]]+)\]$/);
        if (m) {
          const claimId = m[1];
          const claim = claimsById.get(claimId);
          if (claim) {
            return <EvidenceChip key={i} claim={claim} />;
          }
          // Fallback: render as a missing claim chip
          return (
            <span key={i} className="text-[10px] text-[var(--color-muted-foreground)] font-mono">
              [^{claimId.slice(0, 8)}…]
            </span>
          );
        }
        return <Fragment key={i}>{renderBold(part)}</Fragment>;
      })}
    </>
  );
}

function renderBold(text: string): ReactNode {
  // Split on **bold**
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}
