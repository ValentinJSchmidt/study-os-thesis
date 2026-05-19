import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: string;
  badge?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export default function StatCard({
  label,
  value,
  unit,
  icon,
  badge,
  children,
  className = "",
}: StatCardProps) {
  return (
    <div
      className={`bg-surface-container-lowest border border-outline-variant rounded-xl p-6 ambient-shadow relative overflow-hidden ${className}`}
    >
      {icon && (
        <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
          <span className="material-symbols-outlined text-[64px]">{icon}</span>
        </div>
      )}
      <h4 className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider mb-2">
        {label}
      </h4>
      <div className="flex items-baseline gap-2">
        <span className="font-display-lg text-display-lg text-primary font-bold">
          {value}
        </span>
        {unit && (
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            {unit}
          </span>
        )}
      </div>
      {badge && <div className="mt-4">{badge}</div>}
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}
