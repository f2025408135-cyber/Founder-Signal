/** ThesisPage — edit the active investment thesis (spec §9.3).

Per spec §9.3: "Changing sectors/check_size saves to backend and re-scores the inbox;
a confirmation modal appears before re-scoring."
*/
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, AlertCircle, Check, X } from "lucide-react";
import Layout from "../components/Layout";
import { Button, Card, Input, Badge, Modal } from "../components/ui";
import { api, type Thesis } from "../lib/api";

const AVAILABLE_SECTORS = ["AI infra", "DevTools", "Climate", "Robotics", "Fintech", "Healthtech", "EdTech"];
const AVAILABLE_STAGES = ["pre-seed", "seed", "series-a"];
const AVAILABLE_GEOGRAPHIES = ["DE", "US", "PK", "SG", "GB", "FR", "IN"];

export default function ThesisPage() {
  const qc = useQueryClient();
  const { data: thesis, isLoading, error } = useQuery({
    queryKey: ["thesis"],
    queryFn: api.getThesis,
  });

  const [draft, setDraft] = useState<Thesis | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    if (thesis) setDraft(thesis);
  }, [thesis]);

  const saveMutation = useMutation({
    mutationFn: (patch: Partial<Thesis>) => api.updateThesis(patch),
    onSuccess: (saved) => {
      setDraft(saved);
      qc.invalidateQueries({ queryKey: ["thesis"] });
      qc.invalidateQueries({ queryKey: ["inbox"] });
    },
  });

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-24 text-sm text-[var(--color-muted-foreground)]">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading thesis…
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="px-8 py-6 max-w-3xl mx-auto">
          <Card className="p-5 border-[var(--color-destructive)]/30">
            <div className="flex items-center gap-2 text-[var(--color-destructive)]">
              <AlertCircle className="w-4 h-4" />
              <span className="font-medium text-sm">Failed to load thesis</span>
            </div>
            <p className="text-xs mt-2 text-[var(--color-muted-foreground)]">{(error as Error).message}</p>
          </Card>
        </div>
      </Layout>
    );
  }

  if (!draft) return null;

  const hasChanges = JSON.stringify(draft) !== JSON.stringify(thesis);

  const onSave = () => {
    setShowConfirm(true);
  };

  const onConfirmSave = () => {
    setShowConfirm(false);
    saveMutation.mutate({
      name: draft.name,
      sectors: draft.sectors,
      stage: draft.stage,
      geography: draft.geography,
      check_size_usd: draft.check_size_usd,
      ownership_target_pct: draft.ownership_target_pct,
      risk_appetite: draft.risk_appetite,
    });
  };

  return (
    <Layout>
      <div className="px-8 py-6 max-w-3xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Investment Thesis</h1>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
            The active thesis drives all scoring. Only one thesis can be active at a time.
          </p>
        </header>

        <Card className="p-6 space-y-5">
          {/* Name */}
          <label className="block">
            <span className="text-xs font-medium text-[var(--color-muted-foreground)]">Name</span>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              className="mt-1"
            />
          </label>

          {/* Sectors (multi-select chips) */}
          <div>
            <span className="text-xs font-medium text-[var(--color-muted-foreground)]">Sectors</span>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {AVAILABLE_SECTORS.map((s) => {
                const selected = draft.sectors.includes(s);
                return (
                  <button
                    key={s}
                    onClick={() =>
                      setDraft({
                        ...draft,
                        sectors: selected ? draft.sectors.filter((x) => x !== s) : [...draft.sectors, s],
                      })
                    }
                    className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                      selected
                        ? "bg-[var(--color-primary)] text-[var(--color-primary-foreground)] border-[var(--color-primary)]"
                        : "border-[var(--color-border)] hover:bg-[var(--color-accent)]"
                    }`}
                  >
                    {s} {selected && <X className="w-2.5 h-2.5 inline ml-1" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Stage */}
          <div>
            <span className="text-xs font-medium text-[var(--color-muted-foreground)]">Stage</span>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {AVAILABLE_STAGES.map((s) => {
                const selected = draft.stage.includes(s);
                return (
                  <button
                    key={s}
                    onClick={() =>
                      setDraft({
                        ...draft,
                        stage: selected ? draft.stage.filter((x) => x !== s) : [...draft.stage, s],
                      })
                    }
                    className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                      selected
                        ? "bg-[var(--color-primary)] text-[var(--color-primary-foreground)] border-[var(--color-primary)]"
                        : "border-[var(--color-border)] hover:bg-[var(--color-accent)]"
                    }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Geography */}
          <div>
            <span className="text-xs font-medium text-[var(--color-muted-foreground)]">Geography (ISO-2)</span>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {AVAILABLE_GEOGRAPHIES.map((g) => {
                const selected = draft.geography.includes(g);
                return (
                  <button
                    key={g}
                    onClick={() =>
                      setDraft({
                        ...draft,
                        geography: selected ? draft.geography.filter((x) => x !== g) : [...draft.geography, g],
                      })
                    }
                    className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                      selected
                        ? "bg-[var(--color-primary)] text-[var(--color-primary-foreground)] border-[var(--color-primary)]"
                        : "border-[var(--color-border)] hover:bg-[var(--color-accent)]"
                    }`}
                  >
                    {g}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Check size + ownership */}
          <div className="grid grid-cols-2 gap-4">
            <label className="block">
              <span className="text-xs font-medium text-[var(--color-muted-foreground)]">Check Size (USD)</span>
              <Input
                type="number"
                value={draft.check_size_usd}
                onChange={(e) => setDraft({ ...draft, check_size_usd: Number(e.target.value) })}
                className="mt-1"
              />
            </label>
            <label className="block">
              <span className="text-xs font-medium text-[var(--color-muted-foreground)]">Ownership Target (%)</span>
              <Input
                type="number"
                step="0.1"
                value={draft.ownership_target_pct}
                onChange={(e) => setDraft({ ...draft, ownership_target_pct: Number(e.target.value) })}
                className="mt-1"
              />
            </label>
          </div>

          {/* Risk appetite */}
          <details className="border border-[var(--color-border)] rounded-md">
            <summary className="px-4 py-3 cursor-pointer text-sm font-medium">Risk Appetite</summary>
            <div className="px-4 pb-4 space-y-3">
              <label className="block">
                <span className="text-xs text-[var(--color-muted-foreground)]">Max founder age (years since incorporation)</span>
                <Input
                  type="number"
                  value={draft.risk_appetite.max_founder_age_years}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      risk_appetite: { ...draft.risk_appetite, max_founder_age_years: Number(e.target.value) },
                    })
                  }
                  className="mt-1"
                />
              </label>
              <label className="block">
                <span className="text-xs text-[var(--color-muted-foreground)]">Min conviction score</span>
                <Input
                  type="number"
                  value={draft.risk_appetite.min_conviction_score}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      risk_appetite: { ...draft.risk_appetite, min_conviction_score: Number(e.target.value) },
                    })
                  }
                  className="mt-1"
                />
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ["accepts_no_prior_funding", "Accepts no prior funding"],
                  ["accepts_no_github", "Accepts no GitHub"],
                  ["accepts_cold_start", "Accepts cold-start"],
                  ["allow_neutral_market", "Allow neutral market"],
                ].map(([key, label]) => (
                  <label key={key} className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={(draft.risk_appetite as Record<string, unknown>)[key] as boolean}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          risk_appetite: { ...draft.risk_appetite, [key]: e.target.checked },
                        })
                      }
                      className="w-3.5 h-3.5"
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
          </details>

          {/* Status */}
          {saveMutation.isPending && (
            <div className="text-xs text-[var(--color-muted-foreground)] flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" /> Saving…
            </div>
          )}
          {saveMutation.isError && (
            <div className="text-xs text-[var(--color-destructive)] flex items-center gap-2">
              <AlertCircle className="w-3 h-3" /> {(saveMutation.error as Error).message}
            </div>
          )}
          {saveMutation.isSuccess && (
            <div className="text-xs text-[var(--color-verified)] flex items-center gap-2">
              <Check className="w-3 h-3" /> Saved — inbox will re-evaluate on next view.
            </div>
          )}

          {/* Save button */}
          <div className="flex justify-end gap-2 pt-2 border-t border-[var(--color-border)]">
            <Button variant="ghost" onClick={() => setDraft(thesis ?? null)} disabled={!hasChanges}>
              Reset
            </Button>
            <Button onClick={onSave} disabled={!hasChanges || saveMutation.isPending}>
              Save & Re-evaluate
            </Button>
          </div>
        </Card>

        {/* Metadata */}
        <div className="mt-4 flex items-center gap-3 text-[10px] text-[var(--color-muted-foreground)]">
          <Badge variant="outline">id: {draft.id.slice(0, 8)}</Badge>
          <span>updated: {new Date(draft.updated_at).toLocaleString()}</span>
          {draft.active && <Badge>active</Badge>}
        </div>
      </div>

      {/* Confirmation modal (spec §9.3) */}
      <Modal
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        title="Re-evaluate inbox?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowConfirm(false)}>
              Cancel
            </Button>
            <Button onClick={onConfirmSave}>Save & Re-evaluate</Button>
          </>
        }
      >
        <p>
          Saving will re-evaluate all founders in the inbox. The re-score triggers will fire on the
          next card view for each founder (cached outputs are now stale relative to the updated thesis).
          This may incur LLM costs for each re-scored founder.
        </p>
        <p className="mt-2 text-[var(--color-muted-foreground)]">
          Continue?
        </p>
      </Modal>
    </Layout>
  );
}
