"use client";
import { useState } from "react";
import { Clock, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import {
  ChartsSkeleton,
  DashboardCharts,
} from "@/components/charts/DashboardCharts";
import { SystemStatus } from "@/components/system-status";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSummary } from "@/hooks/use-data";
import { cn } from "@/lib/cn";
import { dateShort, idr, shiftDays, todayWIB } from "@/lib/format";

const RANGES = [
  { v: 7, l: "7D" },
  { v: 30, l: "30D" },
  { v: 90, l: "90D" },
];
const DOMAINS = [
  { v: "", l: "All" },
  { v: "business", l: "Business" },
  { v: "personal", l: "Personal" },
];

function Seg<T extends string | number>({
  value,
  onChange,
  options,
  label,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { v: T; l: string }[];
  label: string;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className="glass inline-flex rounded-xl p-1"
    >
      {options.map((o) => (
        <button
          key={String(o.v)}
          aria-pressed={o.v === value}
          onClick={() => onChange(o.v)}
          className={cn(
            "min-h-10 rounded-lg px-3 text-sm font-semibold transition",
            o.v === value
              ? "bg-linear-135 from-primary to-blue-500 text-white"
              : "text-muted hover:bg-primary-light",
          )}
        >
          {o.l}
        </button>
      ))}
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: typeof Wallet;
  label: string;
  value?: string;
  sub: string;
  tone: "success" | "danger" | "info" | "warning";
}) {
  const t = {
    success: "bg-success/10 text-success",
    danger: "bg-danger/10 text-danger",
    info: "bg-primary/10 text-primary",
    warning: "bg-warning/10 text-warning",
  }[tone];
  return (
    <GlassCard className="p-4 sm:p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">{label}</p>
        <span className={cn("grid size-8 place-items-center rounded-lg", t)}>
          <Icon size={16} />
        </span>
      </div>
      {value === undefined ? (
        <Skeleton className="mt-3 h-8 w-32" />
      ) : (
        <p className="mt-2 text-lg font-extrabold tabular-nums sm:text-2xl">
          {value}
        </p>
      )}
      <p className="mt-1 text-xs text-muted">{sub}</p>
    </GlassCard>
  );
}

export default function Dashboard() {
  const [days, setDays] = useState(30);
  const [domain, setDomain] = useState("");
  const to = todayWIB();
  const from = shiftDays(to, -(days - 1));
  const { data, error, isLoading, mutate } = useSummary(from, to, domain);
  const period = `${dateShort(from)} – ${dateShort(to)}`;

  return (
    <>
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-extrabold">Dashboard</h1>
        <SystemStatus />
      </header>
      <div className="mb-4 flex flex-wrap gap-3">
        <Seg label="Range" value={days} onChange={setDays} options={RANGES} />
        <Seg
          label="Domain"
          value={domain}
          onChange={setDomain}
          options={DOMAINS}
        />
      </div>

      {error ? (
        <GlassCard className="flex flex-col items-center gap-3 p-10 text-center">
          <p className="font-bold">Couldn&apos;t load analytics</p>
          <p className="text-sm text-muted">{error.message}</p>
          <Button onClick={() => mutate()}>Retry</Button>
        </GlassCard>
      ) : (
        <>
          <section className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            <Stat
              icon={TrendingUp}
              tone="success"
              label="Revenue"
              sub={period}
              value={data && idr(data.income)}
            />
            <Stat
              icon={TrendingDown}
              tone="danger"
              label="Expenses"
              sub={period}
              value={data && idr(data.expense)}
            />
            <Stat
              icon={Wallet}
              tone={data && data.profit < 0 ? "danger" : "info"}
              label="Profit"
              sub={period}
              value={data && idr(data.profit)}
            />
            <Stat
              icon={Clock}
              tone="warning"
              label="Pending orders"
              sub="Awaiting QRIS payment"
              value={data && String(data.pending_orders)}
            />
          </section>
          {isLoading || !data ? (
            <ChartsSkeleton />
          ) : (
            <DashboardCharts data={data} />
          )}
        </>
      )}
    </>
  );
}
