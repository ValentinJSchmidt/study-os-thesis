import { useEffect, useRef, useState } from "react";
import TopBar from "../components/TopBar";
import StatCard from "../components/StatCard";
import SkillBar from "../components/SkillBar";
import SkillRadar, { coursesToRadarData } from "../components/SkillRadar";
import { useAuth } from "../auth/AuthContext";
import { getStudentProfile, uploadTranscript, type StudentProfile } from "../api/students";

// Fixed skill-bar labels mapped from radar axes
const SKILL_BAR_AXES = [
  "Programming",
  "Statistics",
  "Databases",
  "Projects",
  "Web",
  "Versioning",
] as const;

export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.email?.split("@")[0] ?? "User";

  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setProfileLoading(true);
    getStudentProfile()
      .then(setProfile)
      .catch(() => setProfile(null)) // 404 = no profile yet
      .finally(() => setProfileLoading(false));
  }, []);

  async function handleFile(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Bitte nur PDF-Dateien hochladen.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    try {
      const updated = await uploadTranscript(file, profile?.program ?? undefined, profile?.semester ?? undefined);
      setProfile(updated);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload fehlgeschlagen.");
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  const hasProfile = profile !== null && !profileLoading;
  const radarData = hasProfile ? coursesToRadarData(profile.courses) : undefined;
  const totalCredits = hasProfile
    ? profile.courses.reduce((s, c) => s + (c.credits ?? 0), 0)
    : null;

  // Derive skill bars from radar data (same axes, percent = score/4 * 100)
  const skillBars = radarData
    ? SKILL_BAR_AXES.map((label, i) => ({
        label,
        percent: Math.round((radarData[i] / 4) * 100),
      }))
    : null;

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
              <span className="font-label-md text-label-md text-on-surface">AI Engine Online</span>
            </div>
          </div>

          {/* Bento Grid: upload + stats */}
          <div className="grid grid-cols-12 gap-gutter mb-8">
              {/* Upload Area */}
              <div className="col-span-12 md:col-span-8 flex flex-col">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  className="hidden"
                  onChange={handleInputChange}
                />
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => !uploading && fileInputRef.current?.click()}
                  className={`bg-surface-container-lowest border-2 rounded-xl p-8 flex-1 flex flex-col items-center justify-center text-center relative overflow-hidden ambient-shadow group cursor-pointer transition-all
                    ${dragging ? "border-primary bg-surface-container-low/60" : "border-dashed border-outline-variant hover:border-primary/50 hover:bg-surface-container-low/60"}
                    ${hasProfile ? "border-solid border-tertiary-container/40 bg-tertiary-fixed/10" : ""}
                  `}
                >
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-primary-fixed/20 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

                  {uploading ? (
                    <>
                      <div className="w-16 h-16 rounded-full bg-primary-container/10 flex items-center justify-center mb-6 text-primary relative z-10">
                        <div className="w-8 h-8 border-2 border-outline-variant border-t-primary rounded-full animate-spin" />
                      </div>
                      <h3 className="font-title-lg text-title-lg text-on-surface font-semibold mb-2 relative z-10">
                        Analysiere Transcript…
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md relative z-10">
                        Die KI extrahiert deine Kurse und berechnet dein Kompetenzprofil.
                      </p>
                    </>
                  ) : hasProfile ? (
                    <>
                      <div className="w-16 h-16 rounded-full bg-tertiary-container/20 flex items-center justify-center mb-6 text-tertiary-container relative z-10">
                        <span className="material-symbols-outlined text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                          check_circle
                        </span>
                      </div>
                      <h3 className="font-title-lg text-title-lg text-on-surface font-semibold mb-2 relative z-10">
                        Transcript erfolgreich hochgeladen
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md mb-1 relative z-10">
                        {profile.program && `${profile.program}${profile.semester ? ` · Semester ${profile.semester}` : ""} · `}
                        Zuletzt aktualisiert: {new Date(profile.updated_at).toLocaleDateString("de-DE")}
                      </p>
                      <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md mb-6 relative z-10">
                        Klicke, um ein neues Transcript hochzuladen.
                      </p>
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

                  {uploadError && (
                    <p className="mt-4 font-body-sm text-body-sm text-error relative z-10">
                      {uploadError}
                    </p>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="col-span-12 md:col-span-4 flex flex-col gap-6">
                <StatCard
                  label="Aktueller Notendurchschnitt"
                  value={profileLoading ? "…" : profile?.gpa != null ? profile.gpa.toFixed(2) : "–"}
                  unit="GPA"
                  icon="grade"
                  badge={
                    profile?.gpa != null ? (
                      <div className="flex items-center gap-1 text-tertiary-container font-label-md text-label-md bg-tertiary-fixed/20 w-fit px-2 py-1 rounded">
                        <span className="material-symbols-outlined text-[14px]">grade</span>
                        Deutsch: {profile.gpa.toFixed(2)}
                      </div>
                    ) : undefined
                  }
                />

                <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 ambient-shadow flex-1 flex flex-col justify-between">
                  <div>
                    <h4 className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider mb-4">
                      Akademischer Fortschritt
                    </h4>
                    <div className="flex justify-between items-end mb-4 border-b border-outline-variant/30 pb-4">
                      <div>
                        <span className="block font-headline-md text-headline-md text-on-surface font-semibold">
                          {profileLoading ? "…" : totalCredits != null ? Math.round(totalCredits) : "–"}
                        </span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant">Credits (ECTS)</span>
                      </div>
                      <div className="text-right">
                        <span className="block font-headline-md text-headline-md text-on-surface font-semibold">
                          {profileLoading ? "…" : profile ? profile.courses.length : "–"}
                        </span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant">Kurse</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <div className={`w-2 h-2 rounded-full ${hasProfile ? "bg-tertiary-container" : "bg-outline-variant"} animate-pulse`} />
                    <span className="font-label-md text-label-md text-on-surface-variant">
                      {profileLoading ? "Lädt…" : hasProfile ? "Profil aktualisiert" : "Wartet auf Transcript"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

          {/* Skill Analysis */}
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
              {/* Lock overlay — shown before any profile */}
              {!hasProfile && !profileLoading && (
                <div className="absolute inset-0 glass-panel z-20 flex flex-col items-center justify-center rounded-xl">
                  <span className="material-symbols-outlined text-[48px] text-primary/40 mb-4">lock</span>
                  <h4 className="font-headline-md text-headline-md text-primary mb-2 text-center">
                    Profil noch unvollständig
                  </h4>
                  <p className="font-body-md text-body-md text-on-surface-variant max-w-md text-center">
                    Lade dein aktuelles Transcript of Records hoch, um deine detaillierte
                    Kompetenzanalyse freizuschalten.
                  </p>
                </div>
              )}

              <div className={!hasProfile && !profileLoading ? "opacity-40 pointer-events-none" : ""}>
                <SkillRadar currentData={radarData} />

                {skillBars && (
                  <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {skillBars.map((s) => (
                      <SkillBar key={s.label} label={s.label} percent={s.percent} />
                    ))}
                  </div>
                )}

                {hasProfile && profile.courses.length > 0 && (
                  <div className="mt-6 bg-surface-container border border-outline-variant/50 rounded-lg p-6">
                    <h4 className="font-title-lg text-title-lg text-primary mb-4 flex items-center gap-2">
                      <span className="material-symbols-outlined text-tertiary-container">lightbulb</span>
                      Kurse aus deinem Transcript
                    </h4>
                    <div className="max-h-48 overflow-y-auto space-y-1">
                      {profile.courses.map((c) => (
                        <div key={c.id} className="flex items-center justify-between py-1 border-b border-outline-variant/20 last:border-0">
                          <span className="font-body-sm text-body-sm text-on-surface">{c.course_name}</span>
                          <div className="flex items-center gap-3 shrink-0 ml-4">
                            {c.credits != null && (
                              <span className="font-label-md text-label-md text-on-surface-variant">{c.credits} ECTS</span>
                            )}
                            {c.grade && (
                              <span className="font-label-md text-label-md text-primary font-semibold">{c.grade}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
