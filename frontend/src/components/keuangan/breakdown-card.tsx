import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/cn";
import { titleCase } from "@/lib/finance";
import { idr } from "@/lib/format";
import type { BudgetRow } from "@/lib/types";

const barTone = (kind: "in" | "out", pct: number) =>
  kind === "in"
    ? "bg-success"
    : pct > 100
      ? "bg-danger"
      : pct >= 80
        ? "bg-warning"
        : "bg-primary";

function Bar({ pct, cls, label }: { pct: number; cls: string; label: string }) {
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(Math.min(pct, 100))}
      className="h-2 overflow-hidden rounded-full bg-slate-500/15"
    >
      <div
        className={cn(
          "h-full rounded-full transition-[width] duration-500",
          cls,
        )}
        style={{ width: `${Math.min(pct, 100)}%` }}
      />
    </div>
  );
}

export function BreakdownCard({
  title,
  kind,
  rows,
  budgetLabel,
}: {
  title: string;
  kind: "in" | "out";
  rows: BudgetRow[];
  budgetLabel: string;
}) {
  const tb = rows.reduce((s, r) => s + r.budget, 0),
    ta = rows.reduce((s, r) => s + r.actual, 0);
  return (
    <GlassCard className="p-5">
      <div className="mb-4 flex items-baseline justify-between gap-2">
        <h3 className="font-bold">{title}</h3>
        <p className="text-xs text-muted tabular-nums">
          {idr(ta)} / {idr(tb)}{" "}
          <span className="hidden sm:inline">({budgetLabel})</span>
        </p>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-muted">
          Belum ada data. Atur kategori di tab Budgeting.
        </p>
      ) : (
        <ul className="space-y-4">
          {rows.map((r) => {
            const pct = r.pct ?? 0;
            return (
              <li key={r.category}>
                <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
                  <span className="truncate font-semibold">
                    {titleCase(r.category)}
                  </span>
                  <span className="shrink-0 tabular-nums">
                    <b
                      className={cn(
                        kind === "out" && pct > 100 && "text-danger",
                      )}
                    >
                      {idr(r.actual)}
                    </b>
                    <span className="text-muted">
                      {" "}
                      / {r.budget ? idr(r.budget) : "tanpa budget"}
                    </span>
                  </span>
                </div>
                {r.budget > 0 && (
                  <Bar
                    pct={pct}
                    cls={barTone(kind, pct)}
                    label={`${titleCase(r.category)} ${Math.round(pct)}%`}
                  />
                )}
                {r.total_target ? (
                  <div className="mt-2">
                    <div className="mb-1 flex justify-between text-xs text-muted tabular-nums">
                      <span>
                        Tujuan {idr(r.saved ?? 0)} / {idr(r.total_target)}
                        {r.target_date ? ` · ${r.target_date.slice(0, 7)}` : ""}
                      </span>
                      <span className="font-semibold">
                        {Math.min(r.goal_pct ?? 0, 100).toFixed(0)}%
                      </span>
                    </div>
                    <Bar
                      pct={r.goal_pct ?? 0}
                      cls="btn-brand"
                      label={`Progres tujuan ${titleCase(r.category)}`}
                    />
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </GlassCard>
  );
}
