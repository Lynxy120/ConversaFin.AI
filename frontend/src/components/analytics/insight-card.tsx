"use client";
import { Check, Lightbulb, Sparkles, TriangleAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/cn";
import type { Insight } from "@/lib/types";

const S = {
  high: {
    tone: "danger",
    label: "Act now",
    icon: TriangleAlert,
    chip: "bg-danger/10 text-danger",
  },
  medium: {
    tone: "warning",
    label: "This week",
    icon: TriangleAlert,
    chip: "bg-warning/10 text-warning",
  },
  low: {
    tone: "info",
    label: "Opportunity",
    icon: Lightbulb,
    chip: "bg-primary/10 text-primary",
  },
  positive: {
    tone: "success",
    label: "Working well",
    icon: Sparkles,
    chip: "bg-success/10 text-success",
  },
} as const;

export function InsightCard({
  i,
  done,
  onToggle,
}: {
  i: Insight;
  done: boolean;
  onToggle: () => void;
}) {
  const s = S[i.severity];
  return (
    <GlassCard
      className={cn("flex flex-col gap-3 p-5 transition", done && "opacity-60")}
    >
      <div className="flex items-start gap-3">
        <span
          className={cn(
            "grid size-10 shrink-0 place-items-center rounded-xl",
            s.chip,
          )}
        >
          <s.icon size={20} />
        </span>
        <div className="min-w-0 flex-1">
          <Badge tone={s.tone}>{s.label}</Badge>
          <h3 className={cn("mt-1.5 font-bold", done && "line-through")}>
            {i.title}
          </h3>
          <p className="mt-0.5 text-sm text-muted">{i.detail}</p>
        </div>
      </div>
      <div className="rounded-xl bg-primary/5 p-3 text-sm dark:bg-white/5">
        <p className="mb-0.5 text-xs font-bold tracking-wider text-primary uppercase">
          Recommended decision
        </p>
        <p>{i.action}</p>
        {i.impact && (
          <p className="mt-1.5 text-xs font-semibold text-muted">
            Impact: {i.impact}
          </p>
        )}
      </div>
      <button
        onClick={onToggle}
        aria-pressed={done}
        className="flex min-h-11 items-center gap-2 self-start rounded-lg px-2 text-sm font-semibold text-muted transition hover:bg-primary/10 hover:text-primary"
      >
        <span
          className={cn(
            "grid size-5 place-items-center rounded-md border",
            done ? "btn-brand border-transparent text-white" : "border-line",
          )}
        >
          {done && <Check size={13} strokeWidth={3} />}
        </span>
        {done ? "Marked as done" : "Mark as done"}
      </button>
    </GlassCard>
  );
}
