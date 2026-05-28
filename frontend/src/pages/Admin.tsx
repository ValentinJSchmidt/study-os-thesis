import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import {
  listChairs,
  createChair,
  deleteChair,
  addArxivDocument,
  deleteDocument,
  type Chair,
  type ChairCreate,
} from "../api/chairs";
import TopBar from "../components/TopBar";

type User = { id: number; email: string; role: string; created_at: string };
type Tab = "users" | "chairs";

// ─── Users tab ────────────────────────────────────────────────────────────────

function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<User[]>("/api/admin/users")
      .then(setUsers)
      .catch((e) => setError(e instanceof Error ? e.message : "Laden fehlgeschlagen"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  return (
    <div className="overflow-x-auto rounded-xl border border-outline-variant">
      <table className="w-full text-sm">
        <thead className="bg-surface-container-low">
          <tr>
            {["ID", "Email", "Rolle", "Erstellt"].map((h) => (
              <th key={h} className="text-left px-4 py-3 font-label-md text-on-surface-variant uppercase tracking-wider text-[11px]">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-t border-outline-variant hover:bg-surface-container-low transition-colors">
              <td className="px-4 py-3 font-label-md text-on-surface-variant">{u.id}</td>
              <td className="px-4 py-3 font-body-sm text-on-surface">{u.email}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded-full text-[11px] font-label-md ${
                  u.role === "admin"
                    ? "bg-error-container text-on-error-container"
                    : "bg-surface-container text-on-surface-variant"
                }`}>
                  {u.role}
                </span>
              </td>
              <td className="px-4 py-3 font-body-sm text-on-surface-variant">
                {new Date(u.created_at).toLocaleDateString("de-DE")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Create chair form ────────────────────────────────────────────────────────

function CreateChairForm({ onCreated }: { onCreated: (c: Chair) => void }) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<ChairCreate>({
    name: "",
    short_description: "",
    professor_name: "",
    website_url: "",
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const chair = await createChair({
        ...form,
        website_url: form.website_url || null,
      });
      onCreated(chair);
      setOpen(false);
      setForm({ name: "", short_description: "", professor_name: "", website_url: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler");
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-lg font-label-md text-label-md hover:bg-primary-container hover:text-on-primary-container transition-colors"
      >
        <span className="material-symbols-outlined text-[18px]">add</span>
        Neuer Lehrstuhl
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 space-y-4 mb-6"
    >
      <h3 className="font-title-md text-on-surface font-semibold">Lehrstuhl anlegen</h3>
      {error && <ErrorBox msg={error} />}

      <Field label="Name *">
        <input required value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          className={inputCls} placeholder="Lehrstuhl für Maschinelles Lernen" />
      </Field>
      <Field label="Kurzbeschreibung *">
        <textarea required rows={3} value={form.short_description}
          onChange={(e) => setForm((f) => ({ ...f, short_description: e.target.value }))}
          className={inputCls} placeholder="Forschungsschwerpunkte…" />
      </Field>
      <Field label="Professor *">
        <input required value={form.professor_name}
          onChange={(e) => setForm((f) => ({ ...f, professor_name: e.target.value }))}
          className={inputCls} placeholder="Prof. Dr. Max Mustermann" />
      </Field>
      <Field label="Website">
        <input value={form.website_url ?? ""} onChange={(e) => setForm((f) => ({ ...f, website_url: e.target.value }))}
          className={inputCls} placeholder="https://…" type="url" />
      </Field>

      <div className="flex gap-3 pt-2">
        <button type="submit" disabled={saving}
          className="bg-primary text-on-primary px-5 py-2 rounded-lg font-label-md text-label-md hover:bg-primary-container hover:text-on-primary-container transition-colors disabled:opacity-50">
          {saving ? "Speichert…" : "Erstellen"}
        </button>
        <button type="button" onClick={() => setOpen(false)}
          className="px-5 py-2 rounded-lg border border-outline-variant font-label-md text-label-md text-on-surface hover:bg-surface-container-high transition-colors">
          Abbrechen
        </button>
      </div>
    </form>
  );
}

// ─── Arxiv ingest form ────────────────────────────────────────────────────────

function ArxivForm({ chairId, onAdded }: { chairId: number; onAdded: () => void }) {
  const [arxivId, setArxivId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!arxivId.trim()) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const doc = await addArxivDocument(chairId, arxivId.trim());
      setSuccess(`"${doc.title ?? arxivId}" erfolgreich hinzugefügt.`);
      setArxivId("");
      onAdded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-start flex-wrap">
      <input
        value={arxivId}
        onChange={(e) => setArxivId(e.target.value)}
        placeholder="ArXiv ID, z.B. 2301.07041"
        className={`${inputCls} w-64`}
      />
      <button type="submit" disabled={loading}
        className="bg-secondary-container text-on-secondary-container px-4 py-2 rounded-lg font-label-md text-label-md hover:opacity-80 transition-opacity disabled:opacity-50 whitespace-nowrap">
        {loading ? "Lädt…" : "Paper hinzufügen"}
      </button>
      {error && <p className="w-full text-error font-body-sm">{error}</p>}
      {success && <p className="w-full text-tertiary-container font-body-sm">{success}</p>}
    </form>
  );
}

// ─── Chair row ────────────────────────────────────────────────────────────────

function ChairRow({
  chair,
  onDeleted,
  onRefresh,
}: {
  chair: Chair;
  onDeleted: (id: number) => void;
  onRefresh: (id: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    if (!confirm(`Lehrstuhl "${chair.name}" wirklich löschen?`)) return;
    setDeleting(true);
    try {
      await deleteChair(chair.id);
      onDeleted(chair.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler");
      setDeleting(false);
    }
  }

  async function handleDeleteDoc(docId: number) {
    try {
      await deleteDocument(chair.id, docId);
      onRefresh(chair.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Löschen");
    }
  }

  const papers = chair.documents.filter((d) => d.kind === "paper");

  return (
    <div className="border border-outline-variant rounded-xl overflow-hidden">
      {/* Header row */}
      <div className="flex items-center justify-between p-4 bg-surface-container-lowest">
        <div className="flex-1 min-w-0">
          <h4 className="font-title-md text-on-surface font-semibold truncate">{chair.name}</h4>
          <p className="font-body-sm text-on-surface-variant">{chair.professor_name} · {papers.length} Papers</p>
        </div>
        <div className="flex items-center gap-2 ml-4 shrink-0">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="p-2 rounded-lg hover:bg-surface-container-high transition-colors"
            title={expanded ? "Zuklappen" : "Aufklappen"}
          >
            <span className="material-symbols-outlined text-on-surface-variant">
              {expanded ? "expand_less" : "expand_more"}
            </span>
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-2 rounded-lg hover:bg-error-container transition-colors text-error disabled:opacity-40"
            title="Löschen"
          >
            <span className="material-symbols-outlined">delete</span>
          </button>
        </div>
      </div>

      {error && <ErrorBox msg={error} />}

      {/* Expanded section */}
      {expanded && (
        <div className="p-4 border-t border-outline-variant bg-surface space-y-4">
          <p className="font-body-sm text-on-surface-variant">{chair.short_description}</p>

          {/* ArXiv ingest */}
          <div>
            <h5 className="font-label-md text-on-surface uppercase tracking-wider text-[11px] mb-2">
              Paper hinzufügen
            </h5>
            <ArxivForm chairId={chair.id} onAdded={() => onRefresh(chair.id)} />
          </div>

          {/* Paper list */}
          {papers.length > 0 && (
            <div>
              <h5 className="font-label-md text-on-surface uppercase tracking-wider text-[11px] mb-2">
                Gespeicherte Papers
              </h5>
              <div className="space-y-2">
                {papers.map((doc) => (
                  <div key={doc.id} className="flex items-start gap-3 bg-surface-container-low rounded-lg p-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-body-sm text-on-surface font-medium line-clamp-1">
                        {doc.title ?? doc.arxiv_id ?? "Paper"}
                      </p>
                      <p className="font-label-md text-[11px] text-on-surface-variant">
                        {doc.arxiv_id && `arXiv:${doc.arxiv_id}`}
                        {doc.published_year && ` · ${doc.published_year}`}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteDoc(doc.id)}
                      className="p-1 rounded hover:bg-error-container transition-colors text-error shrink-0"
                      title="Paper entfernen"
                    >
                      <span className="material-symbols-outlined text-[16px]">close</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Chairs tab ───────────────────────────────────────────────────────────────

function ChairsTab() {
  const [chairs, setChairs] = useState<Chair[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    listChairs()
      .then(setChairs)
      .catch((e) => setError(e instanceof Error ? e.message : "Fehler"))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function refreshChair(_id: number) {
    load();
  }

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  return (
    <div className="space-y-4">
      <CreateChairForm onCreated={(c) => setChairs((prev) => [c, ...prev])} />
      {chairs.length === 0 ? (
        <p className="text-center py-12 font-body-md text-on-surface-variant">
          Noch keine Lehrstühle angelegt.
        </p>
      ) : (
        chairs.map((chair) => (
          <ChairRow
            key={chair.id}
            chair={chair}
            onDeleted={(id) => setChairs((prev) => prev.filter((c) => c.id !== id))}
            onRefresh={refreshChair}
          />
        ))
      )}
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const inputCls =
  "w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface font-body-sm text-body-sm text-on-surface outline-none focus:border-primary transition-colors";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block font-label-md text-label-md text-on-surface-variant mb-1">{label}</label>
      {children}
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex justify-center py-16">
      <div className="w-8 h-8 border-2 border-outline-variant border-t-primary rounded-full animate-spin" />
    </div>
  );
}

function ErrorBox({ msg }: { msg: string }) {
  return (
    <div className="bg-error-container text-on-error-container rounded-lg px-4 py-3 font-body-sm">
      {msg}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Admin() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("users");

  if (user?.role !== "admin") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="font-body-lg text-on-surface-variant">Nur für Admins.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <TopBar title="Admin" showSearch={false} />

      <div className="flex-1 p-4 md:p-margin-desktop">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-headline-lg text-headline-lg text-on-surface mb-6">
            Administration
          </h2>

          {/* Tabs */}
          <div className="flex gap-1 mb-6 border-b border-outline-variant">
            {(["users", "chairs"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-5 py-2.5 font-label-md text-label-md transition-colors border-b-2 -mb-px ${
                  tab === t
                    ? "border-primary text-primary"
                    : "border-transparent text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {t === "users" ? "Benutzer" : "Lehrstühle"}
              </button>
            ))}
          </div>

          {tab === "users" && <UsersTab />}
          {tab === "chairs" && <ChairsTab />}
        </div>
      </div>
    </div>
  );
}
