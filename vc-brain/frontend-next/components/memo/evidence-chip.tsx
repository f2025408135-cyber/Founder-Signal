"use client";
import { Check, HelpCircle, X, Minus, Snowflake } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { claimEvidenceStatus, evidenceChip, cn } from "@/lib/utils";
import type { ClaimRow } from "@/lib/types";
import { EvidenceDrawer } from "./evidence-drawer";

const ICON_MAP = {
  check: Check,
  help: HelpCircle,
  x: X,
  minus: Minus,
  snowflake: Snowflake,
} as const;

export function EvidenceChip({ claim }: { claim: ClaimRow }) {
  const config = evidenceChip(claimEvidenceStatus(claim.validator_status, claim.flags.at(-1)?.flag));
  const Icon = ICON_MAP[config.icon as keyof typeof ICON_MAP] ?? Minus;

  return (
    <TooltipProvider delayDuration={300}>
      <Sheet>
        <Tooltip>
          <TooltipTrigger asChild>
            <SheetTrigger asChild>
              <button
                className={cn(
                  "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono leading-none",
                  "border cursor-pointer hover:opacity-80 transition-opacity",
                  config.textClass,
                  config.bgClass,
                  config.borderClass
                )}
                title={claim.text}
              >
                <Icon className="w-2.5 h-2.5" />
                [{config.label}]
              </button>
            </SheetTrigger>
          </TooltipTrigger>
          <TooltipContent>
            <div className="max-w-xs">
              <div className="font-mono text-[10px] text-text-muted mb-1">
                {claim.source.kind} · {claim.source.ref.slice(0, 40)}
              </div>
              <div className="text-xs">{claim.text.slice(0, 100)}{claim.text.length > 100 ? "…" : ""}</div>
            </div>
          </TooltipContent>
        </Tooltip>
        <SheetContent side="right" title="Claim Detail">
          <EvidenceDrawer claim={claim} />
        </SheetContent>
      </Sheet>
    </TooltipProvider>
  );
}
