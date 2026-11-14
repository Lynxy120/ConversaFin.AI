"use client";
import dynamic from "next/dynamic";
import { Wallet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCashDashboard } from "@/hooks/use-data";
import { BreakdownCard } from "./breakdown-card";
import { DebtTracker } from "./debt-tracker";
import { Hero } from "./hero";
import { Ledger } from "./ledger";
import { CoreSummary } from "./summary";

const loading = () => (
  <GlassCard className="p-5">
    <Skeleton className="h-64 w-full" />
  </GlassCard>
);
const ExpenseDonut = dynamic(
  () => import("./charts").then((m) => m.ExpenseDonut),
  { ssr: false, loading },
);
const ExpenseBars = dynamic(
  () => import("./charts").then((m) => m.ExpenseBars),
  { ssr: false, loading },
);

export function Overview({ month }: { month: string }) {
  const { data: d, error, isLoading, mutate } = useCashDashboard(month);

  if (error)
    return (
      <GlassCard className="flex flex-col items-center gap-3 p-10 text-center">
        <p className="font-bold">Gagal memuat data keuangan</p>
        <p className="text-sm text-muted">{error.message}</p>
        <Button onClick={() => mutate()}>Coba lagi</Button>
      </GlassCard>
    );
  if (isLoading || !d)
    return (
      <div className="space-y-4">
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-36 rounded-3xl" />
          <Skeleton className="h-36 rounded-3xl lg:col-span-2" />
        </div>
        <Skeleton className="h-64 w-full rounded-3xl" />
      </div>
    );

  const cats = [
    ...new Set(
      Object.values(d.groups).flatMap((g) => g.map((r) => r.category)),
    ),
  ];
  const empty =
    d.pockets.length <= 1 &&
    d.summary.every((s) => !s.actual && !s.budget) &&
    d.balance.total === 0;

  return (
    <div className="space-y-6">
      <Hero d={d} />
      {empty && (
        <EmptyState
          icon={Wallet}
          title="Mulai catat keuangan"
          description="Atur pocket dan budget di tab Budgeting, lalu catat transaksi pertama."
        />
      )}
      <section aria-label="Ringkasan" className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <CoreSummary d={d} />
        </div>
        <div className="lg:col-span-2">
          <ExpenseDonut ratio={d.ratio} />
        </div>
      </section>
      <ExpenseBars summary={d.summary} />
      <section
        aria-label="Rincian kategori"
        className="grid gap-4 md:grid-cols-2"
      >
        <BreakdownCard
          title="Pemasukan"
          kind="in"
          budgetLabel="Target"
          rows={d.groups.pemasukan}
        />
        <BreakdownCard
          title="Tagihan"
          kind="out"
          budgetLabel="Budget"
          rows={d.groups.tagihan}
        />
        <BreakdownCard
          title="Pengeluaran Harian"
          kind="out"
          budgetLabel="Budget"
          rows={d.groups.pengeluaran_harian}
        />
        <BreakdownCard
          title="Tabungan & Investasi"
          kind="in"
          budgetLabel="Target/Bulan"
          rows={d.groups.tabungan}
        />
      </section>
      <DebtTracker debts={d.debts} pockets={d.pockets} />
      <Ledger month={month} categories={cats} />
    </div>
  );
}
