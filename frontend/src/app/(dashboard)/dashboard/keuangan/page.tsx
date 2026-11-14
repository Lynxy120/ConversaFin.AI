"use client";
import { useState } from "react";
import { MonthPicker } from "@/components/keuangan/month-picker";
import { Overview } from "@/components/keuangan/overview";
import { Setup } from "@/components/keuangan/setup";
import { Yearly } from "@/components/keuangan/yearly";
import { Segmented } from "@/components/ui/segmented";
import { todayWIB } from "@/lib/format";

type Tab = "overview" | "yearly" | "setup";
const TABS: { v: Tab; l: string }[] = [
  { v: "overview", l: "Overview" },
  { v: "yearly", l: "Yearly" },
  { v: "setup", l: "Budgeting" },
];

export default function KeuanganPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [month, setMonth] = useState(todayWIB().slice(0, 7));

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
            Keuangan
          </h1>
          <p className="mt-1 text-sm text-muted">
            Cashflow, budget, tabungan, dan hutang
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Segmented
            label="Tampilan"
            value={tab}
            onChange={setTab}
            options={TABS}
          />
          {tab !== "setup" && <MonthPicker value={month} onChange={setMonth} />}
        </div>
      </header>
      {tab === "overview" && <Overview month={month} />}
      {tab === "yearly" && <Yearly year={Number(month.slice(0, 4))} />}
      {tab === "setup" && <Setup />}
    </div>
  );
}
