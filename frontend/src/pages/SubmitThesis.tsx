import { useState } from "react";
import { api } from "../api/client";

type Thesis = {
  id: number;
  title: string;
  abstract: string;
  source: string;
};

export default function SubmitThesis() {
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Thesis | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const t = await api<Thesis>("/api/theses", {
        method: "POST",
        json: { title, abstract },
      });
      setCreated(t);
      setTitle("");
      setAbstract("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <h1>Submit a thesis topic</h1>
      <p style={{ color: "#6b7280" }}>
        Your submission will be embedded and available for the chat agent to recommend.
      </p>
      {error && <div className="error">{error}</div>}
      {created && (
        <div className="card">
          <strong>Saved as #{created.id}</strong> ({created.source}): {created.title}
        </div>
      )}
      <form onSubmit={onSubmit}>
        <div className="form-row">
          <label>Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} />
        </div>
        <div className="form-row">
          <label>Abstract</label>
          <textarea
            rows={8}
            value={abstract}
            onChange={(e) => setAbstract(e.target.value)}
            required
            minLength={10}
          />
        </div>
        <button type="submit" disabled={busy}>{busy ? "Embedding…" : "Submit"}</button>
      </form>
    </div>
  );
}
