"use client";
import { evidenceChip, cn } from "@/lib/utils";
import type { ClaimRow } from "@/lib/types";

export function EvidenceDrawer({ claim }: { claim: ClaimRow }) {
  const chip = evidenceChip(claim.validator_status);
  // Extract Langfuse trace link from retrieved_by (format: "agent_name@trace_id/span_id")
  const retrievedBy = claim.source.retrieved_by || "";
  const traceMatch = retrievedBy.match(/@([^/]+)\/(.+)/);
  const traceId = traceMatch?.[1];
  const spanId = traceMatch?.[2];

  return (
    <div className="space-y-4 text-sm">
      {/* Claim text */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
          Claim Text
        </div>
        <p className="leading-relaxed text-text-primary">{claim.text}</p>
      </div>

      {/* Kind */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">Kind</div>
        <code className="text-xs bg-elevated px-1.5 py-0.5 rounded text-text-secondary">
          {claim.kind}
        </code>
      </div>

      {/* Source */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">Source</div>
        <div className="text-xs space-y-1">
          <div>
            <span className="text-text-muted">kind: </span>
            <code className="text-text-secondary">{claim.source.kind}</code>
          </div>
          <div>
            <span className="text-text-muted">ref: </span>
            {claim.source.ref.startsWith("http") ? (
              <a
                href={claim.source.ref}
                target="_blank"
                rel="noreferrer"
                className="text-accent underline break-all"
              >
                {claim.source.ref}
              </a>
            ) : (
              <code className="break-all text-text-secondary">{claim.source.ref}</code>
            )}
          </div>
          <div>
            <span className="text-text-muted">retrieved_by: </span>
            <code className="break-all text-text-secondary">{claim.source.retrieved_by}</code>
          </div>
          <div>
            <span className="text-text-muted">raw_payload_hash: </span>
            <code className="break-all text-text-secondary">
              {claim.source.raw_payload_hash.slice(0, 16)}…
            </code>
          </div>
        </div>
      </div>

      {/* Validator */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">Validator</div>
        <div className="text-xs space-y-1">
          <div>
            <span className="text-text-muted">status: </span>
            <span
              className={cn(
                "px-1.5 py-0.5 rounded font-mono",
                chip.textClass,
                chip.bgClass
              )}
            >
              {claim.validator_status ?? "—"}
            </span>
          </div>
          <div>
            <span className="text-text-muted">confidence: </span>
            <span className="font-mono" data-numeric>
              {claim.confidence.toFixed(2)}
            </span>
          </div>
          {claim.flags.length > 0 && (
            <div className="pt-2">
              {claim.flags.map((flag, i) => (
                <div key={i} className="mt-1 p-2 rounded bg-elevated text-[11px]">
                  <div className="font-mono font-bold text-text-primary">{flag.flag}</div>
                  <div className="text-text-muted mt-0.5">{flag.reason}</div>
                  {flag.counter_evidence_ref && (
                    <div className="mt-1 text-error">
                      counter: <code>{flag.counter_evidence_ref}</code>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Langfuse trace link (Agentic Traceability) */}
      {traceId && (
        <div>
          <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">
            Agentic Traceability
          </div>
          <a
            href={`${process.env.NEXT_PUBLIC_LANGFUSE_HOST || "http://localhost:3000"}/trace/${traceId}${spanId ? `/span/${spanId}` : ""}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-accent underline"
          >
            View in Langfuse →
          </a>
        </div>
      )}

      {/* Superseded */}
      {claim.superseded_by && (
        <div className="text-xs text-warning">
          ⚠ Superseded by claim <code>{claim.superseded_by}</code>
        </div>
      )}

      <div className="text-[10px] text-text-subtle pt-2 border-t border-border">
        Created: {new Date(claim.created_at).toLocaleString()}
      </div>
    </div>
  );
}
