"use client";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, AlertCircle, Check, X } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button, Card, Input, Badge, Skeleton } from "@/components/ui/primitives";
import { Modal } from "@/components/ui/sheet";
import { api } from "@/lib/api";
import type { Thesis } from "@/lib/types";

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
      <AppShell>
        <div className="px-8 py-6 max-w-3xl mx-auto space-y-5" aria-label="Loading investment thesis">
          <Skeleton className="h-8 w-2/5" />
          <Skeleton className="h-[420px] w-full" />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="px-8 py-6 max-w-3xl mx-auto">
          <Card className="p-5 border-error-border">
            <div className="flex items-center gap-2 text-error">
              <AlertCircle className="w-4 h-4" />
              <span className="font-bold text-sm">Failed to load thesis</span>
            </div>
            <p className="text-xs mt-2 text-text-muted">{(error as Error).message}</p>
          </Card>
        </div>
      </AppShell>
    );
  }

  if (!draft) {
    return (
      <AppShell>
        <div className="px-8 py-6 max-w-3xl mx-auto">
          <Card className="p-5 border-warning-border bg-warning-bg">
            <h1 className="text-sm font-bold text-text-primary">No active thesis is available</h1>
            <p className="mt-2 text-xs text-text-secondary">
              Configure an active investment thesis in the backend before screening founders.
            </p>
          </Card>
        </div>
      </AppShell>
    );
  }

  const hasChanges = JSON.stringify(draft) !== JSON.stringify(thesis);

  return (
    <AppShell>
      <div className="px-8 py-6 max-w-3xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Investment Thesis</h1>
          <p className="text-sm text-text-muted mt-1">
            The active thesis drives all scoring. Only one thesis can be active at a time.
          </p>
        </header>

        <Card className="p-6 space-y-5">
          <label className="block">
            <span className="text-xs font-bold text-text-muted">Name</span>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              className="mt-1"
            />
          </label>

          {/* Sectors */}
          <div>
            <span className="text-xs font-bold text-text-muted">Sectors</span>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {AVAILABLE_SECTORS.map((s) => {
                const selected = draft.sectors.includes(s);
                return (
                  <button
                    key={s}
                    onClick={() =>
                      setDraft({
                        ...draft,
                        sectors: selected
                          ? draft.sectors.filter((x) => x !== s)
                          : [...draft.sectors, s],
                      })
                    }
                    className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                      selected
                        ? "bg-accent text-white border-accent"
                        : "border-border-strong text-text-secondary hover:bg-elevated"
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
            <span className="text-xs font-bold text-text-muted">Stage</span>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {AVAILABLE_STAGES.map((s) => {
                const selected = draft.stage.includes(s);
                return (
                  <button
                    key={s}
                    onClick={() =>
                      setDraft({
                        ...draft,
                        stage: selected
                          ? draft.stage.filter((x) => x !== s)
                          : [...draft.stage, s],
                      })
                    }
                    className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                      selected
                        ? "bg-accent text-white border-accent"
                        : "border-border-strong text-text-secondary hover:bg-elevated"
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
            <span className="text-xs font-bold text-text-muted">Geography (ISO-2)</span>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {AVAILABLE_GEOGRAPHIES.map((g) => {
                const selected = draft.geography.includes(g);
                return (
                  <button
                    key={g}
                    onClick={() =>
                      setDraft({
                        ...draft,
                        geography: selected
                          ? draft.geography.filter((x) => x !== g)
                          : [...draft.geography, g],
                      })
                    }
                    className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${
                      selected
                        ? "bg-accent text-white border-accent"
                        : "border-border-strong text-text-secondary hover:bg-elevated"
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
              <span className="text-xs font-bold text-text-muted">Check Size (USD)</span>
              <Input
                type="number"
                value={draft.check_size_usd}
                onChange={(e) => setDraft({ ...draft, check_size_usd: Number(e.target.value) })}
                className="mt-1"
              />
            </label>
            <label className="block">
              <span className="text-xs font-bold text-text-muted">Ownership Target (%)</span>
              <Input
                type="number"
                step="0.1"
                value={draft.ownership_target_pct}
                onChange={(e) =>
                  setDraft({ ...draft, ownership_target_pct: Number(e.target.value) })
                }
                className="mt-1"
              />
            </label>
          </div>

          {/* Risk appetite */}
          <details className="border border-border rounded-md">
            <summary className="px-4 py-3 cursor-pointer text-sm font-bold text-text-primary">
              Risk Appetite
            </summary>
            <div className="px-4 pb-4 space-y-3">
              <label className="block">
                <span className="text-xs text-text-muted">Max founder age (years since incorporation)</span>
                <Input
                  type="number"
                  value={draft.risk_appetite.max_founder_age_years}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      risk_appetite: {
                        ...draft.risk_appetite,
                        max_founder_age_years: Number(e.target.value),
                      },
                    })
                  }
                  className="mt-1"
                />
              </label>
              <label className="block">
                <span className="text-xs text-text-muted">Min conviction score</span>
                <Input
                  type="number"
                  value={draft.risk_appetite.min_conviction_score}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      risk_appetite: {
                        ...draft.risk_appetite,
                        min_conviction_score: Number(e.target.value),
                      },
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
                  <label key={key} className="flex items-center gap-2 text-xs text-text-secondary">
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
            <div className="text-xs text-text-muted flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" /> Saving…
            </div>
          )}
          {saveMutation.isError && (
            <div className="text-xs text-error flex items-center gap-2">
              <AlertCircle className="w-3 h-3" /> {(saveMutation.error as Error).message}
            </div>
          )}
          {saveMutation.isSuccess && (
            <div className="text-xs text-success flex items-center gap-2">
              <Check className="w-3 h-3" /> Saved. The active investment thesis has been updated.
            </div>
          )}

          {/* Save button */}
          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button variant="ghost" onClick={() => setDraft(thesis ?? null)} disabled={!hasChanges}>
              Reset
            </Button>
            <Button onClick={() => setShowConfirm(true)} disabled={!hasChanges || saveMutation.isPending}>
              Save & Re-evaluate
            </Button>
          </div>
        </Card>

        <div className="mt-4 flex items-center gap-3 text-[10px] text-text-subtle">
          <Badge variant="outline">id: {draft.id.slice(0, 8)}</Badge>
          <span>updated: {new Date(draft.updated_at).toLocaleString()}</span>
          {draft.active && <Badge>active</Badge>}
        </div>
      </div>

      {/* Confirmation modal */}
      <Modal
        open={showConfirm}
        onOpenChange={setShowConfirm}
        title="Re-evaluate inbox?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowConfirm(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
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
              }}
            >
              Save & Re-evaluate
            </Button>
          </>
        }
      >
        <p>
          Saving updates the active investment thesis for subsequent evaluations. Existing evidence
          remains visible while the backend schedules any required re-evaluation.
        </p>
        <p className="mt-2 text-text-muted">Continue?</p>
      </Modal>
    </AppShell>
  );
}
