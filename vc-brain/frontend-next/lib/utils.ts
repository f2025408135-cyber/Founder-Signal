import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPct(value: number | null | undefined, digits = 0): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

export function timeAgo(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  const date = new Date(isoString);
  const diffMs = Date.now() - date.getTime();
  const seconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 30) return `${days}d ago`;
  return date.toLocaleDateString();
}

export function countryFlag(iso2: string | null | undefined): string {
  if (!iso2 || iso2.length !== 2) return "";
  const codePoints = iso2
    .toUpperCase()
    .split("")
    .map((c) => 0x1f1e6 + c.charCodeAt(0) - 65);
  return String.fromCodePoint(...codePoints);
}

export function recommendationColor(rec: string | null | undefined): string {
  switch (rec) {
    case "fast_pass":
      return "text-text-primary bg-success-bg border-success-border";
    case "deep_dive":
      return "text-text-primary bg-accent/10 border-border-accent";
    case "pass":
      return "text-text-primary bg-neutral-bg border-neutral-border";
    case "reject":
      return "text-text-primary bg-error-bg border-error-border";
    default:
      return "text-text-primary bg-neutral-bg border-neutral-border";
  }
}

export function marketScoreColor(score: string | number | null | undefined): string {
  if (score == null) return "text-text-muted";
  const label = typeof score === "string" ? score : score >= 75 ? "bullish" : score <= 25 ? "bear" : "neutral";
  switch (label) {
    case "bullish":
      return "text-success";
    case "bear":
      return "text-error";
    default:
      return "text-warning";
  }
}

export function trendSymbol(trend: string | null | undefined): { symbol: string; color: string } {
  switch (trend) {
    case "improving":
      return { symbol: "▲", color: "text-success" };
    case "declining":
      return { symbol: "▼", color: "text-error" };
    case "stable":
      return { symbol: "●", color: "text-text-muted" };
    default:
      return { symbol: "⊘", color: "text-text-subtle" };
  }
}

export const STATE_CONFIG = {
  verified: {
    textClass: "text-text-primary",
    bgClass: "bg-success-bg",
    borderClass: "border-success-border",
    label: "verified",
    icon: "check",
  },
  unverifiable: {
    textClass: "text-text-primary",
    bgClass: "bg-warning-bg",
    borderClass: "border-warning-border",
    label: "unverified",
    icon: "help",
  },
  contradicted: {
    textClass: "text-text-primary",
    bgClass: "bg-error-bg",
    borderClass: "border-error-border",
    label: "contradicted",
    icon: "x",
  },
  not_disclosed: {
    textClass: "text-text-primary",
    bgClass: "bg-neutral-bg",
    borderClass: "border-neutral-border",
    label: "missing",
    icon: "minus",
  },
  low_evidence: {
    textClass: "text-text-primary",
    bgClass: "bg-warning-bg",
    borderClass: "border-warning-border",
    label: "low evidence",
    icon: "help",
  },
  cold_start_inferred: {
    textClass: "text-text-primary",
    bgClass: "bg-warning-bg",
    borderClass: "border-warning-border",
    label: "cold-start",
    icon: "snowflake",
  },
} as const;

export function evidenceChip(status: string | null | undefined) {
  if (!status) return STATE_CONFIG.not_disclosed;
  return STATE_CONFIG[status as keyof typeof STATE_CONFIG] ?? STATE_CONFIG.not_disclosed;
}
