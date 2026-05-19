/** Purple AI insight panel used inside cards and chat */
export default function AiInsightSnippet({ text }: { text: string }) {
  return (
    <div className="ai-purple-bg rounded-lg p-3 border ai-purple-border">
      <div className="flex items-center gap-1 mb-1">
        <span className="material-symbols-outlined text-[14px] ai-purple-text">
          auto_awesome
        </span>
        <span className="font-label-md text-[11px] ai-purple-text">AI Insight</span>
      </div>
      <p className="font-body-sm text-[12px] ai-purple-text-dark leading-tight">{text}</p>
    </div>
  );
}
