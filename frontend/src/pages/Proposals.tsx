import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import TopBar from "../components/TopBar";
import { listTheses, listMyProposals, type Thesis, type ThesisDifficulty, type SkillsRequired } from "../api/theses";
import { listChairs, type Chair } from "../api/chairs";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

const DIFFICULTY_CONFIG: Record<ThesisDifficulty, { label: string; className: string }> = {
  bachelor: { label: "Bachelor", className: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  master:   { label: "Master",   className: "bg-blue-100 text-blue-700 border-blue-200" },
  phd:      { label: "PhD",      className: "bg-purple-100 text-purple-700 border-purple-200" },
};

const SOURCE_CONFIG = {
  professor: { label: "Professor",  className: "bg-primary-fixed/20 text-primary" },
  student:   { label: "KI-Entwurf", className: "bg-tertiary-container/20 text-tertiary-container" },
  openalex:  { label: "OpenAlex",   className: "bg-secondary-container text-on-secondary-fixed-variant" },
};

function SkillChips({ skills }: { skills: SkillsRequired }) {
  const all: { label: string; cat: string }[] = [
    ...skills.programming.map((s) => ({ label: s, cat: "prog" })),
    ...skills.math.map((s) => ({ label: s, cat: "math" })),
    ...skills.theory.map((s) => ({ label: s, cat: "theory" })),
    ...skills.domain.map((s) => ({ label: s, cat: "domain" })),
    ...skills.other.map((s) => ({ label: s, cat: "other" })),
  ];
  if (all.length === 0) return null;

  const catColors: Record<string, string> = {
    prog:   "bg-blue-50 text-blue-700 border-blue-200",
    math:   "bg-purple-50 text-purple-700 border-purple-200",
    theory: "bg-amber-50 text-amber-700 border-amber-200",
    domain: "bg-emerald-50 text-emerald-700 border-emerald-200",
    other:  "bg-surface-container text-on-surface-variant border-outline-variant",
  };

  return (
    <div className="flex flex-wrap gap-1.5 mt-3">
      {all.map(({ label, cat }, i) => (
        <span
          key={i}
          className={`px-2 py-0.5 rounded-full border text-[10px] font-label-md ${catColors[cat]}`}
        >
          {label}
        </span>
      ))}
    </div>
  );
}

// ─── Unified Proposal Card ────────────────────────────────────────────────────

function ProposalCard({
  thesis,
  chairName,
  featured = false,
}: {
  thesis: Thesis;
  chairName?: string;
  featured?: boolean;
}) {
  const src = SOURCE_CONFIG[thesis.source] ?? SOURCE_CONFIG.student;

  return (
    <article
      className={`bg-surface rounded-xl border border-outline-variant flex flex-col h-full relative overflow-hidden
        hover:shadow-[0px_4px_20px_rgba(26,54,93,0.08)] transition-shadow duration-300
        ${featured ? "lg:col-span-2" : ""}`}
    >
      {/* Decorative blob for featured */}
      {featured && (
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary-container opacity-10 rounded-bl-full -z-10" />
      )}

      <div className="p-stack-md flex flex-col h-full">
        {/* Header row: badges + date */}
        <div className="flex items-start justify-between mb-3 gap-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full font-label-md text-[10px] ${src.className}`}>
              {src.label}
            </span>
            {thesis.difficulty && (
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full border font-label-md text-[10px] ${DIFFICULTY_CONFIG[thesis.difficulty].className}`}>
                {DIFFICULTY_CONFIG[thesis.difficulty].label}
              </span>
            )}
          </div>
          <span className="font-label-md text-label-md text-on-surface-variant text-[11px] shrink-0">
            {formatDate(thesis.created_at)}
          </span>
        </div>

        {/* Title */}
        <h3 className={`font-title-lg text-title-lg text-on-background mb-2 ${featured ? "" : "line-clamp-2"}`}>
          {thesis.title}
        </h3>

        {/* Chair */}
        {chairName && (
          <div className="flex items-center gap-1.5 mb-3">
            <span className="material-symbols-outlined text-on-surface-variant text-[15px]">
              account_balance
            </span>
            <span className="font-label-md text-label-md text-on-surface-variant truncate">
              {chairName}
            </span>
          </div>
        )}

        {/* Abstract */}
        <p className={`font-body-sm text-body-sm text-on-surface-variant flex-1 ${featured ? "line-clamp-4" : "line-clamp-3"}`}>
          {thesis.abstract}
        </p>

        {/* Skills */}
        {thesis.skills_required && (
          <SkillChips skills={thesis.skills_required} />
        )}

        {/* Footer */}
        <div className="flex gap-3 mt-4 pt-3 border-t border-outline-variant/50">
          <button className="flex-1 py-2 px-4 rounded-lg bg-primary text-on-primary font-label-md text-label-md hover:bg-primary-container hover:text-on-primary-container transition-colors text-center">
            Details ansehen
          </button>
        </div>
      </div>
    </article>
  );
}

// ─── Tab content ──────────────────────────────────────────────────────────────

function ProposalGrid({
  theses,
  chairMap,
  emptyText,
}: {
  theses: Thesis[];
  chairMap: Record<number, string>;
  emptyText: string;
}) {
  if (theses.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4 text-on-surface-variant">
        <span className="material-symbols-outlined text-[48px]">description</span>
        <p className="font-body-lg">{emptyText}</p>
      </div>
    );
  }

  const [featured, ...rest] = theses;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
      <ProposalCard
        thesis={featured}
        chairName={featured.chair_id ? chairMap[featured.chair_id] : undefined}
        featured
      />
      {rest.map((t) => (
        <ProposalCard
          key={t.id}
          thesis={t}
          chairName={t.chair_id ? chairMap[t.chair_id] : undefined}
        />
      ))}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

type TabId = "all" | "mine";

export default function Proposals() {
  const [searchParams] = useSearchParams();
  const filterChairId = searchParams.get("chair_id") ? Number(searchParams.get("chair_id")) : null;

  const [tab, setTab] = useState<TabId>("mine");
  const [allTheses, setAllTheses] = useState<Thesis[]>([]);
  const [myProposals, setMyProposals] = useState<Thesis[]>([]);
  const [chairs, setChairs] = useState<Chair[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      listTheses().then(setAllTheses),
      listChairs().then(setChairs),
      listMyProposals().then(setMyProposals),
    ])
      .catch((e) => setError(e instanceof Error ? e.message : "Fehler beim Laden"))
      .finally(() => setLoading(false));
  }, []);

  const chairMap = Object.fromEntries(chairs.map((c) => [c.id, c.name]));

  function filterTheses(list: Thesis[]): Thesis[] {
    return list.filter((t) => {
      const matchesChair = filterChairId == null || t.chair_id === filterChairId;
      const lower = search.toLowerCase();
      const matchesSearch =
        !lower ||
        t.title.toLowerCase().includes(lower) ||
        t.abstract.toLowerCase().includes(lower) ||
        (t.chair_id != null && chairMap[t.chair_id]?.toLowerCase().includes(lower));
      return matchesChair && matchesSearch;
    });
  }

  const activeChairName = filterChairId ? chairMap[filterChairId] : null;

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <TopBar showSearch={false} />

      <main className="flex-1 px-4 md:px-margin-desktop py-stack-lg max-w-container-max mx-auto w-full">
        {/* Header */}
        <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-background mb-1">
              Forschungsvorschläge
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              {activeChairName ? `Gefiltert nach: ${activeChairName}` : "Übersicht aller verfügbaren Themenvorschläge"}
            </p>
          </div>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
              search
            </span>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Vorschläge durchsuchen…"
              className="pl-10 pr-4 py-2 rounded-lg border border-outline-variant bg-surface focus:border-primary font-body-sm text-body-sm text-on-surface w-full md:w-64 transition-all outline-none"
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-outline-variant">
          <button
            onClick={() => setTab("all")}
            className={`px-5 py-2.5 font-label-md text-label-md transition-colors border-b-2 -mb-px ${
              tab === "all"
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            }`}
          >
            Alle Vorschläge
          </button>
          <button
            onClick={() => setTab("mine")}
            className={`px-5 py-2.5 font-label-md text-label-md transition-colors border-b-2 -mb-px flex items-center gap-2 ${
              tab === "mine"
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            }`}
          >
            Meine Vorschläge
            {myProposals.length > 0 && (
              <span className="bg-primary text-on-primary text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {myProposals.length}
              </span>
            )}
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-24">
            <div className="w-10 h-10 border-2 border-outline-variant border-t-primary rounded-full animate-spin" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-error-container text-on-error-container rounded-xl p-6 font-body-md mb-6">
            {error}
          </div>
        )}

        {/* Content */}
        {!loading && !error && tab === "all" && (
          <ProposalGrid
            theses={filterTheses(allTheses)}
            chairMap={chairMap}
            emptyText="Noch keine Vorschläge verfügbar."
          />
        )}

        {!loading && !error && tab === "mine" && (
          <div>
            {myProposals.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 gap-4 text-on-surface-variant text-center">
                <span className="material-symbols-outlined text-[48px]">auto_awesome</span>
                <p className="font-body-lg font-semibold text-on-surface">Noch keine generierten Vorschläge</p>
                <p className="font-body-md max-w-md">
                  Chatte mit dem AI-Assistenten und bitte ihn, Proposals für dich zu generieren.
                  Diese erscheinen dann hier.
                </p>
              </div>
            ) : (
              <ProposalGrid
                theses={filterTheses(myProposals)}
                chairMap={chairMap}
                emptyText="Keine Vorschläge für diesen Filter gefunden."
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
