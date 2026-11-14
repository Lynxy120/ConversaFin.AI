"use client";
import { useState } from "react";
import { BarChart3, Receipt, Repeat, ShoppingBag, Wallet } from "lucide-react";
import { BestSellers } from "@/components/analytics/best-sellers";
import { CustomerInsights } from "@/components/analytics/customer-panel";
import { HealthRing } from "@/components/analytics/health-ring";
import { InsightCard } from "@/components/analytics/insight-card";
import { KpiCard } from "@/components/analytics/kpi-card";
import {
  ChartsSkeleton,
  DashboardCharts,
} from "@/components/charts/DashboardCharts";
import { SystemStatus } from "@/components/system-status";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { useInsights, useSummary } from "@/hooks/use-data";
import { dateShort, idr, shiftDays, todayWIB } from "@/lib/format";

const RANGES = [
  { v: 7, l: "7D" },
  { v: 30, l: "30D" },
  { v: 90, l: "90D" },
];

export default function Dashboard() {
  const [days, setDays] = useState(30);
  const [showAll, setShowAll] = useState(false);
  const [done, setDone] = useState<Set<string>>(new Set());
  const to = todayWIB();
  const from = shiftDays(to, -(days - 1));
  const { data, error, isLoading, mutate } = useInsights(days);
  const { data: summary } = useSummary(from, to);

  const toggle = (id: string) =>
    setDone((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  const recs = data?.recommendations ?? [];
  const open = recs.filter((r) => !done.has(r.id)).length;
  const shown = showAll ? recs : recs.slice(0, 4);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
            Bisnis <span className="font-bold text-muted">· Strategy room</span>
          </h1>
          <p className="mt-1 text-sm text-muted">
            {dateShort(from)} – {dateShort(to)} · decisions drawn from your own
            sales
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <SystemStatus />
          <Segmented
            label="Range"
            value={days}
            onChange={setDays}
            options={RANGES}
          />
        </div>
      </header>

      {error ? (
        <GlassCard className="flex flex-col items-center gap-3 p-10 text-center">
          <p className="font-bold">Couldn&apos;t load your analysis</p>
          <p className="text-sm text-muted">{error.message}</p>
          <Button onClick={() => mutate()}>Retry</Button>
        </GlassCard>
      ) : isLoading || !data ? (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            <GlassCard className="h-56 p-5 lg:col-span-1">
              <Skeleton className="size-full" />
            </GlassCard>
            <div className="grid grid-cols-2 gap-4 lg:col-span-2">
              {[0, 1, 2, 3].map((i) => (
                <GlassCard key={i} className="p-5">
                  <Skeleton className="h-24 w-full" />
                </GlassCard>
              ))}
            </div>
          </div>
          <ChartsSkeleton />
        </>
      ) : !data.has_data ? (
        <EmptyState
          icon={BarChart3}
          title="Not enough data yet"
          description="Once customers pay and you record expenses through the bot, your strategic analysis appears here."
        />
      ) : (
        <>
          <section
            aria-label="Executive brief"
            className="grid gap-4 lg:grid-cols-3"
          >
            <HealthRing health={data.health} />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:col-span-2">
              <KpiCard
                icon={Wallet}
                label="Revenue"
                value={idr(data.kpis.revenue)}
                delta={data.kpis.revenue_delta}
              />
              <KpiCard
                icon={BarChart3}
                label="Net margin"
                value={
                  data.kpis.margin === null
                    ? "n/a"
                    : `${data.kpis.margin.toFixed(1)}%`
                }
                sub={`Profit ${idr(data.kpis.profit)} on ${idr(data.kpis.income)} income`}
              />
              <KpiCard
                icon={Receipt}
                label="Average order"
                value={idr(data.kpis.aov)}
                delta={data.kpis.aov_delta}
              />
              <KpiCard
                icon={Repeat}
                label="Repeat customers"
                value={`${data.customers.repeat_rate.toFixed(0)}%`}
                sub={`${data.customers.returning} of ${data.customers.unique} customers came back`}
              />
            </div>
          </section>

          <section aria-label="Recommended decisions">
            <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
              <div>
                <h2 className="text-lg font-extrabold">
                  Decisions for this week
                </h2>
                <p className="text-xs text-muted">
                  {recs.length === 0
                    ? "Nothing needs attention."
                    : `${open} of ${recs.length} still open, most urgent first`}
                </p>
              </div>
              {recs.length > 4 && (
                <Button
                  variant="ghost"
                  className="min-h-11"
                  onClick={() => setShowAll((v) => !v)}
                >
                  {showAll ? "Show top 4" : `Show all ${recs.length}`}
                </Button>
              )}
            </div>
            {recs.length === 0 ? (
              <EmptyState
                icon={BarChart3}
                title="No decisions needed"
                description="Your numbers are steady. New recommendations appear as your data changes."
              />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {shown.map((r) => (
                  <InsightCard
                    key={r.id}
                    i={r}
                    done={done.has(r.id)}
                    onToggle={() => toggle(r.id)}
                  />
                ))}
              </div>
            )}
          </section>

          <section aria-label="Products" className="grid gap-4 lg:grid-cols-5">
            <div className="lg:col-span-3">
              <BestSellers items={data.best_sellers} slow={data.slow_movers} />
            </div>
            <GlassCard className="flex flex-col justify-center gap-4 p-5 lg:col-span-2">
              <h2 className="font-bold">Cash and payments</h2>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between gap-3">
                  <dt className="text-muted">Orders paid</dt>
                  <dd className="font-bold tabular-nums">{data.kpis.orders}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-muted">Payment conversion</dt>
                  <dd className="font-bold tabular-nums">
                    {data.kpis.conversion_rate === null
                      ? "n/a"
                      : `${data.kpis.conversion_rate}%`}
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-muted">QRIS expired</dt>
                  <dd className="font-bold tabular-nums">
                    {data.kpis.expiry_rate === null
                      ? "n/a"
                      : `${data.kpis.expiry_rate}%`}
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-muted">Waiting for payment</dt>
                  <dd className="font-bold text-warning tabular-nums">
                    {idr(data.kpis.pending_amount)} ({data.kpis.pending_count})
                  </dd>
                </div>
              </dl>
            </GlassCard>
          </section>

          <CustomerInsights c={data.customers} />

          <section aria-label="Money flow">
            <h2 className="text-lg font-extrabold">Money flow</h2>
            {summary ? <DashboardCharts data={summary} /> : <ChartsSkeleton />}
          </section>
        </>
      )}
    </div>
  );
}
