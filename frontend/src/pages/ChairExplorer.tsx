import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "../components/TopBar";
import AiInsightChip from "../components/AiInsightChip";
import AiInsightSnippet from "../components/AiInsightSnippet";

interface Chair {
  id: string;
  faculty: string;
  name: string;
  professor: string;
  matchScore: number;
  tags: string[];
  description: string;
  aiInsight?: string;
  openTopics?: number;
  featured?: boolean;
}

const MOCK_CHAIRS: Chair[] = [
  {
    id: "ml",
    faculty: "Informatics",
    name: "Lehrstuhl für Maschinelles Lernen",
    professor: "Prof. Dr. Elena Rodriguez",
    matchScore: 98,
    tags: ["Deep Learning", "NLP", "Computer Vision", "+2 more"],
    description:
      "Forschungsschwerpunkte liegen in Deep Learning, Natural Language Processing und Computer Vision mit starkem Fokus auf erklärbare KI.",
    aiInsight:
      'Based on your exceptional grades in "Advanced Algorithms" (1.0) and "Statistical Methods" (1.3), this chair offers an optimal environment for your thesis. They are currently seeking students for NLP projects.',
    openTopics: 12,
    featured: true,
  },
  {
    id: "da",
    faculty: "Data Science",
    name: "Data Engineering & Analytics",
    professor: "Prof. Dr. M. Weber",
    matchScore: 85,
    tags: ["Big Data", "Distributed Systems", "Data Mining"],
    description:
      "Focuses on scalable architectures for processing massive datasets in real-time environments.",
  },
  {
    id: "robotics",
    faculty: "Robotics",
    name: "Autonome Systeme",
    professor: "Prof. Dr. K. Schmidt",
    matchScore: 72,
    tags: ["Reinforcement Learning", "Kinematics", "Control Theory"],
    description:
      "Researching adaptive control mechanisms for autonomous drones and ground vehicles.",
  },
  {
    id: "theory",
    faculty: "Informatics",
    name: "Theoretische Informatik",
    professor: "Prof. Dr. A. Hoffmann",
    matchScore: 68,
    tags: ["Algorithmic Game Theory", "Complexity Theory", "Formal Methods"],
    description:
      "Exploring the boundaries of computability and the mathematical foundations of computer science.",
  },
  {
    id: "hci",
    faculty: "Human-Computer Interaction",
    name: "Mensch-Maschine Interaktion",
    professor: "Prof. Dr. S. Bauer",
    matchScore: 61,
    tags: ["UX Research", "Accessibility", "Cognitive Load"],
    description:
      "Studies how humans interact with intelligent systems and how to design for cognitive efficiency.",
  },
];

function MatchCircle({ score, size = "lg" }: { score: number; size?: "sm" | "lg" }) {
  const dim = size === "lg" ? 64 : 44;
  const r = 15.9155;
  const circumference = 2 * Math.PI * r;
  const dash = (score / 100) * circumference;
  const isHigh = score >= 90;

  return (
    <div className="flex flex-col items-end">
      <div
        className="rounded-full border-4 border-surface-container flex items-center justify-center relative bg-surface"
        style={{ width: dim, height: dim }}
      >
        <svg
          className="absolute inset-0 w-full h-full -rotate-90"
          viewBox="0 0 36 36"
        >
          <path
            className="text-surface-variant"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="currentColor"
            strokeDasharray={`${circumference}, ${circumference}`}
            strokeWidth="3"
          />
          <path
            style={{ color: isHigh ? "#4cadab" : "#455f88" }}
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="currentColor"
            strokeDasharray={`${dash}, ${circumference}`}
            strokeWidth="3"
          />
        </svg>
        <span
          className="font-headline-md text-headline-md font-bold"
          style={{
            color: isHigh ? "#4cadab" : "#455f88",
            fontSize: size === "sm" ? 12 : 16,
          }}
        >
          {score}
          <span style={{ fontSize: size === "sm" ? 8 : 12 }}>%</span>
        </span>
      </div>
      <span className="font-label-md text-label-md text-on-surface-variant mt-1 text-right">
        Match Score
      </span>
    </div>
  );
}

export default function ChairExplorer() {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const filtered = MOCK_CHAIRS.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.professor.toLowerCase().includes(search.toLowerCase()) ||
      c.faculty.toLowerCase().includes(search.toLowerCase()),
  );

  const featured = filtered.find((c) => c.featured);
  const rest = filtered.filter((c) => !c.featured);

  function goToProposals() {
    navigate("/proposals");
  }

  return (
    <div className="flex flex-col min-h-screen bg-surface-bright">
      <TopBar title="Lehrstuhl-Explorer" showSearch={false} />

      <main className="flex-1 overflow-y-auto p-4 md:p-margin-desktop">
        <div className="max-w-container-max mx-auto space-y-stack-lg">
          {/* Page header */}
          <section className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
              <h2 className="font-display-lg text-display-lg text-on-surface mb-2">
                Find Your Academic Match
              </h2>
              <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl">
                Discover research groups that align perfectly with your academic
                record and interests. Our AI analyzes your transcript to
                calculate match scores.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">
                  search
                </span>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search departments..."
                  className="pl-10 pr-4 py-2 rounded-full border border-outline-variant bg-surface-container-lowest font-label-md text-label-md text-on-surface outline-none focus:border-primary w-64 transition-all"
                />
              </div>
              <button className="px-4 py-2 rounded-full border border-outline-variant bg-surface-container-lowest font-label-md text-label-md text-on-surface flex items-center gap-2 hover:bg-surface-container-low transition-colors">
                <span className="material-symbols-outlined text-sm">tune</span>
                Filters
              </button>
            </div>
          </section>

          {/* Active filter chips */}
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-surface-container border border-outline-variant text-body-sm font-body-sm text-on-surface">
              Faculty: Informatics
              <span className="material-symbols-outlined text-xs cursor-pointer hover:text-error ml-1">
                close
              </span>
            </span>
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-fixed border border-primary-fixed-dim text-body-sm font-body-sm text-on-primary-fixed-variant">
              AI Matched
              <span className="material-symbols-outlined text-xs cursor-pointer hover:text-primary ml-1">
                close
              </span>
            </span>
            <button className="text-body-sm font-body-sm text-primary hover:underline px-2">
              Clear all
            </button>
          </div>

          {/* Bento grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-gutter">
            {/* Featured card — spans 2 cols */}
            {featured && (
              <article className="col-span-1 lg:col-span-2 xl:col-span-2 bg-surface-container-lowest rounded-xl border border-outline-variant p-6 hover-lift flex flex-col relative overflow-hidden group">
                {/* Decorative blob */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-tertiary-fixed opacity-10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:opacity-20 transition-opacity" />

                <div className="relative z-10 flex flex-col md:flex-row justify-between items-start gap-4 mb-6">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 rounded-md bg-secondary-container text-on-secondary-fixed-variant font-label-md text-[10px] uppercase tracking-wider">
                        {featured.faculty}
                      </span>
                      <AiInsightChip label="Smart Match" />
                    </div>
                    <h3 className="font-headline-md text-headline-md text-on-surface mb-1">
                      {featured.name}
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant flex items-center gap-2">
                      <span className="material-symbols-outlined text-sm">person</span>
                      {featured.professor}
                    </p>
                  </div>
                  <MatchCircle score={featured.matchScore} />
                </div>

                <div className="relative z-10 space-y-4">
                  {featured.aiInsight && (
                    <div className="p-4 rounded-lg ai-purple-bg/40 border ai-purple-border flex gap-3">
                      <span className="material-symbols-outlined ai-purple-text mt-0.5">
                        lightbulb
                      </span>
                      <p className="font-body-sm text-body-sm ai-purple-text-dark">
                        <strong>AI Insight:</strong> {featured.aiInsight}
                      </p>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2">
                    {featured.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 rounded-full border border-outline-variant bg-surface font-body-sm text-body-sm text-on-surface-variant"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between border-t border-outline-variant pt-4">
                    {featured.openTopics && (
                      <span className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1">
                        <span className="material-symbols-outlined text-sm">groups</span>
                        {featured.openTopics} Open Topics
                      </span>
                    )}
                    <button
                      onClick={goToProposals}
                      className="bg-primary text-on-primary px-5 py-2 rounded-lg font-label-md text-label-md flex items-center gap-2 hover:bg-primary-container transition-colors shadow-sm"
                    >
                      <span className="material-symbols-outlined text-sm">description</span>
                      Proposals generieren
                    </button>
                  </div>
                </div>
              </article>
            )}

            {/* Standard cards */}
            {rest.map((chair) => (
              <article
                key={chair.id}
                className="bg-surface-container-lowest rounded-xl border border-outline-variant p-6 hover-lift flex flex-col"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="px-2 py-0.5 rounded-md bg-secondary-container text-on-secondary-fixed-variant font-label-md text-[10px] uppercase tracking-wider mb-2 inline-block">
                      {chair.faculty}
                    </span>
                    <h3 className="font-title-lg text-title-lg text-on-surface mb-1 leading-tight">
                      {chair.name}
                    </h3>
                    <p className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-xs">person</span>
                      {chair.professor}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 bg-surface-container px-2 py-1 rounded-md">
                    <span className="material-symbols-outlined text-primary text-sm">
                      check_circle
                    </span>
                    <span className="font-label-md text-label-md text-on-surface">
                      {chair.matchScore}%
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1.5 mb-4">
                  {chair.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 rounded-md bg-surface border border-outline-variant font-body-sm text-[11px] text-on-surface-variant"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {chair.aiInsight && (
                  <div className="mb-4">
                    <AiInsightSnippet text={chair.aiInsight} />
                  </div>
                )}

                <p className="font-body-sm text-body-sm text-on-surface-variant mb-4 line-clamp-2 flex-1">
                  {chair.description}
                </p>

                <div className="border-t border-outline-variant pt-4 mt-auto">
                  <button
                    onClick={goToProposals}
                    className="w-full bg-transparent border border-primary text-primary px-4 py-2 rounded-lg font-label-md text-label-md flex items-center justify-center gap-2 hover:bg-surface-container transition-colors"
                  >
                    <span className="material-symbols-outlined text-sm">description</span>
                    Proposals generieren
                  </button>
                </div>
              </article>
            ))}
          </div>

          {/* Load more */}
          <div className="flex justify-center pt-8 pb-12">
            <button className="px-6 py-2 rounded-full border border-outline-variant bg-surface-container-lowest font-label-md text-label-md text-on-surface hover:bg-surface-container-low transition-colors">
              Load More Chairs
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
