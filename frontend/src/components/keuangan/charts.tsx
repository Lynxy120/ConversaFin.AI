"use client";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { GlassCard } from "@/components/ui/glass-card";
import { idr } from "@/lib/format";
import type { CashDashboard } from "@/lib/types";

const tip = {
  background: "var(--glass)",
  border: "1px solid var(--line)",
  borderRadius: 12,
  backdropFilter: "blur(12px)",
  color: "var(--ink)",
};
const tick = { fill: "var(--muted)", fontSize: 12 };
const short = (n: number) =>
  Math.abs(n) >= 1e6
    ? `${+(n / 1e6).toFixed(1)}jt`
    : Math.abs(n) >= 1e3
      ? `${Math.round(n / 1e3)}rb`
      : String(n);

export function ExpenseDonut({ ratio }: { ratio: CashDashboard["ratio"] }) {
  const over = ratio.expense > ratio.income;
  const data =
    ratio.income > 0
      ? [
          {
            name: "Pengeluaran",
            value: Math.min(ratio.expense, ratio.income),
            c: over ? "#EF4444" : "#0EA5E9",
          },
          {
            name: "Sisa",
            value: Math.max(ratio.income - ratio.expense, 0),
            c: "#10B981",
          },
        ]
      : [{ name: "Belum ada pemasukan", value: 1, c: "#CBD5E1" }];
  return (
    <GlassCard className="p-5">
      <h2 className="font-bold">Rasio Pengeluaran</h2>
      <div
        className="relative mx-auto mt-2 h-52 max-w-xs"
        role="img"
        aria-label={`Pengeluaran ${ratio.pct ?? 0} persen dari pemasukan`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              innerRadius="66%"
              outerRadius="92%"
              startAngle={90}
              endAngle={-270}
              stroke="none"
              paddingAngle={data.length > 1 ? 2 : 0}
            >
              {data.map((x) => (
                <Cell key={x.name} fill={x.c} />
              ))}
            </Pie>
            {ratio.income > 0 && (
              <Tooltip contentStyle={tip} formatter={(v) => idr(Number(v))} />
            )}
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <p className="text-3xl font-extrabold tabular-nums">
            {ratio.pct === null ? "–" : `${ratio.pct}%`}
          </p>
        </div>
      </div>
      <p className="mt-2 text-center text-sm font-semibold">
        {ratio.pct === null
          ? "Belum ada pemasukan bulan ini"
          : `Pengeluaran sebesar ${ratio.pct}% dari Pemasukan`}
      </p>
      <p className="mt-1 text-center text-xs text-muted tabular-nums">
        {idr(ratio.expense)} dari {idr(ratio.income)}
      </p>
    </GlassCard>
  );
}

export function ExpenseBars({
  summary,
}: {
  summary: CashDashboard["summary"];
}) {
  const data = summary
    .filter((s) => ["tagihan", "pengeluaran", "hutang"].includes(s.key))
    .map((s) => ({ name: s.label, Budget: s.budget, Aktual: s.actual }));
  return (
    <GlassCard className="p-5">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-bold">Perform Expense</h2>
        <div className="flex gap-4 text-xs text-muted">
          <span className="flex items-center gap-1.5">
            <i className="size-2.5 rounded-full bg-slate-400" />
            Budget
          </span>
          <span className="flex items-center gap-1.5">
            <i className="size-2.5 rounded-full bg-primary" />
            Aktual
          </span>
        </div>
      </div>
      <div
        className="h-56"
        role="img"
        aria-label="Perbandingan budget dan aktual pengeluaran"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ left: 0, right: 12 }}
            barGap={4}
          >
            <CartesianGrid horizontal={false} stroke="var(--line)" />
            <XAxis
              type="number"
              tickFormatter={short}
              tick={tick}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={88}
              tick={tick}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={tip}
              formatter={(v) => idr(Number(v))}
              cursor={{ fill: "rgba(14,165,233,.08)" }}
            />
            <Bar
              dataKey="Budget"
              fill="#94A3B8"
              barSize={14}
              radius={[0, 6, 6, 0]}
            />
            <Bar
              dataKey="Aktual"
              fill="#0EA5E9"
              barSize={14}
              radius={[0, 6, 6, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  );
}
