import {
  Banknote,
  CreditCard,
  Landmark,
  PiggyBank,
  Smartphone,
  Wallet,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/cn";
import { idr } from "@/lib/format";
import type { CashDashboard, PocketType } from "@/lib/types";

const ICON = {
  cash: Banknote,
  bank: Landmark,
  ewallet: Smartphone,
  savings: PiggyBank,
} satisfies Record<PocketType, unknown>;

export function Hero({ d }: { d: CashDashboard }) {
  const b = d.balance;
  const split = [
    {
      label: "Cash",
      v: b.cash,
      icon: Wallet,
      tone: "bg-primary/10 text-primary",
    },
    {
      label: "Tabungan",
      v: b.savings,
      icon: PiggyBank,
      tone: "bg-success/10 text-success",
    },
    {
      label: "Hutang",
      v: b.debt_remaining,
      icon: CreditCard,
      tone: "bg-danger/10 text-danger",
    },
  ];
  return (
    <section aria-label="Saldo" className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        <div
          className="rounded-3xl p-6 text-white shadow-lg shadow-primary/25"
          style={{ background: "linear-gradient(135deg,#0EA5E9,#3B82F6)" }}
        >
          <p className="text-sm font-semibold opacity-90">$ BALANCE</p>
          <p className="mt-2 text-3xl font-extrabold tracking-tight tabular-nums sm:text-4xl">
            {idr(b.total)}
          </p>
          <p className="mt-1 text-xs opacity-80">
            Cash + tabungan di semua pocket
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3 lg:col-span-2">
          {split.map((s) => (
            <GlassCard
              key={s.label}
              className="flex flex-col justify-between gap-3 p-5"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted">{s.label}</p>
                <span
                  className={cn(
                    "grid size-9 place-items-center rounded-xl",
                    s.tone,
                  )}
                >
                  <s.icon size={18} />
                </span>
              </div>
              <p className="truncate text-xl font-extrabold tabular-nums">
                {idr(s.v)}
              </p>
            </GlassCard>
          ))}
        </div>
      </div>
      <ul
        aria-label="Saldo per pocket"
        className="no-scrollbar -mx-4 flex snap-x gap-3 overflow-x-auto px-4 py-1 md:mx-0 md:px-0"
      >
        {d.pockets.map((p) => {
          const Icon = ICON[p.type];
          return (
            <li
              key={p.id}
              className="glass min-w-[152px] shrink-0 snap-start rounded-2xl p-4"
            >
              <div className="flex items-center gap-2 text-xs font-semibold text-muted">
                <Icon size={16} className="text-primary" />
                {p.name}
              </div>
              <p
                className={cn(
                  "mt-2 text-base font-extrabold tabular-nums",
                  p.balance < 0 && "text-danger",
                )}
              >
                {idr(p.balance)}
              </p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
