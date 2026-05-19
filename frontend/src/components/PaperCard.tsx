import AiInsightSnippet from "./AiInsightSnippet";

export interface Paper {
  id: string;
  category: string; // e.g. "ArXiv • CS.AI"
  title: string;
  abstract: string;
  authors?: string;
  daysAgo?: number;
  aiInsight?: string;
}

export default function PaperCard({ paper }: { paper: Paper }) {
  return (
    <div className="bg-surface-container-lowest rounded-xl border border-outline-variant p-stack-md hover:shadow-[0px_4px_20px_rgba(26,54,93,0.08)] transition-all cursor-pointer group">
      <div className="flex justify-between items-start mb-unit">
        <span className="font-label-md text-[10px] bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded-full uppercase tracking-widest">
          {paper.category}
        </span>
        <button className="text-outline hover:text-primary transition-colors opacity-0 group-hover:opacity-100">
          <span className="material-symbols-outlined text-[18px]">bookmark_add</span>
        </button>
      </div>

      <h4 className="font-title-lg text-[16px] leading-snug text-on-surface font-semibold mb-2 group-hover:text-primary transition-colors">
        {paper.title}
      </h4>

      <p className="font-body-sm text-body-sm text-on-surface-variant mb-stack-md line-clamp-2">
        {paper.abstract}
      </p>

      {paper.aiInsight && <AiInsightSnippet text={paper.aiInsight} />}

      {paper.authors && (
        <div className="flex items-center gap-2 mt-3 pt-2 border-t border-outline-variant">
          <div className="flex -space-x-2">
            <div className="w-6 h-6 rounded-full bg-surface-variant border-2 border-surface-container-lowest" />
            <div className="w-6 h-6 rounded-full bg-surface-dim border-2 border-surface-container-lowest" />
          </div>
          <span className="font-label-md text-[11px] text-on-surface-variant">
            {paper.authors}
            {paper.daysAgo !== undefined &&
              ` • ${paper.daysAgo === 0 ? "today" : paper.daysAgo === 1 ? "yesterday" : `${paper.daysAgo} days ago`}`}
          </span>
        </div>
      )}
    </div>
  );
}
