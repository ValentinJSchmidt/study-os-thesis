import { useState } from "react";
import TopBar from "../components/TopBar";
import StatCard from "../components/StatCard";
import SkillBar from "../components/SkillBar";
import SkillRadar from "../components/SkillRadar";
import { useAuth } from "../auth/AuthContext";

const SKILL_BARS = [
  { label: "Data Science", percent: 85 },
  { label: "Maschinelles Lernen", percent: 72 },
  { label: "Theoretische Informatik", percent: 90 },
  { label: "Software Engineering", percent: 65 },
];

export default function Dashboard() {
  const { user } = useAuth();
  const [transcriptUploaded, setTranscriptUploaded] = useState(false);
  const [dragging, setDragging] = useState(false);

  const firstName = user?.email?.split("@")[0] ?? "Student";

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    setTranscriptUploaded(true);
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <TopBar showSearch />

      <div className="flex-1 overflow-y-auto p-4 md:p-margin-desktop">
        <div className="max-w-container-max mx-auto">
          {/* Hero */}
          <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h2 className="font-display-lg text-display-lg text-primary tracking-tight max-w-3xl leading-tight">
                Willkommen zurück, {firstName}.
                <span className="text-on-surface-variant font-headline-lg text-headline-lg mt-2 block font-normal">
                  Bereit für dein nächstes Forschungsprojekt?
                </span>
              </h2>
            </div>
            <div className="flex items-center gap-2 bg-surface-container-low border border-outline-variant rounded-full px-4 py-2 shrink-0">
              <span
                className="material-symbols-outlined text-tertiary-container text-[20px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                auto_awesome
              </span>
              <span className="font-label-md text-label-md text-on-surface">
                AI Engine Online
              </span>
            </div>
          </div>

          {/* Bento Grid: upload + stats */}
          <div className="grid grid-cols-12 gap-gutter mb-8">
            {/* Upload Area — col 8 */}
            <div className="col-span-12 md:col-span-8 flex flex-col">
              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => setTranscriptUploaded(true)}
                className={`bg-surface-container-lowest border-2 rounded-xl p-8 flex-1 flex flex-col items-center justify-center text-center relative overflow-hidden ambient-shadow group cursor-pointer transition-all
                  ${dragging
                    ? "border-primary bg-surface-container-low/60"
                    : "border-dashed border-outline-variant hover:border-primary/50 hover:bg-surface-container-low/60"
                  }
                  ${transcriptUploaded ? "border-solid border-tertiary-container/40 bg-tertiary-fixed/10" : ""}
                `}
              >
                {/* Decorative blob */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-primary-fixed/20 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

                {transcriptUploaded ? (
                  <>
                    <div className="w-16 h-16 rounded-full bg-tertiary-container/20 flex items-center justify-center mb-6 text-tertiary-container relative z-10">
                      <span className="material-symbols-outlined text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                        check_circle
                      </span>
                    </div>
                    <h3 className="font-title-lg text-title-lg text-on-surface font-semibold mb-2 relative z-10">
                      Transcript erfolgreich hochgeladen
                    </h3>
                    <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md mb-6 relative z-10">
                      Deine KI-Analyse ist abgeschlossen. Dein Kompetenzprofil wurde aktualisiert.
                    </p>
                    <button
                      onClick={(e) => { e.stopPropagation(); setTranscriptUploaded(false); }}
                      className="bg-surface border border-outline-variant text-primary font-label-md text-label-md py-2.5 px-6 rounded-lg flex items-center gap-2 hover:bg-surface-container-high transition-colors relative z-10 shadow-sm"
                    >
                      <span className="material-symbols-outlined text-[18px]">refresh</span>
                      Neues Transcript laden
                    </button>
                  </>
                ) : (
                  <>
                    <div className="w-16 h-16 rounded-full bg-primary-container/10 flex items-center justify-center mb-6 text-primary relative z-10 group-hover:scale-110 transition-transform duration-300">
                      <span className="material-symbols-outlined text-[32px]">upload_file</span>
                    </div>
                    <h3 className="font-title-lg text-title-lg text-on-surface font-semibold mb-2 relative z-10">
                      Transcript of Records hochladen
                    </h3>
                    <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md mb-6 relative z-10">
                      Ziehe dein PDF-Dokument hierher oder klicke, um eine Datei auszuwählen.
                      Unsere AI analysiert deine akademische Historie in Sekunden.
                    </p>
                    <button className="bg-surface border border-outline-variant text-primary font-label-md text-label-md py-2.5 px-6 rounded-lg flex items-center gap-2 hover:bg-surface-container-high transition-colors relative z-10 shadow-sm">
                      <span className="material-symbols-outlined text-[18px]">folder_open</span>
                      Datei auswählen
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Quick Stats — col 4 */}
            <div className="col-span-12 md:col-span-4 flex flex-col gap-6">
              {/* GPA Card */}
              <StatCard
                label="Aktueller Notendurchschnitt"
                value="1.4"
                unit="GPA"
                icon="grade"
                badge={
                  <div className="flex items-center gap-1 text-tertiary-container font-label-md text-label-md bg-tertiary-fixed/20 w-fit px-2 py-1 rounded">
                    <span className="material-symbols-outlined text-[14px]">trending_up</span>
                    Top 12% im Jahrgang
                  </div>
                }
              />

              {/* Credits Card */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 ambient-shadow flex-1 flex flex-col justify-between">
                <div>
                  <h4 className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider mb-4">
                    Akademischer Fortschritt
                  </h4>
                  <div className="flex justify-between items-end mb-4 border-b border-outline-variant/30 pb-4">
                    <div>
                      <span className="block font-headline-md text-headline-md text-on-surface font-semibold">
                        124
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Credits (ECTS)
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="block font-headline-md text-headline-md text-on-surface font-semibold">
                        28
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Analysierte Kurse
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <div className="w-2 h-2 rounded-full bg-tertiary-container animate-pulse" />
                  <span className="font-label-md text-label-md text-on-surface-variant">
                    {transcriptUploaded ? "Profil aktualisiert" : "Wartet auf neues Transcript"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Skill Analysis Section */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-title-lg text-title-lg text-primary font-semibold flex items-center gap-2">
                <span className="material-symbols-outlined">radar</span>
                Kompetenzprofil
              </h3>
              <span className="bg-surface-container border border-outline-variant text-on-surface-variant font-label-md text-label-md px-3 py-1 rounded-full flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
                AI Generiert
              </span>
            </div>

            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 md:p-8 ambient-shadow relative">
              {/* Lock overlay — shown before upload */}
              {!transcriptUploaded && (
                <div className="absolute inset-0 glass-panel z-20 flex flex-col items-center justify-center rounded-xl">
                  <span className="material-symbols-outlined text-[48px] text-primary/40 mb-4">
                    lock
                  </span>
                  <h4 className="font-headline-md text-headline-md text-primary mb-2 text-center">
                    Profil noch unvollständig
                  </h4>
                  <p className="font-body-md text-body-md text-on-surface-variant max-w-md text-center">
                    Lade dein aktuelles Transcript of Records hoch, um deine
                    detaillierte Kompetenzanalyse und KI-gestützte
                    Forschungsvorschläge freizuschalten.
                  </p>
                </div>
              )}

              {/* Underlying content (blurred until upload) */}
              <div className={transcriptUploaded ? "" : "opacity-40 pointer-events-none"}>
                {/* Tab selector for chart type */}
                <div className="flex gap-2 mb-6">
                  <button className="font-label-md text-label-md px-4 py-1.5 rounded-full bg-primary text-on-primary">
                    Radar Chart
                  </button>
                  <button className="font-label-md text-label-md px-4 py-1.5 rounded-full border border-outline-variant text-on-surface-variant hover:bg-surface-container-high transition-colors">
                    Skill Bars
                  </button>
                </div>

                <SkillRadar />

                {/* Skill bars below radar */}
                <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {SKILL_BARS.map((s) => (
                    <SkillBar key={s.label} label={s.label} percent={s.percent} />
                  ))}
                </div>

                {/* AI Insight */}
                <div className="mt-6 bg-surface-container border border-outline-variant/50 rounded-lg p-6">
                  <h4 className="font-title-lg text-title-lg text-primary mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-tertiary-container">
                      lightbulb
                    </span>
                    AI Insight
                  </h4>
                  <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                    Basierend auf den bisherigen Kursen zeigt sich eine starke
                    Tendenz zur theoretischen Fundierung (90%) kombiniert mit
                    exzellenten methodischen Fähigkeiten in Data Science (85%).
                    Ein ideales Profil für Forschung im Bereich erklärbarer KI
                    (XAI) oder algorithmischer Spieltheorie.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
