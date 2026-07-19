/** EvidenceChip — inline citation chip per spec §9.2.

| Validator status | Chip color | Label |
|------------------|------------|-------|
| verified         | green      | [verified] |
| unverifiable     | yellow     | [unverified] |
| contradicted     | red        | [contradicted] |
| not_disclosed    | gray       | [missing] |

Clicking a chip opens a right-side drawer with full claim details.
*/
import { Sheet, SheetContent, SheetTrigger } from "./ui";
import { evidenceChip, cn } from "../lib/utils";
import type { ClaimRow } from "../lib/api";

export default function EvidenceChip({ claim }: { claim: ClaimRow }) {
  const chip = evidenceChip(claim.validator_status);
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          className={cn(
            "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono leading-none cursor-pointer hover:opacity-80 transition-opacity",
            chip.color
          )}
          title={claim.text}
        >
          [{chip.label}]
        </button>
      </SheetTrigger>
      <SheetContent title="Claim Detail" side="right">
        <ClaimDetail claim={claim} />
      </SheetContent>
    </Sheet>
  );
}

function ClaimDetail({ claim }: { claim: ClaimRow }) {
  return (
    <div className="space-y-4 text-sm">
      <div>
        <div className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)] mb-1">
          Claim Text
        </div>
        <p className="leading-relaxed">{claim.text}</p>
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)] mb-1">
          Kind
        </div>
        <code className="text-xs bg-[var(--color-muted)] px-1.5 py-0.5 rounded">{claim.kind}</code>
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)] mb-1">
          Source
        </div>
        <div className="text-xs space-y-1">
          <div>
            <span className="text-[var(--color-muted-foreground)]">kind: </span>
            <code>{claim.source.kind}</code>
          </div>
          <div>
            <span className="text-[var(--color-muted-foreground)]">ref: </span>
            {claim.source.ref.startsWith("http") ? (
              <a
                href={claim.source.ref}
                target="_blank"
                rel="noreferrer"
                className="text-[var(--color-primary)] underline break-all"
              >
                {claim.source.ref}
              </a>
            ) : (
              <code className="break-all">{claim.source.ref}</code>
            )}
          </div>
          <div>
            <span className="text-[var(--color-muted-foreground)]">retrieved_by: </span>
            <code className="break-all">{claim.source.retrieved_by}</code>
          </div>
          <div>
            <span className="text-[var(--color-muted-foreground)]">raw_payload_hash: </span>
            <code className="break-all">{claim.source.raw_payload_hash.slice(0, 16)}…</code>
          </div>
        </div>
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)] mb-1">
          Validator
        </div>
        <div className="text-xs space-y-1">
          <div>
            <span className="text-[var(--color-muted-foreground)]">status: </span>
            <span className={evidenceChip(claim.validator_status).color + " px-1.5 py-0.5 rounded font-mono"}>
              {claim.validator_status ?? "—"}
            </span>
          </div>
          <div>
            <span className="text-[var(--color-muted-foreground)]">confidence: </span>
            <span className="font-mono">{claim.confidence.toFixed(2)}</span>
          </div>
          {claim.flags.length > 0 && (
            <div className="pt-2">
              {claim.flags.map((flag, i) => (
                <div key={i} className="mt-1 p-2 rounded bg-[var(--color-muted)] text-[11px]">
                  <div className="font-mono font-medium">{flag.flag}</div>
                  <div className="text-[var(--color-muted-foreground)] mt-0.5">{flag.reason}</div>
                  {flag.counter_evidence_ref && (
                    <div className="mt-1 text-[var(--color-contradicted)]">
                      counter: <code>{flag.counter_evidence_ref}</code>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {claim.superseded_by && (
        <div className="text-xs text-[var(--color-muted-foreground)]">
          ⚠ Superseded by claim <code>{claim.superseded_by}</code>
        </div>
      )}

      <div className="text-[10px] text-[var(--color-muted-foreground)] pt-2 border-t border-[var(--color-border)]">
        Created: {new Date(claim.created_at).toLocaleString()}
      </div>
    </div>
  );
}
