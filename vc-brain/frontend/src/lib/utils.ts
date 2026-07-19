import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Tailwind-aware className combiner (shadcn pattern). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a number as a percentage (0.62 -> "62%"). */
export function formatPct(value: number | null | undefined, digits = 0): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

/** Format a USD amount with appropriate suffix (B/M/K). */
export function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

/** Relative time formatter (e.g. "2h ago", "just now"). */
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

/** Convert ISO-2 country code to flag emoji. */
export function countryFlag(iso2: string | null | undefined): string {
  if (!iso2 || iso2.length !== 2) return "";
  const codePoints = iso2
    .toUpperCase()
    .split("")
    .map((c) => 0x1f1e6 + c.charCodeAt(0) - 65);
  return String.fromCodePoint(...codePoints);
}

/** Map a recommendation string to its display color class. */
export function recommendationColor(rec: string | null | undefined): string {
  switch (rec) {
    case "fast_pass":
      return "text-[var(--color-fast-pass)] bg-[var(--color-fast-pass)]/10 border-[var(--color-fast-pass)]/30";
    case "deep_dive":
      return "text-[var(--color-deep-dive)] bg-[var(--color-deep-dive)]/10 border-[var(--color-deep-dive)]/30";
    case "pass":
      return "text-[var(--color-pass)] bg-[var(--color-pass)]/10 border-[var(--color-pass)]/30";
    case "reject":
      return "text-[var(--color-reject)] bg-[var(--color-reject)]/10 border-[var(--color-reject)]/30";
    default:
      return "text-[var(--color-muted-foreground)] bg-[var(--color-muted)] border-[var(--color-border)]";
  }
}

/** Map a market score (numeric or label) to its display color. */
export function marketScoreColor(score: string | number | null | undefined): string {
  if (score == null) return "text-[var(--color-muted-foreground)]";
  const label = typeof score === "string" ? score : score >= 75 ? "bullish" : score <= 25 ? "bear" : "neutral";
  switch (label) {
    case "bullish":
      return "text-[var(--color-bullish)]";
    case "bear":
      return "text-[var(--color-bear)]";
    default:
      return "text-[var(--color-neutral)]";
  }
}

/** Map a trend string to its arrow + color. */
export function trendSymbol(trend: string | null | undefined): { symbol: string; color: string } {
  switch (trend) {
    case "improving":
      return { symbol: "▲", color: "text-[var(--color-bullish)]" };
    case "declining":
      return { symbol: "▼", color: "text-[var(--color-bear)]" };
    case "stable":
      return { symbol: "●", color: "text-[var(--color-muted-foreground)]" };
    default:
      return { symbol: "⊘", color: "text-[var(--color-muted-foreground)]" };
  }
}

/** Map a validator status to its chip color + label (spec §9.2 evidence chips). */
export function evidenceChip(status: string | null | undefined): { color: string; label: string } {
  switch (status) {
    case "verified":
      return { color: "text-[var(--color-verified)] bg-[var(--color-verified)]/10", label: "verified" };
    case "unverifiable":
      return { color: "text-[var(--color-unverified)] bg-[var(--color-unverified)]/10", label: "unverified" };
    case "contradicted":
      return { color: "text-[var(--color-contradicted)] bg-[var(--color-contradicted)]/10", label: "contradicted" };
    case "not_disclosed":
      return { color: "text-[var(--color-not-disclosed)] bg-[var(--color-not-disclosed)]/10", label: "missing" };
    case "low_evidence":
      return { color: "text-[var(--color-unverified)] bg-[var(--color-unverified)]/10", label: "low evidence" };
    case "cold_start_inferred":
      return { color: "text-[var(--color-cold-start)] bg-[var(--color-cold-start)]/10", label: "cold-start" };
    default:
      return { color: "text-[var(--color-muted-foreground)] bg-[var(--color-muted)]", label: "—" };
  }
}
