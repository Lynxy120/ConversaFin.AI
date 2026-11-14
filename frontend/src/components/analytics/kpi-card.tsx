import { TrendingDown, TrendingUp, type LucideIcon } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/cn";

export function KpiCard({
  label,
  value,
  sub,
  delta,
  icon: Icon,
}: {
  label: string;
  value: string;
  sub?: string;
  delta?: number | null;
  icon: LucideIcon;
}) {
  const up = (delta ?? 0) >= 0;
  return (
    <GlassCard className="flex flex-col justify-between gap-3 p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted">{label}</p>
        <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
          <Icon size={18} />
        </span>
      </div>
      <p className="truncate text-xl font-extrabold tracking-tight tabular-nums sm:text-2xl">
        {value}
      </p>
      {delta !== undefined &&
        (delta === null ? (
          <p className="text-xs text-muted">No prior period to compare</p>
        ) : (
          <p
            className={cn(
              "flex items-center gap-1 text-xs font-semibold",
              up ? "text-success" : "text-danger",
            )}
          >
            {up ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {up ? "+" : ""}
            {delta.toFixed(1)}%{" "}
            <span className="font-medium text-muted">vs previous</span>
          </p>
        ))}
      {sub && delta === undefined && (
        <p className="text-xs text-muted">{sub}</p>
      )}
    </GlassCard>
  );
}
