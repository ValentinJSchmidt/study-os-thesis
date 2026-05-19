import { useState } from "react";
import TopBar from "../components/TopBar";
import AiInsightChip from "../components/AiInsightChip";

interface Proposal {
  id: string;
  title: string;
  chair: string;
  abstract: string;
  date: string;
  isAiDraft: boolean;
  featured?: boolean;
}

const MOCK_PROPOSALS: Proposal[] = [
  {
    id: "1",
    title:
      "Optimierung von Transformer-Modellen für Edge-Devices durch Quantisierung",
    chair: "Lehrstuhl für Künstliche Intelligenz (Prof. Dr. Schmidt)",
    abstract:
      "Dieser Vorschlag untersucht Methoden zur Reduzierung der Inferenzzeit von Large Language Models auf ressourcenbeschränkten Geräten. Der Fokus liegt auf der Entwicklung neuartiger Post-Training-Quantisierungsverfahren, die den Genauigkeitsverlust im Vergleich zu bestehenden Methoden minimieren.",
    date: "Heute, 14:30",
    isAiDraft: true,
    featured: true,
  },
  {
    id: "2",
    title:
      "Ethische Implikationen algorithmischer Entscheidungsfindung im Personalwesen",
    chair: "Lehrstuhl für Wirtschaftsethik",
    abstract:
      "Eine empirische Analyse von Bias in gängigen Recruiting-Algorithmen und Entwicklung eines Rahmenwerks für auditierbare und faire KI-gestützte Auswahlprozesse.",
    date: "Gestern",
    isAiDraft: false,
  },
  {
    id: "3",
    title: "Nachhaltige Lieferketten durch Blockchain-Technologie",
    chair: "Institut für Logistik",
    abstract:
      "Untersuchung der Implementierungsbarrieren von Smart Contracts zur Sicherstellung von Transparenz und ESG-Compliance in globalen textilen Lieferketten.",
    date: "12. Okt 2023",
    isAiDraft: true,
  },
];

export default function Proposals() {
  const [search, setSearch] = useState("");

  const filtered = MOCK_PROPOSALS.filter(
    (p) =>
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.chair.toLowerCase().includes(search.toLowerCase()),
  );

  const featured = filtered.find((p) => p.featured);
  const rest = filtered.filter((p) => !p.featured);

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <TopBar showSearch={false} />

      <main className="flex-1 px-4 md:px-margin-desktop py-stack-lg max-w-container-max mx-auto w-full">
        {/* Page header */}
        <div className="mb-stack-lg flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-background mb-2">
              Deine Forschungsvorschläge
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Verwalte und exportiere deine KI-generierten Exposé-Entwürfe.
            </p>
          </div>
          <div className="flex gap-3">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                search
              </span>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Vorschläge durchsuchen..."
                className="pl-10 pr-4 py-2 rounded-lg border border-outline-variant bg-surface focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm text-on-surface w-full md:w-64 transition-all outline-none"
              />
            </div>
            <button className="p-2 rounded-lg border border-outline-variant text-on-surface-variant hover:bg-surface-container-low transition-colors flex items-center justify-center">
              <span className="material-symbols-outlined">filter_list</span>
            </button>
          </div>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
          {/* Featured card — spans 2 cols */}
          {featured && (
            <article className="bg-surface rounded-xl border border-outline-variant p-stack-md hover:shadow-[0px_4px_20px_rgba(26,54,93,0.08)] transition-shadow duration-300 flex flex-col h-full lg:col-span-2 relative overflow-hidden">
              {/* Decorative corner blob */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary-container opacity-10 rounded-bl-full -z-10" />

              <div className="flex justify-between items-start mb-stack-sm">
                <div className="flex gap-2 items-center">
                  {featured.isAiDraft && <AiInsightChip label="KI-Entwurf" />}
                  <span className="font-label-md text-label-md text-on-surface-variant">
                    {featured.date}
                  </span>
                </div>
                <button className="text-on-surface-variant hover:text-primary transition-colors">
                  <span className="material-symbols-outlined">more_vert</span>
                </button>
              </div>

              <h3 className="font-title-lg text-title-lg text-on-background mb-2">
                {featured.title}
              </h3>

              <div className="flex items-center gap-2 mb-stack-md">
                <span className="material-symbols-outlined text-on-surface-variant text-[16px]">
                  account_balance
                </span>
                <span className="font-label-md text-label-md text-on-surface-variant">
                  {featured.chair}
                </span>
              </div>

              <p className="font-body-sm text-body-sm text-on-surface-variant mb-stack-md flex-1 line-clamp-3">
                {featured.abstract}
              </p>

              <div className="flex gap-3 mt-auto pt-stack-sm border-t border-outline-variant/50">
                <button className="flex-1 py-2 px-4 rounded-lg bg-primary text-on-primary font-label-md text-label-md hover:bg-primary-container hover:text-on-primary-container transition-colors text-center">
                  Details ansehen
                </button>
                <button className="py-2 px-4 rounded-lg border border-primary text-primary font-label-md text-label-md hover:bg-primary-fixed hover:text-on-primary-fixed-variant transition-colors flex items-center justify-center gap-2">
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  PDF
                </button>
              </div>
            </article>
          )}

          {/* Standard cards */}
          {rest.map((proposal) => (
            <ProposalCard key={proposal.id} proposal={proposal} />
          ))}

          {/* Empty state / new proposal card */}
          <button className="bg-surface rounded-xl border-2 border-dashed border-outline-variant p-stack-md flex flex-col items-center justify-center gap-3 hover:border-primary/50 hover:bg-surface-container-low/40 transition-all group min-h-[200px]">
            <div className="w-12 h-12 rounded-full bg-primary-container/10 flex items-center justify-center group-hover:scale-110 transition-transform">
              <span className="material-symbols-outlined text-[24px] text-primary">add</span>
            </div>
            <span className="font-label-md text-label-md text-on-surface-variant group-hover:text-primary transition-colors">
              Neuen Vorschlag erstellen
            </span>
          </button>
        </div>
      </main>
    </div>
  );
}

function ProposalCard({ proposal }: { proposal: Proposal }) {
  return (
    <article className="bg-surface rounded-xl border border-outline-variant p-stack-md hover:shadow-[0px_4px_20px_rgba(26,54,93,0.08)] transition-shadow duration-300 flex flex-col h-full">
      <div className="flex justify-between items-start mb-stack-sm">
        <div className="flex gap-2 items-center">
          {proposal.isAiDraft ? (
            <AiInsightChip label="KI-Entwurf" />
          ) : (
            <span className="inline-flex items-center px-2 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-md text-[10px]">
              Entwurf
            </span>
          )}
          <span className="font-label-md text-label-md text-on-surface-variant">
            {proposal.date}
          </span>
        </div>
      </div>

      <h3 className="font-title-lg text-title-lg text-on-background mb-2 line-clamp-2">
        {proposal.title}
      </h3>

      <div className="flex items-center gap-2 mb-stack-md">
        <span className="material-symbols-outlined text-on-surface-variant text-[16px]">
          account_balance
        </span>
        <span className="font-label-md text-label-md text-on-surface-variant truncate">
          {proposal.chair}
        </span>
      </div>

      <p className="font-body-sm text-body-sm text-on-surface-variant mb-stack-md flex-1 line-clamp-3">
        {proposal.abstract}
      </p>

      <div className="flex gap-3 mt-auto pt-stack-sm border-t border-outline-variant/50">
        <button className="flex-1 py-2 px-4 rounded-lg bg-primary text-on-primary font-label-md text-label-md hover:bg-primary-container hover:text-on-primary-container transition-colors text-center">
          Details
        </button>
        <button className="p-2 rounded-lg border border-outline-variant text-on-surface-variant hover:bg-surface-container-low transition-colors flex items-center justify-center">
          <span className="material-symbols-outlined">download</span>
        </button>
      </div>
    </article>
  );
}
