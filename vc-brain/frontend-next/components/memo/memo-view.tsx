"use client";
import { Fragment, type ReactNode } from "react";
import { EvidenceChip } from "./evidence-chip";
import type { ClaimRow } from "@/lib/types";

export function MemoView({ markdown, claims }: { markdown: string; claims: ClaimRow[] }) {
  const claimsById = new Map(claims.map((c) => [c.id, c]));
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
  // Cold-start banner (blockquote at top) — RED border per spec §9.2
  if (line.startsWith("> ⚠️") || line.startsWith("> ⚠")) {
    return (
      <div className="my-4 p-3 rounded-md border-2 border-error bg-error-bg text-sm">
        {renderInline(line.replace(/^>\s*/, ""), claimsById)}
      </div>
    );
  }

  // Headings
  if (line.startsWith("# ")) {
    return (
      <h1 className="text-2xl font-bold mt-6 mb-3 text-text-primary">
        {renderInline(line.slice(2), claimsById)}
      </h1>
    );
  }
  if (line.startsWith("## ")) {
    const heading = line.slice(3);
    return (
      <h2
        id={heading.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")}
        className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-border text-text-primary"
      >
        {renderInline(heading, claimsById)}
      </h2>
    );
  }
  if (line.startsWith("### ")) {
    return (
      <h3 className="text-base font-bold mt-4 mb-1 text-text-primary">
        {renderInline(line.slice(4), claimsById)}
      </h3>
    );
  }

  // Bold subheadings
  if (line.startsWith("**") && line.endsWith(":**")) {
    return (
      <div className="font-bold mt-3 mb-1 text-sm text-text-primary">
        {renderInline(line, claimsById)}
      </div>
    );
  }

  // Markdown table (Due Diligence Log)
  if (line.startsWith("|")) {
    if (line.startsWith("|--") || line.startsWith("|-")) return null;
    const cells = line.split("|").slice(1, -1).map((c) => c.trim());
    const isHeader = cells[0] === "Claim";
    return (
      <table className="w-full my-2 text-xs border border-border">
        <tbody>
          <tr className={isHeader ? "bg-elevated font-bold" : ""}>
            {cells.map((cell, i) => (
              <td
                key={i}
                className="px-2 py-1 border-r border-border last:border-r-0 text-text-secondary"
              >
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
        <span className="text-text-muted">•</span>
        <div className="flex-1 text-text-secondary">{renderInline(line.slice(2), claimsById)}</div>
      </div>
    );
  }

  // Empty line
  if (!line.trim()) return <div className="h-2" />;

  // Default paragraph
  return <p className="text-sm my-1 leading-relaxed text-text-secondary">{renderInline(line, claimsById)}</p>;
}

function renderInline(text: string, claimsById: Map<string, ClaimRow>): ReactNode {
  const parts = text.split(/(\[\^[^\]]+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const m = part.match(/^\[\^([^\]]+)\]$/);
        if (m) {
          const claimId = m[1];
          const claim = claimsById.get(claimId);
          if (claim) return <EvidenceChip key={i} claim={claim} />;
          return (
            <span key={i} className="text-[10px] text-text-subtle font-mono">
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
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-text-primary">{part.slice(2, -2)}</strong>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}
