"use client";
import { BarChart3 } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EmptyState } from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMedia } from "@/hooks/use-media";
import { catLabel, compact, dayLabel, idr } from "@/lib/format";
import type { Summary } from "@/lib/types";

const C = {
  income: "#10B981",
  expense: "#EF4444",
  profit: "#0EA5E9",
  grid: "rgba(100,116,139,.18)",
  tick: "#64748B",
};
const PIE = [
  "#0EA5E9",
  "#3B82F6",
  "#8B5CF6",
  "#10B981",
  "#F59E0B",
  "#EC4899",
  "#94A3B8",
];
const tip = {
  contentStyle: {
    background: "rgba(255,255,255,.92)",
    backdropFilter: "blur(12px)",
    border: "1px solid rgba(255,255,255,.5)",
    borderRadius: 12,
    boxShadow: "0 4px 30px rgba(0,0,0,.08)",
    fontSize: 12,
  },
};
const axis = {
  tick: { fill: C.tick, fontSize: 11 },
  tickLine: false,
  axisLine: false,
} as const;
const money = (v: unknown) => idr(Number(v));

function Panel({
  title,
  sub,
  className,
  children,
}: {
  title: string;
  sub?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <GlassCard className={`p-4 sm:p-5 ${className ?? ""}`}>
      <h2 className="font-bold">{title}</h2>
      {sub && <p className="mb-3 text-xs text-muted">{sub}</p>}
      <div className="mt-2 h-64 sm:h-72">{children}</div>
    </GlassCard>
  );
}

export function ChartsSkeleton() {
  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-3">
      <GlassCard className="h-80 p-5 lg:col-span-2">
        <Skeleton className="size-full" />
      </GlassCard>
      <GlassCard className="h-80 p-5">
        <Skeleton className="size-full" />
      </GlassCard>
      <GlassCard className="h-80 p-5 lg:col-span-3">
        <Skeleton className="size-full" />
      </GlassCard>
    </div>
  );
}

export function DashboardCharts({ data }: { data: Summary }) {
  const desktop = useMedia("(min-width: 768px)");
  const rows = data.series.map((r) => {
    const income = Number(r.income),
      expense = Number(r.expense);
    return { day: r.day, income, expense, profit: income - expense };
  });

  if (rows.every((r) => r.income === 0 && r.expense === 0)) {
    return (
      <div className="mt-4">
        <EmptyState
          icon={BarChart3}
          title="No transactions in this period"
          description="Send a voice note or receipt photo to your WhatsApp bot to record your first transaction."
        />
      </div>
    );
  }

  const bars = desktop && rows.length <= 31; // dense ranges + mobile → lines
  const shared = (
    <>
      <CartesianGrid stroke={C.grid} vertical={false} />
      <XAxis dataKey="day" tickFormatter={dayLabel} minTickGap={24} {...axis} />
      <YAxis tickFormatter={compact} width={44} {...axis} />
      <Tooltip
        {...tip}
        formatter={money}
        labelFormatter={(l) => dayLabel(String(l))}
      />
    </>
  );

  const exp = data.categories
    .filter((c) => c.type === "expense")
    .map((c) => ({ name: catLabel(c.category), value: Number(c.total) }));
  const top = exp.slice(0, 6);
  const rest = exp.slice(6).reduce((s, c) => s + c.value, 0);
  const slices = rest > 0 ? [...top, { name: "Others", value: rest }] : top;
  const totalExp = slices.reduce((s, c) => s + c.value, 0);

  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-3">
      <Panel
        title="Revenue vs Expenses"
        sub="Daily, IDR"
        className="lg:col-span-2"
      >
        <ResponsiveContainer width="100%" height="100%">
          {bars ? (
            <BarChart data={rows} barGap={2}>
              {shared}
              <Bar
                dataKey="income"
                name="Revenue"
                fill={C.income}
                radius={[6, 6, 0, 0]}
              />
              <Bar
                dataKey="expense"
                name="Expenses"
                fill={C.expense}
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          ) : (
            <LineChart data={rows}>
              {shared}
              <Line
                dataKey="income"
                name="Revenue"
                stroke={C.income}
                strokeWidth={2.5}
                dot={false}
              />
              <Line
                dataKey="expense"
                name="Expenses"
                stroke={C.expense}
                strokeWidth={2.5}
                dot={false}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </Panel>

      <GlassCard className="p-4 sm:p-5">
        <h2 className="font-bold">Expenses by category</h2>
        {slices.length === 0 ? (
          <p className="mt-6 text-sm text-muted">No expenses in this period.</p>
        ) : (
          <>
            <div className="relative mt-2 h-44">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={slices}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="64%"
                    outerRadius="92%"
                    paddingAngle={2}
                    stroke="none"
                  >
                    {slices.map((s, i) => (
                      <Cell key={s.name} fill={PIE[i % PIE.length]} />
                    ))}
                  </Pie>
                  <Tooltip {...tip} formatter={money} />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
                <div>
                  <p className="text-xs text-muted">Total</p>
                  <p className="text-sm font-extrabold tabular-nums">
                    {compact(totalExp)}
                  </p>
                </div>
              </div>
            </div>
            <ul className="mt-3 space-y-1.5 text-sm">
              {slices.map((s, i) => (
                <li key={s.name} className="flex items-center gap-2">
                  <span
                    className="size-2.5 rounded-full"
                    style={{ background: PIE[i % PIE.length] }}
                  />
                  <span className="flex-1 truncate">{s.name}</span>
                  <span className="text-xs text-muted tabular-nums">
                    {Math.round((s.value / totalExp) * 100)}%
                  </span>
                  <span className="w-24 text-right font-semibold tabular-nums">
                    {idr(s.value)}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </GlassCard>

      <Panel
        title="Profit"
        sub="Revenue − expenses, daily"
        className="lg:col-span-3"
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={rows}>
            <defs>
              <linearGradient id="pf" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.profit} stopOpacity={0.35} />
                <stop offset="100%" stopColor={C.profit} stopOpacity={0} />
              </linearGradient>
            </defs>
            {shared}
            <ReferenceLine y={0} stroke={C.tick} strokeDasharray="4 4" />
            <Area
              dataKey="profit"
              name="Profit"
              stroke={C.profit}
              strokeWidth={2.5}
              fill="url(#pf)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  );
}
