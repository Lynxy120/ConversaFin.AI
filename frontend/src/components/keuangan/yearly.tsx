"use client";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useYearly } from "@/hooks/use-data";
import { cn } from "@/lib/cn";
import { MONTHS_ID, num, titleCase } from "@/lib/finance";
import type { YearRow } from "@/lib/types";

const stick =
  "sticky left-0 z-10 bg-white/90 backdrop-blur dark:bg-slate-900/90";

function Cell({ v, bold }: { v: number | null; bold?: boolean }) {
  return (
    <td
      className={cn(
        "px-3 py-2.5 text-right tabular-nums",
        v ? (bold ? "font-bold" : "") : "text-muted/60",
      )}
    >
      {v === null ? "–" : num(v)}
    </td>
  );
}

function Line({
  label,
  r,
  tone,
}: {
  label: string;
  r: YearRow;
  tone?: string;
}) {
  return (
    <tr className="border-t border-line">
      <th
        scope="row"
        className={cn(stick, "px-3 py-2.5 text-left font-medium", tone)}
      >
        {label}
      </th>
      {r.values.map((v, i) => (
        <Cell key={i} v={v} />
      ))}
      <Cell v={r.total} bold />
    </tr>
  );
}

const Head = ({ children }: { children: string }) => (
  <tr>
    <th
      colSpan={14}
      className={cn(
        stick,
        "bg-primary/10 px-3 py-2 text-left text-xs font-extrabold tracking-wider text-primary",
      )}
    >
      {children}
    </th>
  </tr>
);

export function Yearly({ year }: { year: number }) {
  const { data: y, error, isLoading } = useYearly(year);
  if (error)
    return (
      <GlassCard className="p-8 text-center text-sm text-danger">
        {error.message}
      </GlassCard>
    );
  if (isLoading || !y) return <Skeleton className="h-96 w-full rounded-3xl" />;
  const tone = { income: "text-success", expense: "text-danger" } as Record<
    string,
    string
  >;
  return (
    <GlassCard className="p-0">
      <p className="px-5 pt-4 text-xs text-muted">
        Tahun {y.year} · dalam Rupiah · geser ke samping untuk melihat semua
        bulan
      </p>
      <div className="overflow-x-auto p-2">
        <table className="w-full min-w-[1400px] text-sm">
          <thead>
            <tr className="text-xs text-muted">
              <th className={cn(stick, "px-3 py-3 text-left font-semibold")}>
                {y.year}
              </th>
              {MONTHS_ID.map((m) => (
                <th
                  key={m}
                  className="min-w-[104px] px-3 py-3 text-right font-semibold"
                >
                  {m}
                </th>
              ))}
              <th className="min-w-[120px] px-3 py-3 text-right font-extrabold text-ink">
                TOTAL
              </th>
            </tr>
          </thead>
          <tbody>
            <Head>INCOME</Head>
            {y.income.length ? (
              y.income.map((r) => (
                <Line key={r.category} label={titleCase(r.category!)} r={r} />
              ))
            ) : (
              <tr>
                <td colSpan={14} className="px-3 py-3 text-muted">
                  Belum ada pemasukan tahun ini.
                </td>
              </tr>
            )}
            <Head>EXPENSE</Head>
            {y.expense.map((r) => (
              <Line key={r.key} label={r.label!} r={r} />
            ))}
            <Head>CASHFLOW SUMMARY</Head>
            {y.summary.map((r) => (
              <Line
                key={r.key}
                label={r.label!}
                r={r}
                tone={cn(tone[r.key!], r.key === "saldo" && "font-extrabold")}
              />
            ))}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
}
