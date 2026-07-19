"use client";
import { useState } from "react";
import Link from "next/link";
import { 
  Sparkles, Inbox, Network, Filter, FileText, 
  ChevronDown, ChevronRight, ArrowRight, 
  Search, Activity, Snowflake, Check, X, AlertCircle,
  MessageCircle, Radar, ClipboardList, GitBranch
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Badge, Button } from "@/components/ui/primitives";
import { FounderCard } from "@/components/founder/founder-card";
import { AxisScore } from "@/components/founder/axis-score";
import { ConfidenceBand } from "@/components/founder/confidence-band";
import { cn } from "@/lib/utils";
import type { InboxCard } from "@/lib/types";

const SECTIONS = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "fin-agent", label: "Fin Agent", icon: Sparkles },
  { id: "inbox", label: "Inbox & Cards", icon: Inbox },
  { id: "memo", label: "Memo & Evidence", icon: FileText },
  { id: "radar", label: "Signal Radar", icon: Radar },
  { id: "network", label: "Network View", icon: Network },
  { id: "funnel", label: "Funnel View", icon: Filter },
  { id: "thesis", label: "Thesis Config", icon: ClipboardList },
  { id: "cold-start", label: "Cold-Start Rule", icon: Snowflake },
  { id: "trust", label: "Trust Scores", icon: Check },
  { id: "pipeline", label: "Pipeline Architecture", icon: GitBranch },
];

// Mock data for the guide (using real InboxCard type)
const mockCard: InboxCard = {
  founder_id: "demo-1",
  founder_name: "Jane Doe",
  company_id: "demo-co-1",
  company_name: "StealthCo",
  geography: "DE",
  sector: "AI infra",
  received_at: new Date(Date.now() - 2 * 3600000).toISOString(),
  founder_score: 62,
  founder_trend: "insufficient_data",
  market_score: "neutral",
  idea_vs_market_score: 55,
  thesis_fit_score: 74,
  conviction: 35,
  evidence_coverage: 0.0,
  open_contradictions: 0,
  recommendation: "deep_dive",
  cold_start: true,
  trend: "insufficient_data",
  trace_id: null,
  computed_at: new Date().toISOString(),
};

export default function GuidePage() {
  const [openSection, setOpenSection] = useState<string>("overview");

  const toggle = (id: string) => setOpenSection(openSection === id ? "" : id);

  return (
    <AppShell>
      <div className="flex h-full">
        {/* Left: section nav */}
        <aside className="w-64 border-r border-border bg-card overflow-y-auto p-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-text-muted mb-3 px-2">Usage Guide</h2>
          <nav className="space-y-0.5">
            {SECTIONS.map((s) => {
              const Icon = s.icon;
              const active = openSection === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => toggle(s.id)}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors text-left",
                    active ? "bg-elevated text-text-primary font-medium" : "text-text-muted hover:text-text-primary hover:bg-elevated"
                  )}
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  {s.label}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Right: content */}
        <main className="flex-1 overflow-y-auto px-8 py-6 max-w-4xl">
          {/* Overview */}
          {openSection === "overview" && <OverviewSection />}
          {openSection === "fin-agent" && <FinAgentSection />}
          {openSection === "inbox" && <InboxSection mockCard={mockCard} />}
          {openSection === "memo" && <MemoSection />}
          {openSection === "radar" && <RadarSection />}
          {openSection === "network" && <NetworkSection />}
          {openSection === "funnel" && <FunnelSection />}
          {openSection === "thesis" && <ThesisSection />}
          {openSection === "cold-start" && <ColdStartSection />}
          {openSection === "trust" && <TrustSection />}
          {openSection === "pipeline" && <PipelineSection />}
        </main>
      </div>
    </AppShell>
  );
}

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">{title}</h1>
        {subtitle && <p className="text-sm text-text-muted mt-1">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function Step({ num, title, children }: { num: number; title: string; children: React.ReactNode }) {
  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center text-xs font-bold text-white shrink-0">{num}</div>
        <div className="flex-1">
          <h3 className="text-sm font-bold text-text-primary mb-1">{title}</h3>
          <div className="text-sm text-text-secondary">{children}</div>
        </div>
      </div>
    </Card>
  );
}

function Tag({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "success" | "warning" | "error" }) {
  const variants = {
    default: "bg-accent/15 text-accent border-border-accent",
    success: "bg-success-bg text-success border-success-border",
    warning: "bg-warning-bg text-warning border-warning-border",
    error: "bg-error-bg text-error border-error-border",
  };
  return <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono border", variants[variant])}>{children}</span>;
}

// ============= SECTIONS =============

function OverviewSection() {
  return (
    <Section title="VC Brain — Overview" subtitle="An AI-powered investment screening OS that sources, screens, and scores startup founders.">
      <Card className="p-6">
        <p className="text-sm text-text-secondary leading-relaxed mb-4">
          The VC Brain takes raw signals — GitHub commits, arXiv papers, Product Hunt launches, investor
          applications — and runs them through a pipeline of 6 specialized AI agents. Each agent handles
          one part of the screening process: ingesting data, validating claims, scoring the founder/market/idea
          independently, and synthesizing everything into an evidence-backed investment memo.
        </p>
        <div className="grid grid-cols-2 gap-3 mt-4">
          {[
            { icon: Sparkles, label: "Fin Agent", desc: "Conversational thesis builder" },
            { icon: Inbox, label: "Inbox", desc: "Founder card grid with scores" },
            { icon: FileText, label: "Investment Memo", desc: "Per-claim evidence + citations" },
            { icon: Radar, label: "Signal Radar", desc: "Live pipeline activity feed" },
            { icon: Network, label: "Network View", desc: "Founder ↔ channel graph" },
            { icon: Filter, label: "Funnel View", desc: "Sourcing → screening → decision" },
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <div key={i} className="flex items-center gap-3 p-3 rounded-md border border-border bg-card">
                <Icon className="w-4 h-4 text-accent shrink-0" />
                <div>
                  <div className="text-sm font-medium text-text-primary">{item.label}</div>
                  <div className="text-xs text-text-muted">{item.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Quick Start</h3>
        <ol className="space-y-2 text-sm text-text-secondary">
          <li>1. Open <Link href="/hero" className="text-accent underline">Fin Agent</Link> and type what you're looking for in plain English</li>
          <li>2. Fin Agent interviews you to fill any gaps, then runs the pipeline</li>
          <li>3. Review founders in the <Link href="/inbox" className="text-accent underline">Inbox</Link> — sorted by conviction</li>
          <li>4. Click any founder card to open the full <strong>investment memo</strong></li>
          <li>5. Hover evidence chips <Tag variant="success">[verified]</Tag> to see source provenance</li>
          <li>6. Watch the <Link href="/inbox" className="text-accent underline">Signal Radar</Link> for live pipeline activity</li>
        </ol>
      </Card>
    </Section>
  );
}

function FinAgentSection() {
  return (
    <Section title="Fin Agent" subtitle="Conversational sourcing agent — your primary entry point">
      <Step num={1} title="Open the Hero Screen">
        Navigate to <Link href="/hero" className="text-accent underline">/hero</Link> or click "Fin Agent" in the sidebar.
        You'll see a particle sphere with the greeting: <em>"Hey — I'm Fin Agent. Tell me what you're looking for."</em>
      </Step>
      <Step num={2} title="Type Your Thesis in Plain English">
        Type something like: <code className="text-xs bg-elevated px-1.5 py-0.5 rounded">"pre-seed AI infra founders in Berlin"</code>
        No forms, no dropdowns — just natural language.
      </Step>
      <Step num={3} title="Answer Follow-Up Questions">
        Fin Agent extracts your thesis fields and asks targeted follow-ups for anything missing:
        <ul className="mt-2 space-y-1 text-xs">
          <li>• "Any geographic focus, or fully remote-friendly?"</li>
          <li>• "Are you the type to bet on a strong founder with a shaky market?"</li>
        </ul>
      </Step>
      <Step num={4} title="Watch the Thesis Summary Card">
        The right panel updates in real time as Fin Agent fills in fields:
        <div className="mt-2 flex flex-wrap gap-2">
          <Tag variant="success">✓ Sectors: AI infra</Tag>
          <Tag variant="success">✓ Stage: pre-seed</Tag>
          <Tag variant="success">✓ Geography: DE</Tag>
          <Tag variant="warning">— Check Size: not yet discussed</Tag>
        </div>
      </Step>
      <Step num={5} title="Confirm and Execute">
        Once all fields are filled, Fin Agent shows the complete thesis and asks for confirmation.
        On "yes" or "looks right", the pipeline starts — Fin narrates progress conversationally.
      </Step>
      <Step num={6} title="Handoff to Dashboard">
        When the pipeline completes, a <Button size="sm">View results on Dashboard →</Button> button appears.
        Click it to land on the Inbox, pre-filtered to this run's results.
      </Step>
      <Card className="p-4 border-warning-border bg-warning-bg">
        <p className="text-sm text-warning">
          <strong>Constraint:</strong> Fin Agent never applies a thesis or starts the pipeline without explicit confirmation.
          The manual <Link href="/thesis" className="text-warning underline">Thesis Config</Link> form remains available as a fallback.
        </p>
      </Card>
    </Section>
  );
}

function InboxSection({ mockCard }: { mockCard: InboxCard }) {
  return (
    <Section title="Inbox & Founder Cards" subtitle="Your dashboard — sorted by conviction, scannable at a glance">
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-3">Anatomy of a Founder Card</h3>
        <p className="text-sm text-text-muted mb-4">Here's a real card with every field labeled:</p>
        <div className="max-w-md">
          <FounderCard card={mockCard} />
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-3">Field Reference</h3>
        <div className="space-y-2 text-sm">
          {[
            ["Company name + ❄", "Cold-start indicator (amber border + snowflake icon)"],
            ["Geography flag", "ISO-2 country code as flag emoji"],
            ["Sector badge", "Self-reported sector from application"],
            ["Founder axis", "0-100 score with 10-segment bar + trend arrow (▲▼●⊘)"],
            ["Market axis", "Categorical: bullish (green) / neutral (amber) / bear (red)"],
            ["Idea↔Mkt axis", "0-100 fit score between product and market"],
            ["Thesis Fit", "0-100 cosine similarity between founder and thesis sectors"],
            ["Conviction", "Geometric mean of all axes — never arithmetic average"],
            ["Evidence coverage", "verified_claims / total_claims ratio"],
            ["Recommendation pill", "fast_pass (green) / deep_dive (blue) / pass (gray) / reject (red)"],
          ].map(([field, desc], i) => (
            <div key={i} className="flex gap-3">
              <span className="text-text-primary font-medium w-40 shrink-0">{field}</span>
              <span className="text-text-muted">{desc}</span>
            </div>
          ))}
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-3">Compound Query Search</h3>
        <p className="text-sm text-text-secondary mb-3">
          The search bar at the top accepts <strong>natural language compound queries</strong> — not manual filter toggles.
          The backend decomposes your query into atomic attributes and runs a single SQL pass against all claims.
        </p>
        <div className="bg-elevated p-3 rounded-md text-xs text-text-muted font-mono">
          "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator"
        </div>
        <p className="text-xs text-text-muted mt-2">
          → Decomposed into 6 attributes → matched against claims → ranked by composite score
        </p>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-3">Filters</h3>
        <p className="text-sm text-text-secondary">
          Click the <Button size="sm" variant="outline">Filters</Button> button to filter by:
          sector, geography, recommendation, and cold-start status.
        </p>
      </Card>
    </Section>
  );
}

function MemoSection() {
  return (
    <Section title="Investment Memo & Evidence" subtitle="Every claim cited, every fact traceable">
      <Step num={1} title="Open the Memo">
        Click any founder card's <Button size="sm">Open Memo</Button> button to open the 3-column detail view.
      </Step>
      <Step num={2} title="Read the Memo">
        The center column shows the full investment memo with 14 sections:
        <div className="grid grid-cols-2 gap-1 mt-2 text-xs">
          {["Company Snapshot", "Investment Hypotheses", "SWOT", "Problem & Product", "Traction & KPIs", "Team & History", "Technology & Defensibility", "Market Sizing", "Competition", "Financials & Round", "Cap Table", "Due Diligence Log", "Exit Perspective", "Recommendation"].map((s) => (
            <div key={s} className="text-text-muted">• {s}</div>
          ))}
        </div>
      </Step>
      <Step num={3} title="Evidence Chips — Per-Claim Trust">
        <p className="mb-2">Every factual sentence in the memo has an inline citation chip. Here are the 6 states:</p>
        <div className="flex flex-wrap gap-2">
          <Tag variant="success">[verified]</Tag>
          <Tag variant="warning">[unverified]</Tag>
          <Tag variant="error">[contradicted]</Tag>
          <Tag>[missing]</Tag>
          <Tag variant="warning">[low evidence]</Tag>
          <Tag variant="warning">[cold-start]</Tag>
        </div>
      </Step>
      <Step num={4} title="Click a Chip to See Source">
        Clicking any evidence chip opens a right-side drawer with:
        <ul className="mt-2 space-y-1 text-xs">
          <li>• Full claim text</li>
          <li>• Source kind (GitHub, arXiv, deck, etc.) + ref (URL, slide number)</li>
          <li>• Validator status + confidence score</li>
          <li>• Counter-evidence (if contradicted)</li>
          <li>• Langfuse trace deep-link to the exact span that produced this claim</li>
        </ul>
      </Step>
      <Step num={5} title="Pipeline Trace Panel">
        The right rail shows the Langfuse trace tree for this pipeline run.
        Each node (ingestion, validator, founder, market, etc.) expands to show:
        model used, token count, latency, and status.
      </Step>
      <Step num={6} title="Score History Sparkline">
        Below the memo, a sparkline shows the founder's score history across all pipeline runs.
        Cold-start runs appear in amber; verified runs in accent blue.
      </Step>
    </Section>
  );
}

function RadarSection() {
  return (
    <Section title="Signal Radar" subtitle="Live pipeline activity feed — military-grade HUD">
      <Card className="p-4">
        <p className="text-sm text-text-secondary mb-4">
          The Signal Radar is a live, real-time activity feed at the top of the Inbox page.
          It shows pipeline events as they actually happen — not simulated.
        </p>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-warning" />
            <span className="text-sm text-text-secondary">Radar sweep: rotating champagne gold beam with blips mapped by source angle</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-success" />
            <span className="text-sm text-text-secondary">Active blips: saturated gold (#d4af37) — in-flight signals</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full" style={{ background: "#e8dcc0" }} />
            <span className="text-sm text-text-secondary">Resolved blips: pale gold-white (#e8dcc0) — completed pipeline runs</span>
          </div>
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Source Sectors (compass points)</h3>
        <div className="grid grid-cols-3 gap-2 text-xs">
          {[
            ["GITHUB", "top (12 o'clock)"],
            ["ARXIV", "upper right (2 o'clock)"],
            ["HN", "lower right (4 o'clock)"],
            ["PH", "bottom (6 o'clock)"],
            ["INBOUND", "lower left (8 o'clock)"],
            ["PIPELINE", "upper left (10 o'clock)"],
          ].map(([src, pos]) => (
            <div key={src} className="flex gap-2">
              <span className="font-mono text-warning">{src}</span>
              <span className="text-text-muted">{pos}</span>
            </div>
          ))}
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">HUD Activity Log</h3>
        <p className="text-sm text-text-secondary mb-2">The text log beside the radar shows the same events as readable lines:</p>
        <div className="bg-card rounded-md p-3 font-mono text-[10px] space-y-0.5">
          <div className="text-warning"><span className="text-text-subtle">[14:32:07]</span> GITHUB   new commit detected</div>
          <div className="text-warning"><span className="text-text-subtle">[14:32:11]</span> FOUNDER  scoring...</div>
          <div className="text-warning"><span className="text-text-subtle">[14:32:14]</span> MARKET   scoring...</div>
          <div style={{ color: "#e8dcc0" }}><span className="text-text-subtle">[14:32:21]</span> SCORED   82 Founder / 61 Market</div>
        </div>
        <p className="text-xs text-text-muted mt-2">Click any blip to navigate to that founder's memo.</p>
      </Card>
    </Section>
  );
}

function NetworkSection() {
  return (
    <Section title="Network View" subtitle="Founders ↔ sourcing channels ↔ institutions as a connected graph">
      <Card className="p-4">
        <p className="text-sm text-text-secondary mb-3">
          The Network page (<Link href="/network" className="text-accent underline">/network</Link>) renders a 2D React Flow canvas with three custom node types:
        </p>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded border border-accent" />
            <span className="text-sm text-text-primary"><strong>Founder Node</strong> — square, accent border (amber if cold-start)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full border border-success" />
            <span className="text-sm text-text-primary"><strong>Channel Node</strong> — circle, source-colored (GitHub=green, arXiv=blue, PH=amber, HN=amber)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 border border-text-muted" style={{ clipPath: "polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)" }} />
            <span className="text-sm text-text-primary"><strong>Institution Node</strong> — hexagon, neutral color</span>
          </div>
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Interactions</h3>
        <ul className="space-y-1 text-sm text-text-secondary">
          <li>• <strong>Click node</strong> → right sidebar opens with full details</li>
          <li>• <strong>Double-click founder</strong> → navigate to their memo page</li>
          <li>• <strong>Drag</strong> → reposition nodes</li>
          <li>• <strong>Scroll</strong> → zoom in/out</li>
          <li>• <strong>Background drag</strong> → pan the canvas</li>
        </ul>
      </Card>
    </Section>
  );
}

function FunnelSection() {
  return (
    <Section title="Funnel View" subtitle="Inbound + outbound tracks converging into screening stages">
      <Card className="p-4">
        <p className="text-sm text-text-secondary mb-3">
          The Funnel page (<Link href="/funnel" className="text-accent underline">/funnel</Link>) shows the full sourcing-to-decision pipeline:
        </p>
        <div className="space-y-2">
          {[
            ["Sourced", "Total inbound + outbound founders", "bg-accent"],
            ["Screened", "Pipeline completed", "bg-accent/80"],
            ["Diligence", "Recommendation: deep_dive", "bg-warning"],
            ["fast_pass", "Immediate $100K deployment", "bg-success-bg text-success"],
            ["pass", "Park in pipeline, revisit in 30 days", "bg-neutral-bg text-text-muted"],
            ["reject", "Pass — fatal weakness detected", "bg-error-bg text-error"],
          ].map(([stage, desc, color]) => (
            <div key={stage} className={cn("rounded-md p-3 text-sm", color)}>
              <span className="font-bold">{stage}</span>
              <span className="ml-3 opacity-80">{desc}</span>
            </div>
          ))}
        </div>
      </Card>
    </Section>
  );
}

function ThesisSection() {
  return (
    <Section title="Thesis Config" subtitle="Edit the active investment thesis — the source of truth">
      <Card className="p-4">
        <p className="text-sm text-text-secondary mb-3">
          The Thesis page (<Link href="/thesis" className="text-accent underline">/thesis</Link>) lets you edit the active investment thesis directly.
          This is the same config that Fin Agent writes into — it's always visible and editable.
        </p>
        <div className="space-y-2 text-sm">
          <div><strong className="text-text-primary">Name:</strong> Free text (e.g. "Maschmeyer Group — AI Infra & DevTools")</div>
          <div><strong className="text-text-primary">Sectors:</strong> Multi-select chips (AI infra, DevTools, Climate, Robotics, Fintech, Healthtech, EdTech)</div>
          <div><strong className="text-text-primary">Stage:</strong> Multi-select (pre-seed, seed, series-a)</div>
          <div><strong className="text-text-primary">Geography:</strong> ISO-2 country chips (DE, US, PK, SG, GB, FR, IN)</div>
          <div><strong className="text-text-primary">Check Size:</strong> USD amount (default: $100,000)</div>
          <div><strong className="text-text-primary">Ownership Target:</strong> Percentage (default: 7.5%)</div>
          <div><strong className="text-text-primary">Risk Appetite:</strong> Collapsible panel with 4 toggles + 2 numeric inputs</div>
        </div>
      </Card>
      <Card className="p-4 border-warning-border bg-warning-bg">
        <p className="text-sm text-warning">
          <strong>Re-score:</strong> Saving the thesis invalidates the cached results for all founders.
          A confirmation modal appears before saving: "Saving will re-evaluate all founders in the inbox. Continue?"
        </p>
      </Card>
    </Section>
  );
}

function ColdStartSection() {
  return (
    <Section title="The Cold-Start Rule" subtitle="The system's single most important differentiator">
      <Card className="p-4 border-warning-border">
        <p className="text-sm text-text-secondary mb-4">
          A cold-start founder has <strong>zero GitHub activity, zero arXiv papers, zero Product Hunt launches,
          zero accelerator membership, and zero prior VC backing</strong>. The old system would reject them
          with a falsely precise low score. The VC Brain doesn't.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-bold text-error mb-2">❌ False Precision</h4>
            <div className="h-2 bg-card rounded-full mb-1">
              <div className="h-full bg-error rounded-full" style={{ width: "35%" }} />
            </div>
            <p className="text-xs text-text-muted">Thin bar, score=35, "REJECT" — data is sparse, not bad</p>
          </div>
          <div>
            <h4 className="text-sm font-bold text-success mb-2">✅ Honest Wide Confidence</h4>
            <div className="h-3 bg-card rounded-full relative">
              <div className="absolute h-full rounded-full border border-success" style={{ left: "25%", width: "60%", background: "rgba(62,207,142,0.2)" }} />
            </div>
            <p className="text-xs text-text-muted mt-1">Wide band 25–85 (width: 60), "DEEP_DIVE" — scored from what IS inferable</p>
          </div>
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Enforced at 4 Levels</h3>
        <div className="space-y-2 text-sm">
          <div className="flex gap-2"><Tag variant="success">①</Tag> <span className="text-text-secondary"><strong>Schema:</strong> <code className="text-xs bg-elevated px-1 rounded">ClaimKind.COLD_START_INFERRED</code> enum value + <code className="text-xs bg-elevated px-1 rounded">cold_start: bool</code> field</span></div>
          <div className="flex gap-2"><Tag variant="success">②</Tag> <span className="text-text-secondary"><strong>Ingestion Agent R3:</strong> if no external source kinds, MUST emit at least one <code className="text-xs bg-elevated px-1 rounded">cold_start_inferred</code> claim</span></div>
          <div className="flex gap-2"><Tag variant="success">③</Tag> <span className="text-text-secondary"><strong>Founder Agent Rule:</strong> <code className="text-xs bg-elevated px-1 rounded">confidence_band</code> width ≥ 50, ALL 5 flags enumerated</span></div>
          <div className="flex gap-2"><Tag variant="success">④</Tag> <span className="text-text-secondary"><strong>Aggregator Downgrade:</strong> <code className="text-xs bg-elevated px-1 rounded">overall_recommendation ≠ "fast_pass"</code> — forced to <code className="text-xs bg-elevated px-1 rounded">deep_dive</code></span></div>
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Visual Indicators</h3>
        <div className="flex items-center gap-4">
          <div className="border border-warning rounded-lg p-3">
            <div className="flex items-center gap-1"><Snowflake className="w-3 h-3 text-warning" /><span className="text-xs text-warning">cold-start</span></div>
          </div>
          <span className="text-xs text-text-muted">Amber card border + ❄ icon + wide confidence band + "deep_dive" (never fast_pass)</span>
        </div>
      </Card>
    </Section>
  );
}

function TrustSection() {
  return (
    <Section title="Trust Scores" subtitle="Per-claim confidence — never a single trust number for the whole company">
      <Card className="p-4">
        <p className="text-sm text-text-secondary mb-4">
          The Validator Agent is the <strong>ONLY agent</strong> that writes <code className="text-xs bg-elevated px-1 rounded">claim.flags</code> and
          <code className="text-xs bg-elevated px-1 rounded">claim.confidence</code>. Every other agent reads flags but does not write them.
        </p>
        <div className="space-y-2">
          {[
            { status: "verified", color: "success", desc: "At least one external source confirms the claim. Confidence ≥ 0.8." },
            { status: "unverifiable", color: "warning", desc: "No external source confirms or contradicts. Confidence 0.3-0.5. Common for self-reported background claims." },
            { status: "contradicted", color: "error", desc: "At least one external source directly disputes the claim. Confidence ≤ 0.2. Counter-evidence cited." },
            { status: "not_disclosed", color: "default", desc: "The claim is missing entirely (founder didn't provide team info, cap table, etc.). Confidence = 0.0." },
          ].map((s) => (
            <div key={s.status} className="flex items-start gap-3 p-2 rounded-md border border-border">
              <Tag variant={s.color as any}>[{s.status}]</Tag>
              <span className="text-sm text-text-secondary">{s.desc}</span>
            </div>
          ))}
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Key Rules</h3>
        <ul className="space-y-1 text-sm text-text-secondary">
          <li>• Self-reported claims (deck, application_form, founder_bio) can <strong>NEVER</strong> be "verified" without external corroboration</li>
          <li>• Cross-claim contradictions: if two claims of the same kind assert mutually exclusive values (e.g. $5B vs $500M market size), BOTH are flagged "contradicted"</li>
          <li>• Cold-start inferred claims are always "unverifiable" with confidence 0.4</li>
          <li>• Evidence coverage = verified_count / total_claims. If {"< 0.4"}, recommendation is downgraded by one tier</li>
        </ul>
      </Card>
    </Section>
  );
}

function PipelineSection() {
  return (
    <Section title="Pipeline Architecture" subtitle="8 LangGraph nodes — how data flows through the system">
      <Card className="p-4">
        <div className="font-mono text-xs text-text-muted bg-card rounded-md p-4 leading-relaxed">
          <div className="text-accent">ingestion</div>
          <div className="text-text-subtle">  ↓ ↓ (parallel fan-out)</div>
          <div className="text-accent">  fetch_external_evidence  ←→  thesis_fit</div>
          <div className="text-text-subtle">  ↓</div>
          <div className="text-success">  validator</div>
          <div className="text-text-subtle">  ↓ ↓ (parallel fan-out)</div>
          <div className="text-accent">  founder  ←→  market</div>
          <div className="text-text-subtle">       ↓</div>
          <div className="text-accent">       idea_vs_market</div>
          <div className="text-text-subtle">  ↓ ↓ ↓ (fan-in)</div>
          <div className="text-warning">  aggregator (TOOL-LESS)</div>
          <div className="text-text-subtle">  ↓</div>
          <div className="text-text-primary">  AggregatorOutput + memo_markdown</div>
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Agent Roles</h3>
        <div className="space-y-2 text-sm">
          {[
            ["Ingestion Agent", "Transforms raw signals into atomic Claim records. Enforces R1-R5 rules. Emits cold_start_inferred claim when no external signals exist."],
            ["Fetch External Evidence", "Gathers external evidence for each claim (same-kind claims, Crunchbase mock). Runs in parallel with thesis_fit."],
            ["Thesis Fit", "Computes Sentence-BERT cosine similarity between founder claims and thesis sectors. Outputs thesis_fit_score (0-100) and market_fit_similarity (0-1)."],
            ["Validator Agent", "The ONLY agent that writes claim.flags and claim.confidence. Cross-checks each claim against external evidence. 4 status values + cross-claim contradiction detection."],
            ["Founder Agent", "Scores the founder across 4 axes: technical, market_fit, network, momentum. Enforces cold-start rule: wide confidence band, all 5 flags, never fast_pass."],
            ["Market Agent", "Categorical verdict: bullish / neutral / bear. NEVER a numeric average. Bullish requires ≥2 verified growth claims. Bear requires ≥1 verified contraction."],
            ["Idea-vs-Market Agent", "Scores FIT (how well product serves market) and DEFENSIBILITY (technical moat, IP, switching costs). Runs after Market Agent (reads its reasoning)."],
            ["Aggregator", "TOOL-LESS synthesizer. Receives only pre-verified structured facts. No tool access, no URLs, no raw_inputs. Produces the final memo with [^claim_id] citations."],
          ].map(([role, desc], i) => (
            <div key={i} className="border border-border rounded-md p-3">
              <div className="font-bold text-text-primary text-sm">{role}</div>
              <div className="text-text-muted text-xs mt-1">{desc}</div>
            </div>
          ))}
        </div>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-bold text-text-primary mb-2">Re-Scoring Triggers</h3>
        <p className="text-sm text-text-secondary mb-2">The pipeline re-runs when any of these fire (60-min cache TTL):</p>
        <div className="space-y-1 text-sm">
          <div className="flex gap-2"><Tag variant="success">①</Tag> <span className="text-text-secondary">New application received from this founder</span></div>
          <div className="flex gap-2"><Tag variant="success">②</Tag> <span className="text-text-secondary">External signal with conviction_delta &gt; 5 detected by outbound scan</span></div>
          <div className="flex gap-2"><Tag variant="success">③</Tag> <span className="text-text-secondary">No prior score exists (first time we see them)</span></div>
          <div className="flex gap-2"><Tag variant="success">④</Tag> <span className="text-text-secondary">Last score older than 24 hours (stale-cache sweep)</span></div>
        </div>
      </Card>
    </Section>
  );
}
