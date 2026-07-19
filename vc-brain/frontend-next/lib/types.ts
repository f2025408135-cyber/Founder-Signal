// TypeScript interfaces mirroring backend schemas (lib/types.ts)

export interface InboxCard {
  founder_id: string;
  founder_name: string;
  company_id: string | null;
  company_name: string | null;
  geography: string | null;
  sector: string | null;
  received_at: string | null;
  founder_score: number | null;
  founder_trend: "improving" | "declining" | "stable" | "insufficient_data";
  market_score: "bullish" | "neutral" | "bear" | null;
  idea_vs_market_score: number | null;
  thesis_fit_score: number | null;
  conviction: number | null;
  evidence_coverage: number | null;
  open_contradictions: number;
  recommendation: "fast_pass" | "deep_dive" | "pass" | "reject" | null;
  cold_start: boolean | null;
  trend: string;
  trace_id: string | null;
  computed_at: string | null;
  application_id?: string;
}

export interface InboxResponse {
  total: number;
  cards: InboxCard[];
  filters: Record<string, unknown>;
}

export interface ClaimRow {
  id: string;
  kind: string;
  text: string;
  source: {
    kind: string;
    ref: string;
    raw_payload_hash: string;
    retrieved_by: string;
    ingested_at: string;
  };
  confidence: number;
  flags: Array<{
    flag: string;
    set_by: string;
    set_at: string;
    reason: string;
    counter_evidence_ref: string | null;
  }>;
  validator_status: string | null;
  superseded_by: string | null;
  created_at: string;
}

export interface ScoreSnapshotRow {
  computed_at: string;
  score: number;
  trend: string;
  trigger: string;
  cold_start: boolean;
  component_scores: Record<string, number>;
  confidence_band: [number, number];
}

export interface FounderMemo {
  founder_id: string;
  founder_name: string;
  company_name: string | null;
  aggregator_output: {
    id: string;
    overall_recommendation: "fast_pass" | "deep_dive" | "pass" | "reject";
    overall_conviction: number;
    axes: Record<string, number>;
    axes_trends: Record<string, string>;
    thesis_fit_score: number;
    evidence_coverage: number;
    open_contradictions: string[];
    missing_required_sections: string[];
    missing_optional_sections: string[];
    memo_markdown: string;
    next_actions: string[];
    computed_at: string;
    trace_id: string | null;
  };
  claims: ClaimRow[];
  score_history: ScoreSnapshotRow[];
  rescore_reason: string;
}

export interface Thesis {
  id: string;
  name: string;
  sectors: string[];
  stage: string[];
  geography: string[];
  check_size_usd: number;
  ownership_target_pct: number;
  risk_appetite: {
    max_founder_age_years: number;
    accepts_no_prior_funding: boolean;
    accepts_no_github: boolean;
    accepts_cold_start: boolean;
    min_conviction_score: number;
    allow_neutral_market: boolean;
  };
  created_at: string;
  updated_at: string;
  active: boolean;
}

export interface OutboundCard extends InboxCard {
  sourcing_channel: string;
  signal_detected_at: string;
  conviction_delta: number;
}

export interface QueryMatch {
  founder_id: string;
  score: number;
  matched_attributes: string[];
  founder_name: string;
  company_name: string | null;
}

export interface QueryResponse {
  query: string;
  decomposed_attributes: string[];
  matches: QueryMatch[];
}

export interface TraceNode {
  id: string | null;
  name: string | null;
  type: string | null;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  latency_ms: number | null;
  start_time: string | null;
  end_time: string | null;
  status: string;
  level: string;
}

export interface TraceResponse {
  trace_id: string;
  available: boolean;
  reason?: string;
  nodes?: TraceNode[];
  raw?: unknown;
}

export interface ApplicationCreatePayload {
  founder_name: string;
  founder_email: string;
  founder_bio_text: string;
  company_name: string;
  company_website_url?: string | null;
  deck_url?: string | null;
  github_repo_slugs?: string[];
  accelerator?: string | null;
  hq_country: string;
  sector_self_reported: string;
}

export interface ApplicationResponse {
  id: string;
  founder_id: string;
  company_id: string;
  received_at: string;
  status: string;
  raw_payload: Record<string, unknown>;
  aggregator_output_id: string | null;
  trace_id: string | null;
}
