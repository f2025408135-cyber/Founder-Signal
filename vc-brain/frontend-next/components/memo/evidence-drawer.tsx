"use client";
import { claimEvidenceStatus, evidenceChip, cn } from "@/lib/utils";
import type { ClaimRow } from "@/lib/types";

function sourceHref(kind: string, ref: string): string | null {
  if (/^https?:\/\//i.test(ref)) return ref;
  if (kind === "github" && /^[\w.-]+\/[\w.-]+$/.test(ref)) return `https://github.com/${ref}`;
  if (kind === "arxiv" && /^[\w.-]+$/.test(ref)) return `https://arxiv.org/abs/${ref}`;
  const hnId = ref.match(/^(?:item:)?(\d+)$/)?.[1];
  if (kind === "hackernews" && hnId) return `https://news.ycombinator.com/item?id=${hnId}`;
  const applicationId = ref.match(/^application:([0-9a-f-]{36})$/i)?.[1];
  if (kind === "application_form" && applicationId) return `/api/applications/${applicationId}/source`;
  return null;
}

export function EvidenceDrawer({ claim }: { claim: ClaimRow }) {
  const status = claimEvidenceStatus(claim.validator_status, claim.flags.at(-1)?.flag);
  const chip = evidenceChip(status);
  // Extract Langfuse trace link from retrieved_by (format: "agent_name@trace_id/span_id")
  const retrievedBy = claim.source.retrieved_by || "";
  const traceMatch = retrievedBy.match(/@([^/]+)\/(.+)/);
  const traceId = traceMatch?.[1];
  const spanId = traceMatch?.[2];
  const href = sourceHref(claim.source.kind, claim.source.ref);

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
            {href ? (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="text-accent underline break-all"
              >
                {claim.source.ref}
              </a>
            ) : (
              <span className="break-all text-text-secondary">
                {claim.source.ref} <span className="text-text-muted">(source reference)</span>
              </span>
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
              {status}
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
