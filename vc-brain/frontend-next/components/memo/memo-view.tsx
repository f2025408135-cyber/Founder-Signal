"use client";
import { Fragment, type ReactNode } from "react";
import { EvidenceChip } from "./evidence-chip";
import type { ClaimRow } from "@/lib/types";

export function MemoView({ markdown, claims }: { markdown: string; claims: ClaimRow[] }) {
  const claimsById = new Map(claims.map((c) => [c.id, c]));
  const lines = markdown.split("\n");
  const blocks: ReactNode[] = [];

  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].startsWith("|")) {
      const tableLines: string[] = [];
      while (index < lines.length && lines[index].startsWith("|")) {
        tableLines.push(lines[index]);
        index += 1;
      }
      blocks.push(<MemoTable key={`table-${index}`} lines={tableLines} claimsById={claimsById} />);
      index -= 1;
      continue;
    }
    blocks.push(<Line key={index} line={lines[index]} claimsById={claimsById} />);
  }

  return (
    <div className="prose prose-sm max-w-none">
      {blocks}
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

function MemoTable({ lines, claimsById }: { lines: string[]; claimsById: Map<string, ClaimRow> }) {
  const rows = lines
    .filter((line) => !line.startsWith("|--") && !line.startsWith("|-"))
    .map((line) => line.split("|").slice(1, -1).map((cell) => cell.trim()));
  if (rows.length === 0) return null;
  const [header, ...body] = rows;
  return (
    <div className="my-4 overflow-x-auto border border-border-strong bg-canvas-base/30">
      <table className="w-full min-w-[620px] border-collapse text-left text-xs">
        <thead className="bg-elevated/80 text-text-primary">
          <tr>{header.map((cell, index) => <th key={index} className="border-b border-border px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-data">{renderInline(cell, claimsById)}</th>)}</tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => <tr key={rowIndex} className="border-b border-border last:border-b-0 hover:bg-elevated/45">{row.map((cell, index) => <td key={index} className="px-3 py-2 align-top text-text-secondary">{renderInline(cell, claimsById)}</td>)}</tr>)}
        </tbody>
      </table>
    </div>
  );
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
