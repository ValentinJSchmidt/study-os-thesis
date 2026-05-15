import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

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

export default function Chat() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    const list = await api<Session[]>("/api/chat/sessions");
    setSessions(list);
    if (!active && list.length > 0) setActive(list[0].id);
  }, [active]);

  useEffect(() => { void loadSessions(); }, [loadSessions]);

  useEffect(() => {
    if (active === null) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    (async () => {
      const msgs = await api<Message[]>(`/api/chat/sessions/${active}/messages`);
      if (!cancelled) setMessages(msgs);
    })().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
    return () => { cancelled = true; };
  }, [active]);

  async function newSession() {
    setError(null);
    const s = await api<Session>("/api/chat/sessions", { method: "POST" });
    await loadSessions();
    setActive(s.id);
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!active || !input.trim()) return;
    setError(null);
    setBusy(true);
    const content = input.trim();
    setInput("");
    try {
      const res = await api<{ messages: Message[] }>(
        `/api/chat/sessions/${active}/messages`,
        { method: "POST", json: { content } },
      );
      setMessages((prev) => [...prev, ...res.messages]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h1>Chat</h1>
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
        <button onClick={newSession}>+ New session</button>
        {sessions.map((s) => (
          <button
            key={s.id}
            onClick={() => setActive(s.id)}
            style={{ background: s.id === active ? "#e0e7ff" : undefined }}
          >
            #{s.id}
          </button>
        ))}
      </div>

      {error && <div className="error">{error}</div>}

      {active === null ? (
        <p>Start a new session to begin.</p>
      ) : (
        <>
          <div style={{ marginBottom: "1rem" }}>
            {messages.length === 0 && <p style={{ color: "#6b7280" }}>No messages yet.</p>}
            {messages.map((m) => (
              <MessageView key={m.id} m={m} />
            ))}
            {busy && <div className="msg assistant"><div className="role">Assistant</div>…</div>}
          </div>
          <form onSubmit={send} style={{ display: "flex", gap: "0.5rem" }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="What are you interested in?"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !input.trim()}>Send</button>
          </form>
        </>
      )}
    </div>
  );
}

function MessageView({ m }: { m: Message }) {
  if (m.role === "tool") {
    return (
      <details className="msg tool">
        <summary>tool · {m.tool_name ?? "result"}</summary>
        <pre style={{ whiteSpace: "pre-wrap", margin: "0.5rem 0 0" }}>{m.content}</pre>
      </details>
    );
  }
  if (m.role === "assistant" && m.tool_calls) {
    return (
      <div className={`msg assistant`}>
        <div className="role">Assistant (tool call)</div>
        {m.content || <em style={{ color: "#6b7280" }}>(no text — calling tool)</em>}
        <details style={{ marginTop: "0.5rem" }}>
          <summary>tool_calls</summary>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(m.tool_calls, null, 2)}</pre>
        </details>
      </div>
    );
  }
  return (
    <div className={`msg ${m.role}`}>
      <div className="role">{m.role}</div>
      {m.content}
    </div>
  );
}
