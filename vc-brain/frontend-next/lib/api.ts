// Typed API client (lib/api.ts)

const BASE = "/api";

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
  if (r.status === 204) return null as T;
  const ct = r.headers.get("content-type") || "";
  if (!ct.includes("application/json")) return null as T;
  return r.json() as Promise<T>;
}

export const api = {
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
    return request<import("@/lib/types").InboxResponse>(`/applications/inbox${q ? `?${q}` : ""}`);
  },

  // Founder detail
  getFounderMemo: (id: string) =>
    request<import("@/lib/types").FounderMemo>(`/founders/${id}/memo`),

  // Thesis
  getThesis: () => request<import("@/lib/types").Thesis>(`/thesis`),
  updateThesis: (patch: Partial<import("@/lib/types").Thesis>) =>
    request<import("@/lib/types").Thesis>(`/thesis`, {
      method: "POST",
      body: JSON.stringify(patch),
    }),

  // Outbound
  getOutboundQueue: (limit = 50) =>
    request<{ total: number; founders: import("@/lib/types").OutboundCard[] }>(
      `/outbound/queue?limit=${limit}`
    ),
  triggerOutboundScan: (lookbackHours = 1) =>
    request<{ scan_id: string; status: string; lookback_hours: number; started_at: string }>(
      `/outbound/scan?lookback_hours=${lookbackHours}`,
      { method: "POST" }
    ),

  // Applications (for funnel)
  getApplications: (limit = 50) =>
    request<{
      total: number;
      applications: Array<{
        id: string;
        founder_id: string;
        founder_name: string;
        company_id: string;
        company_name: string;
        received_at: string;
        status: string;
        trace_id: string | null;
      }>;
    }>(`/applications?limit=${limit}`),

  // Compound query
  query: (query: string, limit = 20) =>
    request<import("@/lib/types").QueryResponse>(`/query`, {
      method: "POST",
      body: JSON.stringify({ query, limit }),
    }),

  // Traces
  getTrace: (runId: string) =>
    request<import("@/lib/types").TraceResponse>(`/traces/${runId}`),

  // Health
  ping: () => request<{ pong: boolean }>(`/ping`),
};
