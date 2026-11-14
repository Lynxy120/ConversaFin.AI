import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/cn";
import { idr } from "@/lib/format";
import type { CustomerStats } from "@/lib/types";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const hh = (h: number) => `${String(h).padStart(2, "0")}:00`;

export function CustomerInsights({ c }: { c: CustomerStats }) {
  const maxH = Math.max(...c.hours, 1),
    maxD = Math.max(...c.weekdays, 1);
  const revTotal = c.returning_revenue + c.new_revenue || 1;
  const retPct = Math.round((c.returning_revenue / revTotal) * 100);

  return (
    <section
      aria-label="Customer preferences"
      className="grid gap-4 lg:grid-cols-2"
    >
      <GlassCard className="p-5">
        <h2 className="font-bold">Who is buying</h2>
        <p className="mb-4 text-xs text-muted">
          {c.unique} customers · {c.avg_items} items per order
        </p>
        <div
          className="flex h-3 overflow-hidden rounded-full bg-slate-500/15"
          role="img"
          aria-label={`${retPct}% of revenue from returning customers`}
        >
          <div className="btn-brand" style={{ width: `${retPct}%` }} />
          <div
            className="bg-violet-400/70"
            style={{ width: `${100 - retPct}%` }}
          />
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="flex items-center gap-1.5 text-xs text-muted">
              <span className="size-2 rounded-full bg-primary" />
              Returning ({c.returning})
            </p>
            <p className="font-bold tabular-nums">{idr(c.returning_revenue)}</p>
          </div>
          <div>
            <p className="flex items-center gap-1.5 text-xs text-muted">
              <span className="size-2 rounded-full bg-violet-400" />
              New ({c.unique - c.returning})
            </p>
            <p className="font-bold tabular-nums">{idr(c.new_revenue)}</p>
          </div>
        </div>
        <h3 className="mt-5 mb-2 text-xs font-bold tracking-wider text-muted uppercase">
          Top customers
        </h3>
        {c.top.length === 0 ? (
          <p className="text-sm text-muted">No customers yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {c.top.map((t) => (
              <li
                key={t.name + t.spend}
                className="flex items-center justify-between gap-3 py-2.5 text-sm"
              >
                <span className="truncate font-semibold">{t.name}</span>
                <span className="shrink-0 text-xs text-muted tabular-nums">
                  {t.orders} orders · <b className="text-ink">{idr(t.spend)}</b>
                </span>
              </li>
            ))}
          </ul>
        )}
      </GlassCard>

      <GlassCard className="p-5">
        <h2 className="font-bold">When they buy</h2>
        <p className="mb-4 text-xs text-muted">
          {c.peak_hour !== null
            ? `Peak at ${hh(c.peak_hour)}${c.peak_day ? `, busiest on ${c.peak_day}s` : ""}`
            : "Not enough orders yet"}
        </p>
        <div
          className="grid grid-cols-12 gap-1.5 sm:grid-cols-24"
          aria-hidden="true"
        >
          {c.hours.map((n, h) => (
            <div
              key={h}
              title={`${hh(h)}: ${n} orders`}
              className={cn(
                "aspect-square rounded-md bg-primary",
                h === c.peak_hour &&
                  "ring-2 ring-primary/50 ring-offset-1 ring-offset-transparent",
              )}
              style={{ opacity: n ? 0.18 + (0.82 * n) / maxH : 0.07 }}
            />
          ))}
        </div>
        <div className="mt-1 flex justify-between text-[10px] text-muted tabular-nums">
          <span>00</span>
          <span>06</span>
          <span>12</span>
          <span>18</span>
          <span>23</span>
        </div>
        <div className="mt-5 flex h-24 items-end gap-2" aria-hidden="true">
          {c.weekdays.map((n, d) => (
            <div
              key={d}
              className="flex h-full flex-1 flex-col items-center justify-end gap-1"
            >
              <div
                title={`${DAYS[d]}: ${n} orders`}
                className={cn(
                  "w-full rounded-t-md",
                  n === maxD && n > 0 ? "btn-brand" : "bg-primary/30",
                )}
                style={{ height: `${Math.max((n / maxD) * 100, 4)}%` }}
              />
            </div>
          ))}
        </div>
        <div className="mt-1 flex gap-2 text-[11px] text-muted">
          {DAYS.map((d) => (
            <span key={d} className="flex-1 text-center">
              {d}
            </span>
          ))}
        </div>
      </GlassCard>

      <GlassCard className="p-5 lg:col-span-2">
        <h2 className="font-bold">Often bought together</h2>
        <p className="mb-3 text-xs text-muted">
          Pairs that appear in the same order more than chance would suggest
        </p>
        {c.bundles.length === 0 ? (
          <p className="text-sm text-muted">
            Not enough multi-item orders to find a pattern.
          </p>
        ) : (
          <ul className="grid gap-3 md:grid-cols-3">
            {c.bundles.map((b) => (
              <li
                key={b.a + b.b}
                className="rounded-xl bg-primary/5 p-4 dark:bg-white/5"
              >
                <p className="text-sm font-bold">
                  {b.a} <span className="text-primary">+</span> {b.b}
                </p>
                <p className="mt-1 text-xs text-muted">
                  {b.count} orders · {b.lift}x more likely together
                </p>
                <p className="mt-2 text-xs font-semibold">
                  Suggested bundle{" "}
                  <span className="text-primary tabular-nums">
                    {idr(b.bundle_price)}
                  </span>
                </p>
              </li>
            ))}
          </ul>
        )}
      </GlassCard>
    </section>
  );
}
