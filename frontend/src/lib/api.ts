/** API client + TanStack Query hooks.

All requests go through the Vite dev proxy (localhost:5173/api → localhost:8000/api).
 */

const BASE = "/api";

export interface InboxCard {
  founder_id: string;
  founder_name: string;
  company_id: string | null;
  company_name: string | null;
  geography: string | null;
  sector: string | null;
  received_at: string | null;
  founder_score: number | null;
  founder_trend: string;
  market_score: string | null;
  idea_vs_market_score: number | null;
  thesis_fit_score: number | null;
  conviction: number | null;
  evidence_coverage: number | null;
  open_contradictions: number;
  recommendation: string | null;
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

export interface FounderMemo {
  founder_id: string;
  founder_name: string;
  company_name: string | null;
  company_website_url: string | null;
  geography: string | null;
  sector: string | null;
  // Demo-only fields surfaced from founder.bio_text JSON
  photo_url: string | null;
  university_image_url: string | null;
  image_source: { photo: string; university: string };
  education: {
    university: string;
    degree: string;
    year: number;
    university_country?: string;
  } | null;
  prior_experience: string | null;
  github_profile: {
    username: string;
    repo_count: number;
    primary_language: string;
    commit_activity: string;
    stars: number;
    top_repo?: string;
    contributors?: number;
  } | null;
  deck_summary: string | null;
  categories: string[];
  aggregator_output: {
    id: string;
    overall_recommendation: string;
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

export interface TraceResponse {
  trace_id: string;
  available: boolean;
  reason?: string;
  nodes?: TraceNode[];
  raw?: unknown;
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

export interface LatencyResponse {
  window_hours: number;
  n_applications: number;
  phases: Record<
    string,
    {
      count: number;
      p50_seconds: number | null;
      p95_seconds: number | null;
      mean_seconds: number | null;
      max_seconds: number | null;
    }
  >;
  acceptance_90s: boolean;
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
  ingestion_complete_at: string | null;
  validator_complete_at: string | null;
  scoring_complete_at: string | null;
  aggregator_complete_at: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const body = await r.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore parse error
    }
    throw new Error(`${r.status}: ${detail}`);
  }
  // 204 / empty body
  if (r.status === 204) return null as T;
  const ct = r.headers.get("content-type") || "";
  if (!ct.includes("application/json")) return null as T;
  return r.json() as Promise<T>;
}

export const api = {
  ping: () => request<{ pong: boolean }>("/ping"),
  health: () => fetch("/health").then((r) => r.json()),

  // Inbox
  getInbox: (params?: {
    sector?: string;
    geography?: string;
    recommendation?: string;
    cold_start?: boolean;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.sector) qs.set("sector", params.sector);
    if (params?.geography) qs.set("geography", params.geography);
    if (params?.recommendation) qs.set("recommendation", params.recommendation);
    if (params?.cold_start !== undefined) qs.set("cold_start", String(params.cold_start));
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return request<InboxResponse>(`/applications/inbox${q ? `?${q}` : ""}`);
  },

  // Founder detail
  getFounderCard: (id: string) => request<InboxCard>(`/founders/${id}/card`),
  getFounderMemo: (id: string) => request<FounderMemo>(`/founders/${id}/memo`),

  // Thesis
  getThesis: () => request<Thesis>(`/thesis`),
  updateThesis: (patch: Partial<Thesis>) =>
    request<Thesis>(`/thesis`, {
      method: "POST",
      body: JSON.stringify(patch),
    }),

  // Outbound
  triggerOutboundScan: (lookbackHours = 1) =>
    request<{ scan_id: string; status: string; lookback_hours: number; started_at: string }>(
      `/outbound/scan?lookback_hours=${lookbackHours}`,
      { method: "POST" }
    ),
  getOutboundQueue: (limit = 50) =>
    request<{ total: number; founders: OutboundCard[] }>(`/outbound/queue?limit=${limit}`),

  // Compound query
  query: (query: string, limit = 20) =>
    request<QueryResponse>(`/query`, {
      method: "POST",
      body: JSON.stringify({ query, limit }),
    }),

  // Traces
  getTrace: (runId: string) => request<TraceResponse>(`/traces/${runId}`),

  // Admin
  getLatency: (hours = 24) => request<LatencyResponse>(`/admin/latency?hours=${hours}`),

  // Applications
  createApplication: (payload: ApplicationCreatePayload) =>
    request<ApplicationResponse>(`/applications`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
