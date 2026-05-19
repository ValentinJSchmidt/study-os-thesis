interface SkillBarProps {
  label: string;
  percent: number; // 0–100
}

export default function SkillBar({ label, percent }: SkillBarProps) {
  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="font-label-md text-label-md text-on-surface">{label}</span>
        <span className="font-label-md text-label-md text-primary">{percent}%</span>
      </div>
      <div className="w-full bg-surface-container-highest rounded-full h-2.5">
        <div
          className="chart-bar-fill h-2.5 rounded-full"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
