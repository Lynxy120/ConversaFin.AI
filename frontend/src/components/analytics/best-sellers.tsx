import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { idr } from "@/lib/format";
import type { BestSeller } from "@/lib/types";

export function BestSellers({
  items,
  slow,
}: {
  items: BestSeller[];
  slow: { sku: string; name: string }[];
}) {
  return (
    <GlassCard className="p-5">
      <h2 className="font-bold">Best sellers</h2>
      <p className="mb-4 text-xs text-muted">
        Ranked by revenue. Trend compares units with the previous period.
      </p>
      {items.length === 0 ? (
        <p className="text-sm text-muted">No paid orders in this period yet.</p>
      ) : (
        <ol className="space-y-4">
          {items.map((b, n) => (
            <li key={b.sku}>
              <div className="flex items-center gap-3">
                <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-primary/10 text-xs font-extrabold text-primary tabular-nums">
                  {n + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{b.name}</p>
                  <p className="text-xs text-muted tabular-nums">
                    {b.units} sold · {idr(b.revenue)}
                  </p>
                </div>
                {b.trend === null ? (
                  <Badge tone="info">New</Badge>
                ) : (
                  <Badge tone={b.trend >= 0 ? "success" : "danger"}>
                    {b.trend >= 0 ? (
                      <ArrowUpRight size={12} />
                    ) : (
                      <ArrowDownRight size={12} />
                    )}
                    {Math.abs(b.trend).toFixed(0)}%
                  </Badge>
                )}
              </div>
              <div className="mt-2 flex items-center gap-2 pl-10">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-500/15">
                  <div
                    className="btn-brand h-full rounded-full"
                    style={{ width: `${Math.min(b.share, 100)}%` }}
                  />
                </div>
                <span className="w-10 text-right text-xs font-semibold text-muted tabular-nums">
                  {b.share.toFixed(0)}%
                </span>
              </div>
            </li>
          ))}
        </ol>
      )}
      {slow.length > 0 && (
        <div className="mt-5 border-t border-line pt-4">
          <p className="mb-2 text-xs font-bold tracking-wider text-muted uppercase">
            No sales this period
          </p>
          <div className="flex flex-wrap gap-2">
            {slow.map((s) => (
              <Badge key={s.sku}>{s.name}</Badge>
            ))}
          </div>
        </div>
      )}
    </GlassCard>
  );
}
