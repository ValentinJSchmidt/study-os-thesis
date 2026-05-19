/** Small pill badge: "AI-Generated", "Smart Match", etc. */
export default function AiInsightChip({ label = "AI Generiert" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full ai-purple-bg ai-purple-text font-label-md text-[10px]">
      <span className="material-symbols-outlined text-[12px]">auto_awesome</span>
      {label}
    </span>
  );
}
