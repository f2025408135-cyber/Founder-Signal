"use client";
import { useState, Suspense, lazy } from "react";
import { useRouter } from "next/navigation";
import { Search, ArrowRight, Loader2 } from "lucide-react";
import { Button, Input } from "@/components/ui/primitives";

// Lazy-load the particle sphere so it never blocks initial page render
const ParticleSphereWithFallback = lazy(() =>
  import("@/components/hero/particle-sphere").then((m) => ({
    default: m.ParticleSphereWithFallback,
  }))
);

const SUGGESTION_CHIPS = [
  "Cold-start technical founders in Berlin",
  "Contradicted claims this week",
  "Top Founder Scores, AI infra, pre-seed",
  "No prior VC backing, top-tier accelerator",
  "Improving trend, last 30 days",
  "Idea-vs-Market bears with strong founders",
];

export default function HeroPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSubmitting(true);
    // Navigate to /inbox with the query as a URL param — the inbox page reads it
    router.push(`/inbox?q=${encodeURIComponent(query.trim())}`);
  };

  const handleChipClick = (chip: string) => {
    setQuery(chip);
    setSubmitting(true);
    router.push(`/inbox?q=${encodeURIComponent(chip)}`);
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden"
      style={{
        background:
          "radial-gradient(ellipse at center, #0a0b0d 0%, #07080a 50%, #050608 100%)",
      }}
    >
      {/* Particle sphere — centered, occupies upper 60% of viewport */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[600px] h-[600px] max-w-[80vw] max-h-[60vh]">
          <Suspense
            fallback={
              <div
                className="w-full h-full rounded-full"
                style={{
                  background:
                    "radial-gradient(circle, #c8e8ff 0%, #3d5a80 30%, #1a2438 60%, transparent 80%)",
                  filter: "blur(30px)",
                  opacity: 0.4,
                }}
              />
            }
          >
            <ParticleSphereWithFallback />
          </Suspense>
        </div>
      </div>

      {/* Content layer — above the sphere */}
      <div className="relative z-10 flex flex-col items-center px-6 max-w-2xl w-full">
        {/* Greeting */}
        <h1
          className="text-4xl md:text-5xl font-bold text-center mb-3"
          style={{
            color: "#e0e6ed",
            letterSpacing: "-0.04em",
            textShadow: "0 0 40px rgba(200, 232, 255, 0.15)",
          }}
        >
          Ask the VC Brain anything.
        </h1>

        {/* Subtext */}
        <p
          className="text-sm md:text-base text-center mb-8 max-w-lg"
          style={{ color: "#6b7280" }}
        >
          Search founders by any combination of signal — technical background, sector, geography,
          traction, funding history.
        </p>

        {/* Suggestion chips */}
        <div className="flex flex-wrap gap-2 justify-center mb-8 max-w-lg">
          {SUGGESTION_CHIPS.map((chip) => (
            <button
              key={chip}
              onClick={() => handleChipClick(chip)}
              className="px-3 py-1.5 rounded-full text-xs border transition-all hover:scale-105"
              style={{
                borderColor: "rgba(61, 90, 128, 0.3)",
                background: "rgba(26, 36, 56, 0.4)",
                color: "#9ca3af",
                backdropFilter: "blur(4px)",
              }}
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input bar */}
        <form onSubmit={handleSubmit} className="w-full max-w-xl">
          <div className="relative">
            <Search
              className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4"
              style={{ color: "#3d5a80" }}
            />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask me anything about your pipeline..."
              className="pl-12 pr-32 h-12 text-base rounded-xl"
              style={{
                background: "rgba(20, 21, 26, 0.6)",
                borderColor: "rgba(61, 90, 128, 0.2)",
                color: "#e0e6ed",
                backdropFilter: "blur(8px)",
              }}
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              <Button
                type="submit"
                size="md"
                disabled={!query.trim() || submitting}
                className="h-9 rounded-lg"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    Search
                    <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>

        {/* Skip to dashboard link */}
        <button
          onClick={() => router.push("/inbox")}
          className="mt-8 text-xs transition-colors hover:underline"
          style={{ color: "#3d5a80" }}
        >
          Skip to dashboard →
        </button>
      </div>

      {/* Bottom vignette for depth */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 40%, rgba(5, 6, 8, 0.6) 100%)",
        }}
      />
    </div>
  );
}
