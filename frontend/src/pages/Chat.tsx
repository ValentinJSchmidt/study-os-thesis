import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import TopBar from "../components/TopBar";
import PaperCard, { type Paper } from "../components/PaperCard";

type Role = "user" | "assistant" | "tool" | "system";

type Message = {
  id: number;
  session_id: number;
  role: Role;
  content: string;
  tool_calls?: unknown;
  tool_name?: string | null;
  created_at: string;
};

type Session = { id: number; user_id: number; created_at: string };

// Mock ArXiv paper cards for the right sidebar
const MOCK_PAPERS: Paper[] = [
  {
    id: "1",
    category: "ArXiv • CS.AI",
    title: "Emergent Abilities in Large Language Models: A Critical Review",
    abstract:
      "This paper investigates the phenomenon of emergent abilities in LLMs, challenging previous assumptions with new metrics and rigorous statistical analysis across multiple benchmarks.",
    aiInsight:
      "Highly relevant to your statistics background. Introduces a novel framework for evaluating model performance stability.",
  },
  {
    id: "2",
    category: "ArXiv • STAT.ML",
    title:
      "Probabilistic Inference in High-Dimensional Spaces for Robotics",
    abstract:
      "We propose a new sampling method that significantly reduces computational overhead when dealing with complex, high-dimensional state spaces in autonomous robotic systems.",
    authors: "Chen, et al.",
    daysAgo: 2,
  },
  {
    id: "3",
    category: "ArXiv • CS.LG",
    title: "Scalable Self-Supervised Learning for Scientific Graphs",
    abstract:
      "A contrastive learning framework tailored for molecular and citation graphs that achieves state-of-the-art results with minimal labeled data.",
    authors: "Müller, et al.",
    daysAgo: 5,
  },
];

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Chat() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load sessions once on mount. Auto-create if the user has none.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await api<Session[]>("/api/chat/sessions");
        if (cancelled) return;
        if (list.length > 0) {
          setSessions(list);
          setActive(list[0].id);
        } else {
          // No sessions yet — create one automatically.
          const s = await api<Session>("/api/chat/sessions", { method: "POST" });
          if (cancelled) return;
          setSessions([s]);
          setActive(s.id);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load failed");
      }
    })();
    return () => { cancelled = true; };
  }, []); // run once on mount only

  // Load messages whenever the active session changes.
  useEffect(() => {
    if (active === null) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const msgs = await api<Message[]>(`/api/chat/sessions/${active}/messages`);
        if (!cancelled) setMessages(msgs);
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof Error ? err.message : "Load failed";
        if (msg.toLowerCase().includes("not found")) {
          // Session gone — just deselect, don't trigger another load cycle.
          setActive(null);
          setMessages([]);
        } else {
          setError(msg);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [active]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function newSession() {
    setError(null);
    try {
      const s = await api<Session>("/api/chat/sessions", { method: "POST" });
      setSessions((prev) => [s, ...prev]);
      setActive(s.id);
      setMessages([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create session");
    }
  }

  async function send(e?: React.FormEvent) {
    e?.preventDefault();
    if (!active || !input.trim() || busy) return;
    setError(null);
    setBusy(true);
    const sessionId = active;
    const content = input.trim();
    setInput("");
    // Reset textarea height back to single line after clearing.
    if (textareaRef.current) {
      textareaRef.current.style.height = "48px";
    }

    // Optimistically show the user's message while the worker runs the turn.
    const tempId = -Date.now();
    setMessages((prev) => [
      ...prev,
      { id: tempId, session_id: sessionId, role: "user", content, created_at: new Date().toISOString() },
    ]);

    try {
      // The agent loop runs in a background worker; the POST returns a job id.
      const { job_id } = await api<{ job_id: string; session_id: number }>(
        `/api/chat/sessions/${sessionId}/messages`,
        { method: "POST", json: { content } },
      );

      // Poll the job until the turn finishes, then refetch the full history.
      // (Live streaming over WebSocket is a separate follow-up.)
      // Up to ~5 minutes: local LLMs can be slow, especially under memory pressure.
      const POLL_INTERVAL_MS = 2000;
      const MAX_POLLS = 150; // 150 * 2s = 300s
      let status = "pending";
      for (let i = 0; i < MAX_POLLS && status !== "success" && status !== "failure"; i++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        const job = await api<{ status: string }>(`/api/jobs/${job_id}`);
        status = job.status;
      }

      const msgs = await api<Message[]>(`/api/chat/sessions/${sessionId}/messages`);
      setMessages(msgs);

      if (status === "failure") {
        setError("The assistant could not complete this turn. Please try again.");
      } else if (status !== "success") {
        setError("Still working on it — your reply will appear here once it's ready.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed");
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
    } finally {
      setBusy(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Send on Enter, newline on Shift+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  const visibleMessages = messages.filter(
    (m) => m.role === "user" || m.role === "assistant",
  );

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      <TopBar title="AI Research Assistant" showSearch={false} />

      <main className="flex-1 overflow-hidden p-margin-desktop grid grid-cols-12 gap-gutter bg-surface-container-low">
        {/* Chat panel — left 8 cols */}
        <div className="col-span-12 lg:col-span-8 flex flex-col bg-surface-container-lowest rounded-xl border border-outline-variant h-full overflow-hidden">
          {/* Session tabs */}
          <div className="flex items-center gap-2 px-4 pt-3 pb-2 border-b border-outline-variant overflow-x-auto shrink-0">
            <button
              onClick={newSession}
              className="shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md hover:bg-primary/90 transition-colors text-[11px]"
            >
              <span className="material-symbols-outlined text-[14px]">add</span>
              New
            </button>
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => setActive(s.id)}
                className={`shrink-0 px-3 py-1.5 rounded-full font-label-md text-[11px] transition-colors
                  ${s.id === active
                    ? "bg-primary-fixed text-on-primary-fixed-variant font-bold"
                    : "border border-outline-variant text-on-surface-variant hover:bg-surface-container-high"
                  }`}
              >
                Session #{s.id}
              </button>
            ))}
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-stack-lg flex flex-col gap-stack-lg">
            {active === null ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <div className="w-8 h-8 border-2 border-outline-variant border-t-primary rounded-full animate-spin" />
                <p className="font-body-sm text-on-surface-variant">Session wird geladen…</p>
              </div>
            ) : (
              <>
                {/* Timestamp header */}
                {messages.length > 0 && (
                  <div className="flex justify-center">
                    <span className="font-label-md text-label-md text-on-surface-variant text-xs">
                      {formatTime(messages[0].created_at)}
                    </span>
                  </div>
                )}

                {/* Welcome AI bubble if empty */}
                {messages.length === 0 && !busy && (
                  <div className="flex gap-unit max-w-[85%]">
                    <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center flex-shrink-0 mt-1">
                      <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                    </div>
                    <div className="bg-surface-container rounded-2xl rounded-tl-sm p-stack-md border border-outline-variant shadow-sm ai-glass-panel">
                      <div className="font-label-md text-label-md mb-unit ai-gradient-text-teal">
                        ScholarAI Assistant
                      </div>
                      <p className="font-body-md text-body-md text-on-surface leading-relaxed">
                        Hallo! Ich habe dein Transcript analysiert. Du hast starke
                        Grundlagen in KI und Statistik. Worüber möchtest du heute
                        mehr erfahren? Ich habe Zugriff auf aktuelle ArXiv-Paper
                        und Lehrstuhl-Infos.
                      </p>
                      <div className="flex flex-wrap gap-unit mt-stack-md">
                        <button
                          onClick={() => setInput("Zeig mir aktuelle ArXiv Trends")}
                          className="font-label-md text-[11px] px-3 py-1.5 rounded-full border border-outline-variant text-on-surface-variant hover:border-primary hover:text-primary transition-colors bg-surface-container-lowest"
                        >
                          Show ArXiv trends
                        </button>
                        <button
                          onClick={() => setInput("Erkläre mir spezifische Lehrstühle")}
                          className="font-label-md text-[11px] px-3 py-1.5 rounded-full border border-outline-variant text-on-surface-variant hover:border-primary hover:text-primary transition-colors bg-surface-container-lowest"
                        >
                          Explore specific Lehrstuhl
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {visibleMessages.map((m) => (
                  <ChatBubble key={m.id} m={m} />
                ))}

                {/* Tool call details (collapsible) */}
                {messages
                  .filter((m) => m.role === "tool")
                  .map((m) => (
                    <details
                      key={m.id}
                      className="text-[11px] text-on-surface-variant border border-outline-variant rounded-lg px-3 py-2 bg-surface-container"
                    >
                      <summary className="cursor-pointer font-label-md">
                        tool · {m.tool_name ?? "result"}
                      </summary>
                      <pre className="mt-2 whitespace-pre-wrap font-mono text-[10px]">
                        {m.content}
                      </pre>
                    </details>
                  ))}

                {busy && (
                  <div className="flex gap-unit max-w-[85%]">
                    <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center flex-shrink-0 mt-1">
                      <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                    </div>
                    <div className="bg-surface-container rounded-2xl rounded-tl-sm p-stack-md border border-outline-variant shadow-sm ai-glass-panel">
                      <div className="font-label-md text-label-md mb-unit ai-gradient-text-teal">
                        ScholarAI Assistant
                      </div>
                      <div className="flex gap-1 items-center">
                        <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce [animation-delay:0ms]" />
                        <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce [animation-delay:150ms]" />
                        <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce [animation-delay:300ms]" />
                      </div>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="bg-error-container text-on-error-container border border-error/30 rounded-lg px-4 py-3 font-body-sm text-body-sm">
                    {error}
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input area */}
          <div className="p-stack-md border-t border-outline-variant bg-surface-container-lowest shrink-0">
            <form onSubmit={send} className="relative flex items-end gap-2">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  // Auto-grow: reset to auto first so shrinking works too.
                  e.target.style.height = "auto";
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
                }}
                onKeyDown={handleKeyDown}
                disabled={busy || active === null}
                placeholder={active === null ? "Erstelle zuerst eine neue Session…" : "Forschungsfrage stellen… (Enter senden, Shift+Enter Zeilenumbruch)"}
                rows={1}
                className="flex-1 resize-none bg-surface-container border border-outline-variant focus:border-primary rounded-xl py-3 pl-4 pr-4 outline-none font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant transition-colors disabled:opacity-40"
                style={{ minHeight: "48px", maxHeight: "160px", overflowY: "auto" }}
              />
              <button
                type="submit"
                disabled={busy || !input.trim() || active === null}
                className="mb-0.5 w-10 h-10 flex items-center justify-center text-primary hover:bg-surface-container-highest rounded-xl transition-colors disabled:opacity-40 shrink-0 border border-outline-variant"
              >
                <span
                  className="material-symbols-outlined"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  send
                </span>
              </button>
            </form>
            <div className="mt-2 flex justify-between items-center px-1">
              <span className="font-label-md text-[10px] text-on-surface-variant uppercase tracking-wider">
                AI kann Fehler machen. Wichtige Infos prüfen.
              </span>
            </div>
          </div>
        </div>

        {/* Sidebar — right 4 cols */}
        <div className="hidden lg:flex col-span-4 flex-col gap-stack-md overflow-y-auto h-full pr-1">
          <h3 className="font-title-lg text-title-lg text-on-surface flex items-center gap-2 mb-unit shrink-0">
            <span className="material-symbols-outlined text-tertiary">trending_up</span>
            Aktuelle Trends für dich
          </h3>
          {MOCK_PAPERS.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </div>
      </main>
    </div>
  );
}

function ChatBubble({ m }: { m: Message }) {
  const isUser = m.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-primary text-on-primary rounded-2xl rounded-tr-sm px-4 py-3">
          <p className="font-body-md text-body-md leading-relaxed">{m.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-unit max-w-[85%]">
      <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center flex-shrink-0 mt-1">
        <span className="material-symbols-outlined text-[18px]">smart_toy</span>
      </div>
      <div className="bg-surface-container rounded-2xl rounded-tl-sm p-stack-md border border-outline-variant shadow-sm">
        <div className="font-label-md text-label-md mb-unit ai-gradient-text-teal">
          ScholarAI Assistant
        </div>
        {m.tool_calls ? (
          <>
            <p className="font-body-md text-body-md text-on-surface leading-relaxed">
              {m.content || (
                <em className="text-on-surface-variant">(calling tool…)</em>
              )}
            </p>
            <details className="mt-2 text-[11px] text-on-surface-variant">
              <summary className="cursor-pointer">tool_calls</summary>
              <pre className="mt-1 whitespace-pre-wrap font-mono text-[10px]">
                {JSON.stringify(m.tool_calls, null, 2)}
              </pre>
            </details>
          </>
        ) : (
          <p className="font-body-md text-body-md text-on-surface leading-relaxed whitespace-pre-wrap">
            {m.content}
          </p>
        )}
      </div>
    </div>
  );
}
