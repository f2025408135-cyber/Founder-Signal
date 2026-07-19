"use client";
import { useState, useRef, useEffect, Suspense, lazy } from "react";
import { useRouter } from "next/navigation";
import { Search, ArrowRight, Loader2, Send, Sparkles } from "lucide-react";
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

  // If chat mode is active, show the split-screen layout
  if (showChat) {
    return (
      <div
        className="min-h-screen flex"
        style={{ background: "radial-gradient(ellipse at center, #0a0b0d 0%, #07080a 50%, #050608 100%)" }}
      >
        {/* Left: chat panel */}
        <div className="flex-1 flex flex-col max-w-2xl mx-auto px-6 py-8">
          {/* Header */}
          <div className="flex items-center gap-2 mb-6">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #5e6ad2, #3d5a80)" }}
            >
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="text-sm font-bold" style={{ color: "#e0e6ed" }}>Fin</div>
              <div className="text-[10px]" style={{ color: "#6b7280" }}>Conversational Sourcing Agent</div>
            </div>
            <button
              onClick={() => router.push("/inbox")}
              className="ml-auto text-xs px-3 py-1 rounded-md border"
              style={{ borderColor: "#3d5a80", color: "#9ca3af" }}
            >
              Skip to dashboard →
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4" style={{ maxHeight: "calc(100vh - 200px)" }}>
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className="max-w-[80%] rounded-lg px-4 py-2.5 text-sm"
                  style={
                    msg.role === "user"
                      ? { background: "#5e6ad2", color: "#fff" }
                      : { background: "#14151a", color: "#e0e6ed", border: "1px solid rgba(61,90,128,0.2)" }
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
                  style={{ background: "#14151a", color: "#6b7280", border: "1px solid rgba(61,90,128,0.2)" }}
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
                  className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
                  style={{ background: "#5e6ad2", color: "#fff" }}
                >
                  View results on Dashboard
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
              className="w-full h-12 pl-4 pr-12 rounded-xl text-sm"
              style={{
                background: "rgba(20, 21, 26, 0.6)",
                border: "1px solid rgba(61, 90, 128, 0.2)",
                color: "#e0e6ed",
                backdropFilter: "blur(8px)",
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg flex items-center justify-center disabled:opacity-30"
              style={{ background: "#5e6ad2" }}
            >
              <Send className="w-3.5 h-3.5 text-white" />
            </button>
          </div>
        </div>

        {/* Right: live thesis summary card */}
        <div className="w-96 border-l p-6 overflow-y-auto" style={{ borderColor: "rgba(61,90,128,0.15)" }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: "#e0e6ed" }}>
            Thesis Summary
          </h3>
          <ThesisSummaryCard thesis={thesisState} />

          {/* Pipeline progress */}
          {pipelineStarted && (
            <div className="mt-6 p-4 rounded-lg" style={{ background: "#14151a", border: "1px solid rgba(94,106,210,0.2)" }}>
              <div className="text-xs font-bold mb-2" style={{ color: "#5e6ad2" }}>PIPELINE RUNNING</div>
              <div className="space-y-1.5 text-xs" style={{ color: "#9ca3af" }}>
                <div>✓ Thesis applied</div>
                <div>→ Scanning GitHub, arXiv, PH, HN...</div>
                <div className="opacity-50">○ Screening candidates</div>
                <div className="opacity-50">○ Scoring founder/market/idea</div>
                <div className="opacity-50">○ Validating claims</div>
                <div className="opacity-50">○ Aggregating results</div>
              </div>
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
      style={{ background: "radial-gradient(ellipse at center, #0a0b0d 0%, #07080a 50%, #050608 100%)" }}
    >
      {/* Particle sphere */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[600px] h-[600px] max-w-[80vw] max-h-[60vh]">
          <Suspense
            fallback={
              <div
                className="w-full h-full rounded-full"
                style={{
                  background: "radial-gradient(circle, #c8e8ff 0%, #3d5a80 30%, #1a2438 60%, transparent 80%)",
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
          style={{ color: "#e0e6ed", letterSpacing: "-0.04em", textShadow: "0 0 40px rgba(200, 232, 255, 0.15)" }}
        >
          Ask the VC Brain anything.
        </h1>
        <p className="text-sm md:text-base text-center mb-8 max-w-lg" style={{ color: "#6b7280" }}>
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

        {/* Input bar — starts Fin conversation */}
        <div className="w-full max-w-xl">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "#3d5a80" }} />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about your pipeline..."
              className="w-full h-12 pl-12 pr-32 rounded-xl text-base"
              style={{
                background: "rgba(20, 21, 26, 0.6)",
                border: "1px solid rgba(61, 90, 128, 0.2)",
                color: "#e0e6ed",
                backdropFilter: "blur(8px)",
              }}
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="h-9 rounded-lg"
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
          style={{ color: "#3d5a80" }}
        >
          Skip to dashboard →
        </button>
      </div>

      {/* Bottom vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at center, transparent 40%, rgba(5, 6, 8, 0.6) 100%)" }}
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

  return (
    <Card className="p-4 space-y-3" style={{ background: "#14151a" }}>
      {fields.map((f) => (
        <div key={f.label} className="flex items-center justify-between">
          <span className="text-xs" style={{ color: "#6b7280" }}>{f.label}</span>
          {f.filled ? (
            <Badge variant="success" className="text-[10px]">
              {Array.isArray(f.value) ? f.value.join(", ") : f.value}
            </Badge>
          ) : (
            <span className="text-[10px]" style={{ color: "#4a3a1a" }}>— not yet discussed</span>
          )}
        </div>
      ))}
      {thesis.all_filled && !thesis.confirmed && (
        <div className="pt-2 border-t" style={{ borderColor: "rgba(61,90,128,0.15)" }}>
          <div className="text-xs" style={{ color: "#d4a843" }}>
            ✓ All fields filled — confirm to start pipeline
          </div>
        </div>
      )}
      {thesis.confirmed && (
        <div className="pt-2 border-t" style={{ borderColor: "rgba(61,90,128,0.15)" }}>
          <div className="text-xs" style={{ color: "#3ecf8e" }}>
            ✓ Confirmed — pipeline running
          </div>
        </div>
      )}
    </Card>
  );
}
