# VC Brain — Frontend Build Specification

> Handoff target: autonomous coding agent. Every decision below is resolved — no placeholders, no "choose one of the following." If a coding agent encounters ambiguity, treat it as a bug in this spec, not an invitation to ask the human.

---

## 1. Tech Stack Decision Log

| Layer | Final choice | One-sentence justification |
|---|---|---|
| Framework | **Next.js 16 (App Router) + React 19** | App Router gives file-based routing + RSC for the memo view's heavy static content; React 19 is required by the shadcn dashboard template (no forwardRef boilerplate, `data-slot` attributes). |
| Styling | **Tailwind CSS v4** (`@theme` directive, CSS-first config) | Tailwind v4 ships the Oxide engine (sub-100ms HMR), native CSS variables via `@theme`, and is what shadcn/ui v3 targets. |
| Component library | **shadcn/ui v3 + Radix UI primitives** | Copy-into-repo model gives full source control; Radix handles accessibility (focus traps, ARIA) for Sheet/Modal/Tooltip. |
| Base template | **shadcn-dashboard-landing-template** (`github.com/shadcnstore/shadcn-dashboard-landing-template`) | Ships 30+ admin pages, Recharts, TanStack Table, live theme customizer — adapts to our dark canvas with token swaps, not rebuilds. |
| AI-specific UI | **AI Elements** (`elements.ai-sdk.dev`) | Purpose-built `ChainOfThought`, `Reasoning`, `Sources`, `InlineCitation` blocks map 1:1 onto our Trust Score chip + Agentic Traceability requirements. |
| Charts | **Recharts** (bundled in template) | Composable, declarative, dark-mode friendly; sufficient for sparklines + score-history bars. |
| Tables | **TanStack Table v8** (bundled in template) | Headless, supports column resizing + sorting + filtering at the scale the inbox needs (≤500 founders). |
| Network visualization | **React Flow** (`@xyflow/react`, v12+) | 2D HTML/SVG/CSS rendering, handles 500 nodes natively, built-in dark theme, custom React node components — no WebGL. |
| Icons | **lucide-react** | Consistent stroke width, tree-shakeable, already a shadcn dependency. |
| Fonts | **Geist Sans** (via `next/font/google` or `geist` package) | Variable font, optimized for data-density, matches Vercel/Linear aesthetic. Fallback: SF Pro Display (system). |

---

## 2. Repository Structure

```
vc-brain-frontend/
├── package.json
├── next.config.ts
├── tsconfig.json
├── postcss.config.mjs
├── tailwind.config.ts              # imports tokens from app/globals.css @theme
├── .env.example
├── .eslintrc.json
├── public/
│   ├── fonts/                      # Geist Sans self-hosted (optional)
│   └── og-image.png
├── app/
│   ├── globals.css                 # Tailwind v4 @theme directive — design tokens
│   ├── layout.tsx                  # RootLayout: <html> + <body> + font + ThemeProvider
│   ├── page.tsx                    # Redirect → /inbox
│   ├── inbox/
│   │   └── page.tsx                # Dashboard: founder card grid
│   ├── founders/
│   │   └── [founderId]/
│   │       └── page.tsx            # Founder Detail: memo + trace + score history
│   ├── thesis/
│   │   └── page.tsx                # Thesis Engine config panel
│   ├── network/
│   │   └── page.tsx                # React Flow relationship view
│   ├── funnel/
│   │   └── page.tsx                # Inbound/outbound funnel view
│   └── api/                        # (none — all API calls go to backend at :8000)
├── components/
│   ├── ui/                         # shadcn primitives (Button, Card, Sheet, etc.)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── sheet.tsx
│   │   ├── modal.tsx
│   │   ├── tooltip.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── textarea.tsx
│   │   ├── progress.tsx
│   │   ├── separator.tsx
│   │   └── tabs.tsx
│   ├── ai/                         # AI Elements adaptations
│   │   ├── inline-citation.tsx     # Trust Score chip — wraps AI Elements InlineCitation
│   │   ├── reasoning.tsx           # Collapsible reasoning block for agent outputs
│   │   ├── sources.tsx             # Source list with provenance
│   │   └── chain-of-thought.tsx    # Pipeline trace tree
│   ├── layout/
│   │   ├── app-shell.tsx           # Sidebar + top nav + main content
│   │   ├── sidebar.tsx             # Primary nav (Inbox/Thesis/Network/Funnel)
│   │   ├── topbar.tsx              # Breadcrumb + search + thesis indicator
│   │   └── glass-bar.tsx           # Glassmorphic nav bar (backdrop-blur)
│   ├── founder/
│   │   ├── founder-card.tsx        # Compact card for inbox grid
│   │   ├── founder-table.tsx       # TanStack Table view (toggle from grid)
│   │   ├── axis-score.tsx          # Single axis: label + arrow + score + bar
│   │   ├── cold-start-banner.tsx   # RED-bordered cold-start callout
│   │   ├── confidence-band.tsx     # Wide-band visual for cold-start
│   │   ├── score-history-sparkline.tsx
│   │   └── recommendation-pill.tsx
│   ├── memo/
│   │   ├── memo-view.tsx           # Renders memo_markdown with [^claim_id] substitution
│   │   ├── evidence-chip.tsx       # Inline citation chip (4 states)
│   │   ├── evidence-drawer.tsx     # Right-side Sheet with full claim detail
│   │   ├── section-callout.tsx     # "(not disclosed — request from founder)" callout
│   │   ├── swot-grid.tsx           # 4-quadrant SWOT layout
│   │   ├── due-diligence-log.tsx   # Markdown table of all claims + statuses
│   │   └── missing-sections-card.tsx
│   ├── trace/
│   │   ├── pipeline-trace.tsx      # Right-rail trace panel
│   │   ├── trace-node.tsx          # Single span: model + latency + tokens
│   │   └── trace-tree.tsx          # Collapsible nested spans
│   ├── thesis/
│   │   ├── thesis-editor.tsx       # Full form
│   │   ├── sector-multi-select.tsx # Chip-based multi-select
│   │   ├── geography-chips.tsx     # ISO-2 country chips
│   │   ├── risk-appetite-panel.tsx # Collapsible subsection
│   │   └── rescore-confirm-modal.tsx
│   ├── network/
│   │   ├── network-canvas.tsx      # React Flow wrapper
│   │   ├── founder-node.tsx        # Custom React Flow node
│   │   ├── channel-node.tsx        # Custom React Flow node (github/arxiv/ph/hn)
│   │   ├── institution-node.tsx    # Custom React Flow node (accelerator/VC)
│   │   ├── node-detail-sidebar.tsx # Right sidebar on node click
│   │   └── edge-legend.tsx
│   ├── funnel/
│   │   ├── funnel-view.tsx         # Sankey-style funnel
│   │   ├── funnel-stage.tsx        # Single stage (sourced/screened/diligence/decision)
│   │   └── funnel-tooltip.tsx
│   └── shared/
│       ├── loading-skeleton.tsx
│       ├── error-boundary.tsx
│       ├── empty-state.tsx
│       └── metric-card.tsx
├── lib/
│   ├── api.ts                      # Typed fetch client + TanStack Query hooks
│   ├── types.ts                    # TypeScript interfaces mirroring backend schemas
│   ├── utils.ts                    # cn(), formatPct(), formatUsd(), timeAgo(), countryFlag()
│   ├── constants.ts                # Sector lists, geographies, recommendation colors
│   └── hooks/
│       ├── use-inbox.ts            # useQuery hook for /applications/inbox
│       ├── use-founder-memo.ts     # useQuery hook for /founders/{id}/memo
│       ├── use-thesis.ts           # useQuery + useMutation for /thesis
│       ├── use-outbound.ts         # useQuery for /outbound/queue
│       ├── use-query-search.ts     # useQuery for /query (compound search)
│       └── use-trace.ts            # useQuery for /traces/{run_id}
├── config/
│   ├── site.ts                     # Site metadata, nav items
│   └── theme.ts                    # Theme tokens (mirror of globals.css @theme)
└── tests/
    ├── e2e/                         # Playwright specs (optional)
    └── unit/                        # Vitest specs for utils
```

---

## 3. Design Tokens File

### `app/globals.css` (Tailwind v4 `@theme` directive)

```css
@import "tailwindcss";

@theme {
  /* ============================================================
     COLOR SYSTEM — exact values per spec, do not invent new ones
     ============================================================ */

  /* Canvas surfaces — luminance stepping for depth, NOT drop shadows */
  --color-canvas-base: #0b0f19;       /* page background — NOT pure black */
  --color-card: #14151a;              /* cards, table rows */
  --color-modal: #1e1e22;             /* modals, dropdowns, tooltips */
  --color-elevated: #25252b;          /* hover states, active rows */

  /* Single chromatic accent — primary actions, focus, selections ONLY */
  --color-accent: #5e6ad2;            /* lavender-blue */
  --color-accent-hover: #6e7ad8;
  --color-accent-muted: #3e4ab0;

  /* Functional colors — desaturated, Sentry-style restraint */
  --color-success: #3ecf8e;           /* verified — desaturated emerald */
  --color-success-bg: rgba(62, 207, 142, 0.08);
  --color-success-border: rgba(62, 207, 142, 0.25);

  --color-warning: #d4a843;           /* unverifiable — desaturated amber */
  --color-warning-bg: rgba(212, 168, 67, 0.08);
  --color-warning-border: rgba(212, 168, 67, 0.25);

  --color-error: #d44a5c;             /* contradicted — desaturated crimson */
  --color-error-bg: rgba(212, 74, 92, 0.08);
  --color-error-border: rgba(212, 74, 92, 0.25);

  --color-neutral: #6b7280;           /* not_disclosed — neutral gray */
  --color-neutral-bg: rgba(107, 114, 128, 0.08);
  --color-neutral-border: rgba(107, 114, 128, 0.25);

  --color-cold-start: #d4a843;        /* cold-start band — amber (warning family) */
  --color-cold-start-bg: rgba(212, 168, 67, 0.06);

  /* Text — NOT pure white, reduces eye strain (WCAG 4.5:1 target) */
  --color-text-primary: #f7f8f8;
  --color-text-secondary: #e6e6e6;
  --color-text-muted: #9ca3af;
  --color-text-subtle: #6b7280;

  /* Borders + dividers */
  --color-border: rgba(255, 255, 255, 0.06);
  --color-border-strong: rgba(255, 255, 255, 0.12);
  --color-border-accent: rgba(94, 106, 210, 0.4);

  /* ============================================================
     TYPOGRAPHY — Geist Sans, restricted weights
     ============================================================ */
  --font-sans: "Geist Sans", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "Geist Mono", "SF Mono", "JetBrains Mono", ui-monospace, monospace;

  /* Type scale — 8 steps */
  --text-xs: 11px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 15px;
  --text-lg: 17px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 32px;

  /* Letter-spacing */
  --tracking-tight: -0.04em;   /* headlines 24px+ */
  --tracking-snug: -0.02em;    /* subheads 17-20px */
  --tracking-normal: 0em;      /* body 13-15px */
  --tracking-data: 0.02em;     /* data values, table cells */

  /* Weights — Medium + Bold only, NO light */
  --weight-medium: 500;
  --weight-bold: 700;

  /* ============================================================
     SPACING + RADIUS
     ============================================================ */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
}

@layer base {
  * {
    border-color: var(--color-border);
  }
  html {
    color-scheme: dark;
  }
  body {
    background-color: var(--color-canvas-base);
    color: var(--color-text-primary);
    font-family: var(--font-sans);
    font-size: var(--text-base);
    font-weight: var(--weight-medium);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  /* Headlines: tight letter-spacing */
  h1, h2, h3, h4, h5, h6 {
    letter-spacing: var(--tracking-tight);
    font-weight: var(--weight-bold);
  }
  /* Data values: slightly positive letter-spacing */
  .font-mono, [data-numeric] {
    letter-spacing: var(--tracking-data);
    font-variant-numeric: tabular-nums;
  }
}

@layer utilities {
  /* Glassmorphism — ONLY for nav, dropdowns, tooltips — never primary cards */
  .glass {
    background-color: rgba(20, 21, 26, 0.8);
    backdrop-filter: blur(12px) saturate(180%);
    -webkit-backdrop-filter: blur(12px) saturate(180%);
    border: 1px solid var(--color-border);
  }
  /* Scrollbar — dark, subtle */
  ::-webkit-scrollbar { width: 8px; height: 8px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb {
    background: var(--color-border-strong);
    border-radius: 4px;
  }
  ::-webkit-scrollbar-thumb:hover { background: var(--color-text-subtle); }
}
```

### `tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: "var(--color-canvas-base)",
        card: "var(--color-card)",
        modal: "var(--color-modal)",
        elevated: "var(--color-elevated)",
        accent: {
          DEFAULT: "var(--color-accent)",
          hover: "var(--color-accent-hover)",
          muted: "var(--color-accent-muted)",
        },
        success: "var(--color-success)",
        warning: "var(--color-warning)",
        error: "var(--color-error)",
        neutral: "var(--color-neutral)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## 4. Page List with Component Breakdown

### 4.1 Dashboard / Inbox (`/inbox`)

**Purpose**: Scannable grid of founder cards, sorted by conviction. Compound query search + filters.

**Data source**: `GET /api/applications/inbox` → `InboxResponse`

```typescript
// lib/types.ts
interface InboxCard {
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
```

**Components used**:
- `AppShell` (layout) — sidebar + topbar + main
- `GlassBar` (topbar) — glassmorphic nav with search
- `FounderCard` — compact card (see §4.1.1)
- `AxisScore` — single axis row (label + arrow + score + 10-segment bar)
- `RecommendationPill` — colored pill
- `ConfidenceBand` — wide-band visual for cold-start
- `Input` (shadcn) — search box
- `Button` (shadcn) — filter toggle
- `Badge` (shadcn) — active filter chips
- `DropdownMenu` (shadcn) — filter dropdowns
- `LoadingSkeleton` (shared) — card placeholders
- `EmptyState` (shared) — "no applications yet"

**Mapping to base template**: replaces the dashboard landing page's stat cards with `FounderCard` grid; reuses the template's sidebar + topbar shell.

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ [GlassBar: search + filters]                                 │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ FounderCard │ │ FounderCard │ │ FounderCard │            │
│ │             │ │             │ │             │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ FounderCard │ │ FounderCard │ │ FounderCard │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

#### 4.1.1 FounderCard component

**Props**: `{ card: InboxCard; sourcingChannel?: string }`

**Visual structure** (matches spec §9.1 field list):
```
┌─────────────────────────────────────────────────────────────┐
│ Acme AI            🇩🇪 DE  [AI infra]  [github]    2h ago   │
│ ─────────────────────────────────────────────────────────── │
│ Founder    ▲ 72  [▰▰▰▰▰▰▰▱▱▱]  ❄ cold-start  trend: improving│
│ Market     ● 65  [▰▰▰▰▰▰▰▱▱▱]  neutral                     │
│ Idea↔Mkt   ▲ 80  [▰▰▰▰▰▰▰▰▰▱]                              │
│ Thesis Fit     74  [▰▰▰▰▰▰▰▰▱▱]                            │
│ ─────────────────────────────────────────────────────────── │
│ Conviction 70/100   evidence 0.62   contradictions: 1       │
│ ▸ deep_dive                                                 │
│ [Open Memo]  [Pass]  [Fast-Track]                           │
└─────────────────────────────────────────────────────────────┘
```

**Cold-start visual treatment** (when `card.cold_start === true`):
- 1px amber border (`border-success`/`warning` at 40% opacity — see §5)
- ❄ `Snowflake` icon (lucide) next to company name, amber color
- Confidence band widens visually (see §5)
- No change to score bar — score is still shown, but the band communicates uncertainty

**Non-cold-start**:
- Default 1px `border-border` (subtle white at 6% opacity)
- No ❄ icon

#### 4.1.2 AxisScore component

**Props**: `{ label: string; score: number | null; trend: string; barColor?: string; rightSlot?: ReactNode }`

**Visual**:
- Label (left, `text-text-muted`, width 80px)
- Trend arrow: ▲ improving (success), ▼ declining (error), ● stable (text-muted), ⊘ insufficient (text-subtle)
- Score (font-mono, tabular-nums, width 32px right-aligned)
- 10-segment progress bar (8px × 12px segments, 2px gap)
- Optional right slot (cold-start flag, trend text, market verdict label)

---

### 4.2 Founder Detail / Memo (`/founders/[founderId]`)

**Purpose**: Full investment memo with per-claim Trust Score chips, evidence drawer, pipeline trace, score history.

**Data source**: `GET /api/founders/{id}/memo` → `FounderMemo`

```typescript
interface FounderMemo {
  founder_id: string;
  founder_name: string;
  company_name: string | null;
  aggregator_output: {
    id: string;
    overall_recommendation: "fast_pass" | "deep_dive" | "pass" | "reject";
    overall_conviction: number;
    axes: { founder: number; market: number; idea_vs_market: number };
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

interface ClaimRow {
  id: string;
  kind: string;
  text: string;
  source: {
    kind: "deck" | "application_form" | "github" | "arxiv" | "hackernews" | "producthunt" | "accelerator_cohort" | "company_website" | "founder_bio" | "external_db" | "interview";
    ref: string;
    raw_payload_hash: string;
    retrieved_by: string;
    ingested_at: string;
  };
  confidence: number;
  flags: Array<{
    flag: "verified" | "unverifiable" | "contradicted" | "not_disclosed" | "low_evidence" | "cold_start_inferred";
    set_by: string;
    set_at: string;
    reason: string;
    counter_evidence_ref: string | null;
  }>;
  validator_status: string | null;
  superseded_by: string | null;
  created_at: string;
}
```

**Layout**: 3-column
```
┌──────────┬─────────────────────────────┬──────────────┐
│ Left     │ Center (memo)               │ Right        │
│ rail     │                             │ rail         │
│          │                             │              │
│ Section  │ ┌─── Cold-start banner ──┐ │ Pipeline     │
│ nav      │ │ ⚠️ Cold-start founder.  │ │ Trace        │
│ (anchor  │ │ ...                    │ │ (collapsible)│
│ links)   │ └────────────────────────┘ │              │
│          │                             │ Next Actions │
│ - Company│ # Investment Memo: Acme    │              │
│ - Hypoth │ ## Company Snapshot        │ Metadata:    │
│ - SWOT   │ - Claim text [verified]    │   trace_id   │
│ - ...    │ - Claim text [unverified]  │   computed_at│
│          │                             │   evidence   │
│          │ ## SWOT                    │              │
│          │ **Strengths:** ...         │              │
│          │                             │              │
│          │ ## Due Diligence Log       │              │
│          │ | Claim | Status | ... |   │              │
│          │                             │              │
│          │ ## Recommendation          │              │
│          │ - Overall: deep_dive       │              │
│          │ - Conviction: 72/100       │              │
│          │                             │              │
│          │ ┌─ Score History ────────┐ │              │
│          │ │ ▆ ▇ █ ▅ ▇ (sparkline)  │ │              │
│          │ └────────────────────────┘ │              │
└──────────┴─────────────────────────────┴──────────────┘
```

**Components used**:
- `AppShell` (layout)
- `MemoView` — renders `memo_markdown` with `[^claim_id]` → `EvidenceChip` substitution
- `EvidenceChip` (see §6) — inline Trust Score chip
- `EvidenceDrawer` — right-side `Sheet` (shadcn) with full claim detail
- `ColdStartBanner` — RED-bordered callout (see §5)
- `SectionCallout` — `"(not disclosed — request from founder)"` for missing optional sections
- `SwotGrid` — 2×2 grid for SWOT section
- `DueDiligenceLog` — TanStack Table rendering all claims + Validator statuses
- `MissingSectionsCard` — red border for required, neutral for optional
- `ScoreHistorySparkline` — Recharts sparkline of `score_history`
- `PipelineTrace` — right-rail trace panel (see §4.2.1)
- `TraceNode` — single span row
- `TraceTree` — collapsible nested spans
- `RecommendationPill`
- `Button` (shadcn) — "Back to inbox"
- `Separator` (shadcn)
- `Tooltip` (shadcn) — hover hints on chips

**Mapping to AI Elements**:
- `EvidenceChip` wraps AI Elements' `InlineCitation` — adds our 4-state color system
- `PipelineTrace` adapts AI Elements' `ChainOfThought` — renders Langfuse spans as collapsible reasoning steps
- `EvidenceDrawer` adapts AI Elements' `Sources` — shows full source provenance

#### 4.2.1 PipelineTrace component

**Props**: `{ traceId: string | null }`

**Data source**: `GET /api/traces/{run_id}` → `TraceResponse`

**Visual**:
- Collapsible header: "Pipeline Trace" + chevron
- Flat list of `TraceNode` rows:
  - Span name (font-mono)
  - Model badge (e.g. `gpt-5.6-sol`)
  - Latency (e.g. `2.34s`)
  - Status dot (success=green, error=red)
- Click a node → expand to show: `input_tokens`, `output_tokens`, `start_time`, `level`
- Footer: full `trace_id` (font-mono, truncate)

**States**:
- Loading: spinner + "Loading trace…"
- Unconfigured: "Langfuse not configured" message
- Empty: "No spans returned"
- Error: red error message

---

### 4.3 Thesis Config (`/thesis`)

**Purpose**: Edit the active investment thesis. Confirmation modal before save (re-scores inbox).

**Data source**: `GET /api/thesis` → `Thesis`, `POST /api/thesis` → `Thesis`

```typescript
interface Thesis {
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
```

**Components used**:
- `AppShell` (layout)
- `ThesisEditor` — full form wrapper
- `Input` (shadcn) — name, check_size_usd, ownership_target_pct
- `SectorMultiSelect` — chip-based multi-select (7 sectors)
- `GeographyChips` — ISO-2 country chips (7 geographies)
- `RiskAppetitePanel` — collapsible `<details>` with 4 toggles + 2 numeric inputs
- `RescoreConfirmModal` — `Modal` (shadcn) with confirmation text
- `Button` (shadcn) — Save, Reset
- `Badge` (shadcn) — active status, thesis ID
- `Tabs` (shadcn) — optional: tabs for "Thesis" / "Risk Appetite" / "Preview"

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Investment Thesis                          [active] id: ab12 │
│ The active thesis drives all scoring.                       │
├─────────────────────────────────────────────────────────────┤
│ Name:     [Maschmeyer Group — AI Infra & DevTools         ] │
│                                                             │
│ Sectors:  [AI infra] [DevTools] [Climate] [Robotics]  +    │
│                                                             │
│ Stage:    [pre-seed] [seed]  +                             │
│                                                             │
│ Geography:[DE] [US] [PK] [SG]  +                           │
│                                                             │
│ Check Size (USD):     [100000      ]                       │
│ Ownership Target (%): [7.5         ]                       │
│                                                             │
│ ▼ Risk Appetite                                             │
│   Max founder age:    [3           ] years                 │
│   Min conviction:     [60          ]                       │
│   ☑ Accepts no prior funding                                │
│   ☑ Accepts no GitHub                                       │
│   ☑ Accepts cold-start                                      │
│   ☑ Allow neutral market                                    │
│                                                             │
│                              [Reset]  [Save & Re-evaluate]  │
└─────────────────────────────────────────────────────────────┘
```

**Confirmation modal text** (exact):
```
Re-evaluate inbox?

Saving will re-evaluate all founders in the inbox. The re-score
triggers will fire on the next card view for each founder (cached
outputs are now stale relative to the updated thesis). This may
incur LLM costs for each re-scored founder.

Continue?
[Cancel]  [Save & Re-evaluate]
```

---

### 4.4 Network / Relationship View (`/network`)

**Purpose**: Visualize founders ↔ sourcing channels ↔ institutions as a connected graph.

**Data source**: `GET /api/outbound/queue` + `GET /api/applications/inbox` — combine to build edges.

**Components used**:
- `AppShell` (layout)
- `NetworkCanvas` — React Flow wrapper (see §7)
- `FounderNode` — custom React Flow node (square, accent border)
- `ChannelNode` — custom React Flow node (circle, channel-colored)
- `InstitutionNode` — custom React Flow node (hexagon, neutral)
- `NodeDetailSidebar` — right sidebar on node click
- `EdgeLegend` — bottom-left legend
- `Button` (shadcn) — "Reset zoom", "Fit view"
- `Tooltip` (shadcn) — hover on node shows quick stats

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Network View                          [Reset] [Fit View]    │
├──────────────────────────────────────────┬──────────────────┤
│                                          │ Node Detail      │
│         ◯ github                         │ ─────────────    │
│          │                               │ Name: Bob Smith  │
│          │                               │ Type: founder    │
│      ┌───┴───┐                           │ Conviction: 72   │
│      │ Bob S │──────┐                    │ Recommendation:  │
│      └───────┘      │                    │   deep_dive      │
│          │          │                    │                  │
│          │          │                    │ Edges:           │
│      ◯ arxiv        ◯ YC W24             │ - github         │
│                                          │ - arxiv          │
│                                          │ - YC W24         │
├──────────────────────────────────────────┴──────────────────┤
│ Legend: ◯ Channel  ▭ Founder  ⬡ Institution                │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.5 Outbound Funnel View (`/funnel`)

**Purpose**: Show inbound + outbound tracks converging into one screening funnel.

**Data source**: `GET /api/applications` (inbound) + `GET /api/outbound/queue` (outbound) + `GET /api/applications/inbox` (stages).

**Components used**:
- `AppShell` (layout)
- `FunnelView` — Sankey-style funnel (Recharts Sankey or custom SVG)
- `FunnelStage` — single stage box with count + label
- `FunnelTooltip` — hover tooltip with stage breakdown
- `MetricCard` (shared) — top-level metrics (total inbound, total outbound, conversion rate)
- `Tabs` (shadcn) — toggle between "Funnel" and "Table" view

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Inbound: 24  |  Outbound: 12  |  Conversion: 18%            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Inbound ─────┐                          ┌── fast_pass (2)  │
│   (24)        │                          │                  │
│               ├──► Sourced (36) ──► Screened (28) ──► ...   │
│  Outbound ────┘                          │                  │
│   (12)        │                          ├── deep_dive (8)  │
│               │                          │                  │
│               │                          ├── pass (12)      │
│               │                          │                  │
│               │                          └── reject (6)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Stages**:
1. **Sourced** — total inbound + outbound
2. **Screened** — applications with `aggregator_output_id` set
3. **Diligence** — `recommendation == "deep_dive"`
4. **Decision** — split into `fast_pass` / `pass` / `reject`

---

## 5. Cold-Start Visual State Spec

The cold-start state is the single most important visual differentiator. It must be designed as a first-class state, not an edge case.

### 5.1 When it triggers

`card.cold_start === true` (from `FounderScoreSnapshot.cold_start` on the latest snapshot).

### 5.2 Visual differences from a normal scored founder

| Element | Normal | Cold-start |
|---|---|---|
| **Card border** | 1px `border-border` (white at 6%) | 1px `border-warning` at 40% opacity (amber) |
| **Icon** | None | ❄ `Snowflake` (lucide), amber, 14px, next to company name |
| **Score bar** | Standard 10-segment, filled to score | Same — score is still shown (not hidden) |
| **Confidence band** | Not shown (narrow band implied) | **Explicit wide band shown** — see §5.3 |
| **Trend arrow** | ▲▼●⊘ | ⊘ `insufficient_data` always (gray) |
| **Flags row** | None | Inline chips: `no_github` `no_arxiv` `no_ph_launch` `no_accelerator` `no_prior_vc` (amber, 10px font) |
| **Recommendation pill** | Any | NEVER `fast_pass` — always `deep_dive` or lower |
| **Banner in memo** | None | RED-bordered banner at top of memo (see §5.4) |

### 5.3 ConfidenceBand component

**Props**: `{ low: number; high: number; coldStart: boolean }`

**Visual**:
- A horizontal bar showing the range `[low, high]` on a 0-100 scale
- Normal (narrow band, `!coldStart`): thin 4px bar, accent color, no label
- Cold-start (wide band, `coldStart === true`):
  - 12px tall bar (visually wider/heavier than normal)
  - Amber gradient from `low` to `high`
  - Explicit text label below: `Confidence band: 25–85 (width: 60) — wide due to cold-start`
  - Tooltip on hover: "External signals absent. Band widened to reflect unverified self-reported claims."

```tsx
// components/founder/confidence-band.tsx
export function ConfidenceBand({ low, high, coldStart }: ConfidenceBandProps) {
  const width = high - low;
  if (!coldStart) {
    // Normal: thin bar, no label
    return (
      <div className="h-1 w-full bg-neutral-bg rounded-full">
        <div
          className="h-full bg-accent rounded-full"
          style={{ marginLeft: `${low}%`, width: `${width}%` }}
        />
      </div>
    );
  }
  // Cold-start: wide bar + explicit label
  return (
    <div className="space-y-1">
      <div className="h-3 w-full bg-neutral-bg rounded-full relative">
        <div
          className="h-full rounded-full bg-gradient-to-r from-warning/40 to-warning/80 border border-warning/60"
          style={{ marginLeft: `${low}%`, width: `${width}%` }}
        />
      </div>
      <p className="text-xs text-warning font-medium">
        Confidence band: {low}–{high} (width: {width}) — wide due to cold-start
      </p>
    </div>
  );
}
```

### 5.4 Cold-start banner (in memo)

**Exact text** (per spec §4.6):
```
⚠️ Cold-start founder. External signals absent. All scores carry wide confidence bands. Recommend deep_dive, not fast_pass, regardless of headline numbers.
```

**Visual**:
- 2px RED border (`border-error` — desaturated crimson, NOT amber)
- Background: `bg-error-bg` (crimson at 8% opacity)
- Padding: 16px
- Margin-bottom: 24px (before memo content)
- Font: 14px, `text-text-secondary`
- Icon: ⚠️ emoji or `AlertTriangle` (lucide) in crimson

**Rationale for RED not amber**: spec §9.2 explicitly says "red-bordered banner". The card border is amber (§9.1), but the memo banner is red — this is intentional to signal different severity levels.

---

## 6. Trust Score Chip Component Spec

### 6.1 Four visual states

| Status | Color | Background | Border | Label | Icon |
|---|---|---|---|---|---|
| `verified` | `text-success` (#3ecf8e) | `bg-success-bg` (8% opacity) | `border-success-border` (25% opacity) | `verified` | ✓ `Check` (lucide, 10px) |
| `unverifiable` | `text-warning` (#d4a843) | `bg-warning-bg` | `border-warning-border` | `unverified` | ? `HelpCircle` (lucide, 10px) |
| `contradicted` | `text-error` (#d44a5c) | `bg-error-bg` | `border-error-border` | `contradicted` | ✗ `X` (lucide, 10px) |
| `not_disclosed` | `text-neutral` (#6b7280) | `bg-neutral-bg` | `border-neutral-border` | `missing` | − `Minus` (lucide, 10px) |

**Additional states** (backend supports these too):
| Status | Label | Treatment |
|---|---|---|
| `low_evidence` | `low evidence` | Same as `unverifiable` (warning family) |
| `cold_start_inferred` | `cold-start` | Same as `warning` but with ❄ icon |

### 6.2 Component spec

```tsx
// components/ai/inline-citation.tsx
import { Check, HelpCircle, X, Minus, Snowflake } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { EvidenceDrawer } from "./evidence-drawer";
import { cn } from "@/lib/utils";
import type { ClaimRow } from "@/lib/types";

const STATE_CONFIG = {
  verified: {
    textClass: "text-success",
    bgClass: "bg-success-bg",
    borderClass: "border-success-border",
    label: "verified",
    Icon: Check,
  },
  unverifiable: {
    textClass: "text-warning",
    bgClass: "bg-warning-bg",
    borderClass: "border-warning-border",
    label: "unverified",
    Icon: HelpCircle,
  },
  contradicted: {
    textClass: "text-error",
    bgClass: "bg-error-bg",
    borderClass: "border-error-border",
    label: "contradicted",
    Icon: X,
  },
  not_disclosed: {
    textClass: "text-neutral",
    bgClass: "bg-neutral-bg",
    borderClass: "border-neutral-border",
    label: "missing",
    Icon: Minus,
  },
  low_evidence: {
    textClass: "text-warning",
    bgClass: "bg-warning-bg",
    borderClass: "border-warning-border",
    label: "low evidence",
    Icon: HelpCircle,
  },
  cold_start_inferred: {
    textClass: "text-warning",
    bgClass: "bg-warning-bg",
    borderClass: "border-warning-border",
    label: "cold-start",
    Icon: Snowflake,
  },
} as const;

export function EvidenceChip({ claim }: { claim: ClaimRow }) {
  const status = claim.validator_status ?? "not_disclosed";
  const config = STATE_CONFIG[status as keyof typeof STATE_CONFIG] ?? STATE_CONFIG.not_disclosed;
  const { Icon } = config;

  return (
    <Sheet>
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
      <SheetContent side="right" title="Claim Detail">
        <EvidenceDrawer claim={claim} />
      </SheetContent>
    </Sheet>
  );
}
```

### 6.3 Hover/click behavior (Agentic Traceability)

- **Hover** (≥300ms): show `Tooltip` (shadcn) with claim text (truncated to 100 chars) + source.ref
- **Click**: open right-side `Sheet` (`EvidenceDrawer`) with:
  - Full claim text (uncapped)
  - Kind (badge: `technical_depth`, `market_size`, etc.)
  - Source section:
    - `source.kind` (badge)
    - `source.ref` (hyperlinked if URL, else monospace)
    - `source.retrieved_by` (monospace, e.g. `github.fetch_github_signals@trace_abc/span_123`)
    - `source.raw_payload_hash` (truncated to 16 chars, monospace)
    - `source.ingested_at` (formatted datetime)
  - Raw payload section:
    - Truncated to first 500 chars
    - "Show more" expander for full payload (JSON pretty-printed)
  - Validator section:
    - Status (chip, same as EvidenceChip)
    - Confidence (font-mono, 2 decimal places)
    - Flags list: each flag shows `flag`, `reason`, `counter_evidence_ref` (if any)
  - Langfuse trace link:
    - Deep link to the span that produced this claim
    - Extracted from `source.retrieved_by` (format: `agent_name@trace_id/span_id`)
    - Button: "View in Langfuse" → opens `LANGFUSE_HOST/trace/{trace_id}/span/{span_id}` in new tab
  - Superseded indicator (if `superseded_by` is set):
    - Yellow warning: "⚠ Superseded by claim `{superseded_by}`"

---

## 7. React Flow Network View Spec

### 7.1 Node types

#### 7.1.1 FounderNode

```tsx
// components/network/founder-node.tsx
import { Handle, Position } from "@xyflow/react";

export function FounderNode({ data }: { data: FounderNodeData }) {
  return (
    <div className={cn(
      "bg-card border rounded-lg p-3 min-w-[160px]",
      data.coldStart ? "border-warning/40" : "border-border-strong",
      data.selected && "border-accent ring-2 ring-accent/20"
    )}>
      <Handle type="target" position={Position.Top} className="!bg-accent !w-2 !h-2" />
      <div className="flex items-center gap-2 mb-2">
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold",
          data.recommendation === "fast_pass" ? "bg-success-bg text-success" :
          data.recommendation === "deep_dive" ? "bg-accent/20 text-accent" :
          data.recommendation === "reject" ? "bg-error-bg text-error" :
          "bg-neutral-bg text-neutral"
        )}>
          {data.founderName.charAt(0)}
        </div>
        <div>
          <div className="text-sm font-bold text-text-primary">{data.founderName}</div>
          <div className="text-xs text-text-muted">{data.companyName}</div>
        </div>
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-text-muted">Conviction</span>
          <span className="font-mono text-text-primary">{data.conviction?.toFixed(0) ?? "—"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-muted">Evidence</span>
          <span className="font-mono text-text-primary">{data.evidenceCoverage?.toFixed(2) ?? "—"}</span>
        </div>
        {data.coldStart && (
          <div className="flex items-center gap-1 text-warning">
            <Snowflake className="w-3 h-3" />
            <span className="text-[10px]">cold-start</span>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-accent !w-2 !h-2" />
    </div>
  );
}
```

**Node data shape**:
```typescript
interface FounderNodeData {
  founderId: string;
  founderName: string;
  companyName: string | null;
  conviction: number | null;
  evidenceCoverage: number | null;
  recommendation: string | null;
  coldStart: boolean;
  selected?: boolean;
}
```

#### 7.1.2 ChannelNode

```tsx
// components/network/channel-node.tsx
export function ChannelNode({ data }: { data: ChannelNodeData }) {
  const channelConfig = {
    github: { color: "text-success", bg: "bg-success-bg", icon: Github },
    arxiv: { color: "text-accent", bg: "bg-accent/20", icon: FileText },
    producthunt: { color: "text-warning", bg: "bg-warning-bg", icon: Rocket },
    hackernews: { color: "text-warning", bg: "bg-warning-bg", icon: Newspaper },
    accelerator: { color: "text-accent", bg: "bg-accent/20", icon: Building },
  };
  const config = channelConfig[data.channelType] ?? channelConfig.github;
  const Icon = config.icon;

  return (
    <div className={cn("bg-card border border-border-strong rounded-full p-3 flex items-center gap-2 min-w-[120px]")}>
      <Handle type="target" position={Position.Top} className="!bg-accent !w-2 !h-2" />
      <div className={cn("w-6 h-6 rounded-full flex items-center justify-center", config.bg, config.color)}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div>
        <div className="text-xs font-bold text-text-primary capitalize">{data.channelType}</div>
        <div className="text-[10px] text-text-muted">{data.signalCount} signals</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-accent !w-2 !h-2" />
    </div>
  );
}
```

#### 7.1.3 InstitutionNode

```tsx
// components/network/institution-node.tsx
export function InstitutionNode({ data }: { data: InstitutionNodeData }) {
  return (
    <div className="bg-modal border border-border-strong rounded-lg p-3 min-w-[140px]" style={{ clipPath: "polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)" }}>
      <Handle type="target" position={Position.Top} className="!bg-accent !w-2 !h-2" />
      <div className="text-center">
        <div className="text-xs font-bold text-text-primary">{data.name}</div>
        <div className="text-[10px] text-text-muted">{data.type}</div>
        <div className="text-[10px] text-text-muted mt-1">{data.founderCount} founders</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-accent !w-2 !h-2" />
    </div>
  );
}
```

### 7.2 Edge styling

```typescript
const defaultEdgeOptions = {
  type: "smoothstep",
  style: {
    stroke: "rgba(255, 255, 255, 0.15)",  // muted neutral
    strokeWidth: 1.5,
  },
  animated: false,  // no animation — hurts scannability
};

// Highlighted edge (on node hover)
const highlightedEdgeOptions = {
  style: {
    stroke: "var(--color-accent)",
    strokeWidth: 2,
  },
  animated: true,
};
```

### 7.3 Interaction model

- **Click node**: select node → `NodeDetailSidebar` opens on right → all connected edges highlight
- **Hover node** (≥200ms): `Tooltip` shows quick stats (conviction, evidence_coverage, recommendation)
- **Double-click founder node**: navigate to `/founders/{founderId}`
- **Drag node**: reposition (React Flow built-in)
- **Pan/zoom**: React Flow built-in (mouse wheel + drag)
- **Background click**: deselect node, close sidebar

### 7.4 Performance notes (up to 500 nodes)

- Use `React.memo` on all custom node components
- Set `nodesDraggable={true}` but `nodesConnectable={false}` (no manual edge drawing)
- Set `minZoom={0.2}` and `maxZoom={2}` to prevent perf issues at extremes
- Use `onlyRenderVisibleElements` prop on `<ReactFlow />` — critical for 500-node perf
- Disable `elevateEdgesOnSelect` (renders all edges on select — slow at scale)
- Initial layout: use `dagre` for auto-layout (hierarchical, top-to-bottom: channels → founders → institutions)
- Debounce node position updates (50ms) to avoid React re-render storms during drag

### 7.5 NetworkCanvas component

```tsx
// components/network/network-canvas.tsx
import { ReactFlow, Background, Controls, MiniMap } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const nodeTypes = {
  founder: FounderNode,
  channel: ChannelNode,
  institution: InstitutionNode,
};

export function NetworkCanvas({ nodes, edges, onNodeClick }: NetworkCanvasProps) {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={onNodeClick}
      defaultEdgeOptions={defaultEdgeOptions}
      nodesDraggable
      nodesConnectable={false}
      onlyRenderVisibleElements
      minZoom={0.2}
      maxZoom={2}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      proOptions={{ hideAttribution: true }}
      colorMode="dark"
    >
      <Background color="rgba(255,255,255,0.03)" gap={20} />
      <Controls className="!bg-card !border-border" />
      <MiniMap
        className="!bg-card !border-border"
        nodeColor={(node) => {
          if (node.type === "founder") return "#5e6ad2";
          if (node.type === "channel") return "#3ecf8e";
          return "#6b7280";
        }}
        maskColor="rgba(11, 15, 25, 0.7)"
      />
    </ReactFlow>
  );
}
```

---

## 8. Build Order

Ordered by dependency + risk. Each task has a "done when" acceptance criterion.

### Task 1: Base template adaptation + design tokens (Day 1, 2h)

**Done when**:
- `npx create-next-app@latest` with App Router + TypeScript + Tailwind v4
- shadcn-dashboard-landing-template components copied into `components/ui/`
- `app/globals.css` implements the exact color system from §3
- `tailwind.config.ts` extends with our tokens
- Geist Sans loaded via `next/font/google`
- `/inbox` renders a placeholder page with the dark canvas + sidebar shell
- `npm run build` succeeds with bundle < 500KB gzipped

### Task 2: Dashboard/card view with real data binding (Day 1, 3h)

**Done when**:
- `lib/api.ts` + `lib/types.ts` implemented (typed fetch client + TanStack Query hooks)
- `lib/hooks/use-inbox.ts` fetches `GET /api/applications/inbox`
- `InboxPage` renders `FounderCard` grid sorted by `conviction` desc
- `FounderCard` renders every field from §4.1.1
- `AxisScore` component renders 10-segment bar + trend arrow
- Cold-start amber border + ❄ icon renders when `cold_start === true`
- `ConfidenceBand` wide-band visual renders for cold-start founders
- Compound query search box wired to `POST /api/query` (§9.4)
- Filter bar: sector, geography, recommendation, cold-start toggle
- Loading skeleton + empty state + error boundary
- `npm run dev` against backend at `:8000` shows real data

### Task 3: Founder Detail/memo view with Trust Score chips (Day 2, 4h)

**Done when**:
- `FounderDetailPage` renders 3-column layout (section nav | memo | trace panel)
- `MemoView` renders `memo_markdown` with `[^claim_id]` → `EvidenceChip` substitution
- `EvidenceChip` (§6) renders all 4 states (verified/unverifiable/contradicted/not_disclosed) + 2 extra (low_evidence/cold_start_inferred)
- Click chip → `EvidenceDrawer` (right Sheet) opens with full claim detail + Langfuse trace link
- `ColdStartBanner` (§5.4) renders RED-bordered banner when latest snapshot is cold-start
- `SectionCallout` renders `"(not disclosed — request from founder)"` for missing optional sections
- `DueDiligenceLog` renders all claims as TanStack Table
- `ScoreHistorySparkline` renders Recharts sparkline of `score_history`
- `PipelineTrace` (§4.2.1) fetches `GET /api/traces/{run_id}` and renders collapsible span tree
- Sticky header: company name + recommendation pill + conviction score
- Back button navigates to `/inbox`

### Task 4: Thesis Config panel (Day 2, 2h)

**Done when**:
- `ThesisPage` fetches `GET /api/thesis` and renders edit form
- `SectorMultiSelect` chip-based (7 sectors)
- `GeographyChips` ISO-2 country chips (7 geographies)
- `RiskAppetitePanel` collapsible with 4 toggles + 2 numeric inputs
- `RescoreConfirmModal` shows exact confirmation text (§4.3) before save
- `POST /api/thesis` invalidates `inbox` query cache on success
- Reset button reverts to fetched state
- Save button disabled when no changes

### Task 5: React Flow network view (Day 2, 3h)

**Done when**:
- `NetworkPage` fetches `GET /api/outbound/queue` + `GET /api/applications/inbox`
- `NetworkCanvas` (§7.5) renders React Flow with 3 custom node types
- `dagre` auto-layout positions nodes hierarchically (channels top → founders middle → institutions bottom)
- Click node → `NodeDetailSidebar` opens on right with full node details
- Double-click founder node → navigates to `/founders/{founderId}`
- Edge legend bottom-left
- "Reset zoom" + "Fit view" buttons
- Performance: renders 100 nodes without lag (test with mock data)

### Task 6: Outbound funnel view (Day 3, 2h)

**Done when**:
- `FunnelPage` fetches `GET /api/applications` + `GET /api/outbound/queue`
- `FunnelView` renders Sankey-style funnel: Sourced → Screened → Diligence → Decision
- `FunnelStage` shows count + label per stage
- Hover stage → `FunnelTooltip` shows breakdown
- `MetricCard` top row: total inbound, total outbound, conversion rate
- `Tabs` toggle between Funnel view and Table view (TanStack Table)

### Task 7 (OPTIONAL, SKIPPABLE): 3D landing accent

**Only if Tasks 1-6 are complete and tested. Do NOT start until everything else ships.**

**Done when**:
- Subtle WebGL particle background on `/` (login/landing) only — NOT inside dashboard
- Tech Noir palette matching color system (canvas base + accent particles)
- Lightweight (≤50KB JS), uses `requestAnimationFrame`, pauses when tab hidden
- Does NOT block, delay, or risk the core dashboard build
- If anything breaks, delete the file — no other code depends on it

---

## 9. Explicit Non-Goals

The following are OUT OF SCOPE. Do NOT implement them. If a coding agent finds itself building any of the below, STOP and re-read this section.

### 9.1 Out-of-scope frontend features

- ❌ **3D network graph** — React Flow 2D is the resolved decision. No `react-force-graph-3d`, no WebGL network scene, no Three.js for relationships.
- ❌ **3D confidence orb** — confidence is shown via the 2D `ConfidenceBand` component, not a 3D visualization.
- ❌ **Heavy glassmorphism on primary content cards** — `backdrop-blur` is restricted to the global nav bar, dropdown overlays, and hover tooltips ONLY. Never apply to founder cards, memo content, or table rows — it reduces text contrast and conflicts with the "Bloomberg-level analytical depth" requirement.
- ❌ **Animation that delays data legibility** — no fade-in transitions on data load, no stagger animations on card grids, no skeleton shimmer that lasts >300ms. Scannability first.
- ❌ **Light mode** — dark canvas only. The color system is tuned for dark; a light theme would require re-resolving every token.
- ❌ **Mobile-responsive design** — desktop-first (1280px+). The brief targets an investor at a desk reviewing memos, not a mobile user. Tailwind breakpoints exist but mobile layout is not validated.
- ❌ **Internationalization (i18n)** — English-only. No translation layer.
- ❌ **Authentication UI** — no login page, no signup, no OAuth. Single-user demo.
- ❌ **Real-time streaming of GitHub commits** — signals are polled hourly on the backend; the frontend fetches on page load + manual refresh. No WebSocket, no SSE.
- ❌ **Multi-fund / multi-thesis UI** — the data schema supports multiple `Thesis` rows, but the UI exposes only one active thesis at a time. `ThesisPage` is a single-record editor, not a multi-thesis manager.
- ❌ **Portfolio monitoring dashboards** — out of scope per the overall project brief.
- ❌ **Follow-on investment logic** — out of scope.
- ❌ **Fund operations** (LP reporting, capital calls, NAV) — out of scope.
- ❌ **Exit tooling** (IRR/MOIC trackers, acquisition scenarios) — out of scope.
- ❌ **Legal document generation** (SAFEs, term sheets) — out of scope.
- ❌ **CRM-style founder communication workflows** — out of scope beyond cold-outreach email generation (which is backend-only).

### 9.2 Out-of-scope technical decisions (locked, do not revisit)

- ❌ Do NOT swap Next.js for Vite/CRA/Remix — App Router + RSC is the resolved decision.
- ❌ Do NOT swap Tailwind for styled-components/emotion/CSS Modules — Tailwind v4 with `@theme` is the resolved decision.
- ❌ Do NOT swap shadcn/ui for MUI/Ant Design/Chakra — copy-into-repo model is the resolved decision.
- ❌ Do NOT swap React Flow for D3/Cytoscape/vis.js — React Flow's 2D HTML/SVG rendering with custom React nodes is the resolved decision.
- ❌ Do NOT swap Recharts for Chart.js/visx/Nivo — Recharts is bundled in the base template and sufficient for our needs.
- ❌ Do NOT introduce a state management library (Redux/Zustand/MobX) — TanStack Query + React Context is sufficient for server state; local state stays in `useState`.
- ❌ Do NOT introduce a form library (React Hook Form/Formik) — the thesis form is simple enough for controlled components.

### 9.3 Scope boundary restated

The frontend delivers:
1. **Dashboard**: founder card grid with cold-start visual state + compound query search.
2. **Memo view**: full investment memo with per-claim Trust Score chips + evidence drawer + pipeline trace.
3. **Thesis config**: edit active investment thesis with confirmation modal.
4. **Network view**: React Flow 2D canvas of founders ↔ channels ↔ institutions.
5. **Funnel view**: inbound + outbound tracks converging into screening stages.

Anything before the dashboard (marketing site, landing page) or after the memo (portfolio ops, follow-on, exits, fund admin) is out of scope.

---

## Appendix A: API Contract (Backend → Frontend)

The frontend consumes these endpoints from the backend at `http://localhost:8000/api`:

| Method | Path | Returns | Used by |
|---|---|---|---|
| GET | `/api/applications/inbox` | `InboxResponse` (cards[]) | `InboxPage` |
| GET | `/api/founders/{id}/card` | `InboxCard` | (unused — `InboxPage` provides cards) |
| GET | `/api/founders/{id}/memo` | `FounderMemo` | `FounderDetailPage` |
| GET | `/api/thesis` | `Thesis` | `ThesisPage` |
| POST | `/api/thesis` | `Thesis` | `ThesisPage` (save) |
| POST | `/api/applications` | `ApplicationResponse` (202) | (unused — applications submitted via backend) |
| GET | `/api/applications` | list of applications | `FunnelPage` |
| GET | `/api/outbound/queue` | `OutboundCard[]` | `NetworkPage`, `FunnelPage` |
| POST | `/api/outbound/scan` | `{scan_id, status}` (202) | (unused — scans triggered via backend cron) |
| POST | `/api/query` | `QueryResponse` | `InboxPage` (compound search) |
| GET | `/api/traces/{run_id}` | `TraceResponse` | `FounderDetailPage` (trace panel) |
| GET | `/api/admin/latency` | `LatencyResponse` | (unused — admin-only) |
| GET | `/api/ping` | `{pong: true}` | health check |

**Vite dev proxy** (`next.config.ts` rewrites):
```typescript
// next.config.ts
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: "http://localhost:8000/api/:path*",
    },
  ];
}
```

---

## Appendix B: File-to-Spec Mapping

| Spec section | File(s) |
|---|---|
| §3 Design tokens | `app/globals.css`, `tailwind.config.ts`, `config/theme.ts` |
| §4.1 Dashboard | `app/inbox/page.tsx`, `components/founder/founder-card.tsx`, `components/founder/axis-score.tsx` |
| §4.2 Memo view | `app/founders/[founderId]/page.tsx`, `components/memo/memo-view.tsx`, `components/memo/evidence-chip.tsx`, `components/memo/evidence-drawer.tsx` |
| §4.3 Thesis config | `app/thesis/page.tsx`, `components/thesis/thesis-editor.tsx` |
| §4.4 Network view | `app/network/page.tsx`, `components/network/network-canvas.tsx`, `components/network/founder-node.tsx`, `components/network/channel-node.tsx`, `components/network/institution-node.tsx` |
| §4.5 Funnel view | `app/funnel/page.tsx`, `components/funnel/funnel-view.tsx` |
| §5 Cold-start state | `components/founder/confidence-band.tsx`, `components/founder/cold-start-banner.tsx` |
| §6 Trust Score chip | `components/ai/inline-citation.tsx`, `components/memo/evidence-drawer.tsx` |
| §7 React Flow | `components/network/*` (all files) |
| §8 Build order | tracked via git commits, one per task |

---

*This file is the single source of truth for the frontend build. Hand it to a coding agent with no human editing pass in between.*
