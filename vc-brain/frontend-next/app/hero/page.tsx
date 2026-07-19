"use client";
import { useState, useRef, useEffect, Suspense, lazy } from "react";
import { useRouter } from "next/navigation";
import { Search, ArrowRight, Loader2, Send, Sparkles, RotateCcw } from "lucide-react";
import { Button, Input, Card, Badge } from "@/components/ui/primitives";

// Lazy-load the particle sphere
const ParticleSphereWithFallback = lazy(() =>
  import("@/components/hero/particle-sphere").then((m) => ({
    default: m.ParticleSphereWithFallback,
  }))
);

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ThesisState {
  sectors?: string[] | null;
  stage?: string[] | null;
  geography?: string[] | null;
  check_size_usd?: number | null;
  ownership_target_pct?: number | null;
  risk_appetite?: {
    accepts_cold_start?: boolean;
    accepts_no_github?: boolean;
    min_conviction_score?: number;
    allow_neutral_market?: boolean;
  } | null;
  all_filled?: boolean;
  confirmed?: boolean;
}

const FIN_GREETING = "Hey — I'm Fin. Tell me what you're looking for. Sector, stage, geography, check size — whatever's on your mind.";

export default function HeroPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: FIN_GREETING },
  ]);
  const [input, setInput] = useState("");
  const [thesisState, setThesisState] = useState<ThesisState>({});
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pipelineStarted, setPipelineStarted] = useState(false);
  const [dashboardUrl, setDashboardUrl] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(false); // toggle between hero + chat mode
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const message = (text || input).trim();
    if (!message || loading) return;

    setShowChat(true);
    const newMessages: ChatMessage[] = [...messages, { role: "user", content: message }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/fin/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          thesis_state: thesisState,
          conversation_history: newMessages.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
          confirmed: thesisState.confirmed || false,
        }),
      });

      if (!res.ok) throw new Error(`Fin error: ${res.status}`);
      const data = await res.json();

      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      setThesisState(data.thesis_state || {});
      setConversationId(data.conversation_id);

      if (data.pipeline_started) {
        setPipelineStarted(true);
        setDashboardUrl(data.dashboard_url);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "I'm having trouble connecting. Give me a sec and try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const resetConversation = () => {
    setMessages([{ role: "assistant", content: FIN_GREETING }]);
    setInput("");
    setThesisState({});
    setConversationId(null);
    setPipelineStarted(false);
    setDashboardUrl(null);
    setShowChat(false);
  };

  // If chat mode is active, show the split-screen layout
  if (showChat) {
    return (
      <div
        className="min-h-screen flex flex-col lg:flex-row"
        style={{ background: "radial-gradient(ellipse at 58% -12%, rgba(200,205,212,.13) 0%, transparent 52%), linear-gradient(145deg, #06070a 0%, #020203 58%, #0a0d11 100%)" }}
      >
        {/* Left: chat panel */}
        <div className="flex-1 flex w-full flex-col px-4 py-6 sm:px-6 sm:py-8 lg:max-w-2xl lg:mx-auto">
          {/* Header */}
          <div className="flex items-center gap-2 mb-6">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #6e7681, #f0f4f8 48%, #6e7681)", color: "#06070a" }}
            >
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold silver-text">Fin</div>
              <div className="technical-label text-text-muted">Conversational Sourcing Agent</div>
            </div>
            <button
              onClick={() => router.push("/inbox")}
              className="ml-auto rounded-sm border border-border-strong bg-canvas-base/40 px-3 py-1 text-xs text-text-muted transition-colors hover:border-accent hover:text-text-primary"
            >
              Skip to dashboard →
            </button>
            <button type="button" onClick={resetConversation} className="rounded-sm border border-transparent p-1.5 text-text-muted transition-colors hover:border-border-strong hover:text-text-primary" aria-label="Start a new investment thesis" title="Start a new thesis"><RotateCcw className="h-3.5 w-3.5" /></button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4" style={{ maxHeight: "calc(100vh - 200px)" }}>
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className="max-w-[80%] rounded-lg px-4 py-2.5 text-sm"
                  style={
                    msg.role === "user"
                      ? { background: "linear-gradient(135deg, #6e7681, #c8cdd4 55%, #f0f4f8)", color: "#06070a", border: "1px solid rgba(240,244,248,.35)" }
                      : { background: "linear-gradient(135deg, rgba(42,47,55,.72), rgba(14,17,22,.9))", color: "#f0f4f8", border: "1px solid rgba(200,205,212,.18)" }
                  }
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div
                  className="rounded-lg px-4 py-2.5 text-sm flex items-center gap-2"
                  style={{ background: "linear-gradient(135deg, rgba(42,47,55,.72), rgba(14,17,22,.9))", color: "#8e96a0", border: "1px solid rgba(200,205,212,.18)" }}
                >
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span className="text-xs">Fin is thinking...</span>
                </div>
              </div>
            )}
            {pipelineStarted && dashboardUrl && (
              <div className="flex justify-center mt-4">
                <button
                  onClick={() => router.push(dashboardUrl)}
                  className="metal-button px-4 py-2 rounded-sm text-sm font-medium flex items-center gap-2"
                >
                  Review queued deal flow
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input bar */}
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about your pipeline..."
              disabled={loading || (pipelineStarted && !!dashboardUrl)}
              className="metal-input w-full h-12 pl-4 pr-12 rounded-sm text-sm"
              style={{
                color: "#f0f4f8",
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="metal-button absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-sm flex items-center justify-center disabled:opacity-30"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right: live thesis summary card */}
        <div className="w-full border-t border-border p-4 sm:p-6 lg:w-96 lg:border-l lg:border-t-0 overflow-y-auto" style={{ background: "linear-gradient(180deg, rgba(14,17,22,.72), rgba(2,2,3,.5))" }}>
          <h3 className="text-sm font-bold mb-4 text-text-primary">
            Thesis Summary
          </h3>
          <ThesisSummaryCard thesis={thesisState} />

          {/* Pipeline progress */}
          {pipelineStarted && (
            <div className="metal-panel mt-6 p-4 rounded-sm">
              <div className="technical-label mb-2">Thesis confirmed</div>
              <p className="text-xs leading-relaxed text-text-secondary">Fin has captured the thesis. The deal queue will show verified pipeline activity as the backend publishes it.</p>
              {dashboardUrl && <button type="button" onClick={() => router.push(dashboardUrl)} className="mt-3 text-xs text-accent hover:text-accent-hover">Open deal queue →</button>}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Default: hero/landing screen (pre-conversation)
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden"
      style={{ background: "radial-gradient(ellipse 58% 48% at 54% 42%, rgba(200,205,212,.14), transparent 65%), linear-gradient(145deg, #06070a, #020203 62%, #0a0d11)" }}
    >
      {/* Particle sphere */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[600px] h-[600px] max-w-[80vw] max-h-[60vh]">
          <Suspense
            fallback={
              <div
                className="w-full h-full rounded-full"
                style={{
                  background: "radial-gradient(circle, #f0f4f8 0%, #c8cdd4 28%, #6e7681 56%, transparent 80%)",
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

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center px-6 max-w-2xl w-full">
        <h1
          className="text-4xl md:text-5xl font-bold text-center mb-3"
          style={{ letterSpacing: "-0.04em", textShadow: "0 0 44px rgba(200,205,212,.2)" }}
        >
          <span className="silver-text">Ask the VC Brain anything.</span>
        </h1>
        <p className="text-sm md:text-base text-center mb-8 max-w-lg text-text-muted">
          Tell Fin what you're looking for — sector, stage, geography, traction, funding history. He'll
          interview you, build your thesis, and run the pipeline.
        </p>

        {/* Suggestion chips */}
        <div className="flex flex-wrap gap-2 justify-center mb-8 max-w-lg">
          {[
            "I want pre-seed AI infra founders in Berlin",
            "Show me climate tech, any stage, remote-friendly",
            "Technical founders, no prior VC, YC or Antler",
          ].map((chip) => (
            <button
              key={chip}
              onClick={() => handleSend(chip)}
              className="metal-panel rounded-sm border-border-strong px-3 py-1.5 text-xs text-text-muted transition-all hover:-translate-y-0.5 hover:border-accent hover:text-text-primary"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input bar — starts Fin conversation */}
        <div className="w-full max-w-xl">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-accent-muted" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about your pipeline..."
              className="metal-input w-full h-12 pl-12 pr-32 rounded-sm text-base text-text-primary"
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="h-9 rounded-sm"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
                  <>Talk to Fin <ArrowRight className="w-3.5 h-3.5 ml-1.5" /></>
                )}
              </Button>
            </div>
          </div>
        </div>

        <button
          onClick={() => router.push("/inbox")}
          className="mt-8 text-xs transition-colors hover:underline"
          style={{ color: "#8e96a0" }}
        >
          Skip to dashboard →
        </button>
      </div>

      {/* Bottom vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at center, transparent 38%, rgba(2, 2, 3, 0.74) 100%)" }}
      />
    </div>
  );
}

/** Thesis Summary Card — live-updating structured view of what Fin has extracted */
function ThesisSummaryCard({ thesis }: { thesis: ThesisState }) {
  const fields = [
    { label: "Sectors", value: thesis.sectors, filled: thesis.sectors && thesis.sectors.length > 0 },
    { label: "Stage", value: thesis.stage, filled: thesis.stage && thesis.stage.length > 0 },
    { label: "Geography", value: thesis.geography, filled: thesis.geography && thesis.geography.length > 0 },
    { label: "Check Size", value: thesis.check_size_usd ? `$${thesis.check_size_usd.toLocaleString()}` : null, filled: !!thesis.check_size_usd },
    { label: "Ownership %", value: thesis.ownership_target_pct ? `${thesis.ownership_target_pct}%` : null, filled: !!thesis.ownership_target_pct },
    { label: "Risk Appetite", value: thesis.risk_appetite ? "Set" : null, filled: !!thesis.risk_appetite },
  ];

  const filled = fields.filter((field) => field.filled).length;
  if (filled === 0) {
    return <Card className="p-4"><p className="technical-label">Thesis capture</p><p className="mt-2 text-sm text-text-secondary">0 of 6 thesis fields captured. Start with a sector, stage, or geography and Fin will fill in the rest conversationally.</p></Card>;
  }

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-border pb-2"><span className="technical-label">Thesis capture</span><span className="font-mono text-xs text-accent">{filled}/6</span></div>
      {fields.map((f) => (
        <div key={f.label} className="flex items-center justify-between">
          <span className="text-xs text-text-muted">{f.label}</span>
          {f.filled ? (
            <Badge variant="success" className="text-[10px]">
              {Array.isArray(f.value) ? f.value.join(", ") : f.value}
            </Badge>
          ) : (
            <span className="text-[10px] text-text-subtle">pending</span>
          )}
        </div>
      ))}
      {thesis.all_filled && !thesis.confirmed && (
        <div className="pt-2 border-t border-border">
          <div className="text-xs" style={{ color: "#d4a843" }}>
            ✓ All fields filled — confirm to start pipeline
          </div>
        </div>
      )}
      {thesis.confirmed && (
        <div className="pt-2 border-t border-border">
          <div className="text-xs" style={{ color: "#3ecf8e" }}>
            ✓ Confirmed — review the live queue for verified activity
          </div>
        </div>
      )}
    </Card>
  );
}
