"use client";
import { Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAccounts, useBudgets, useDebts } from "@/hooks/use-data";
import { api } from "@/lib/api";
import {
  monthlyNominal,
  POCKET_LABEL,
  refreshFinance,
  titleCase,
} from "@/lib/finance";
import { idr, todayWIB } from "@/lib/format";
import type { Budget, PocketType } from "@/lib/types";

async function run(fn: () => Promise<unknown>, ok = "Tersimpan") {
  try {
    await fn();
    toast.success(ok);
    await refreshFinance();
    return true;
  } catch (e) {
    toast.error(e instanceof Error ? e.message : "Gagal menyimpan");
    return false;
  }
}

function Section({
  title,
  hint,
  children,
}: {
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <GlassCard className="p-5">
      <h2 className="font-bold">{title}</h2>
      <p className="mb-4 text-xs text-muted">{hint}</p>
      {children}
    </GlassCard>
  );
}

function InlineNumber({
  value,
  onSave,
  label,
}: {
  value: number;
  onSave: (v: number) => void;
  label: string;
}) {
  return (
    <div className="w-36 shrink-0">
      <input
        aria-label={label}
        type="number"
        inputMode="numeric"
        min={0}
        defaultValue={value}
        key={value}
        onBlur={(e) => {
          const v = Number(e.target.value);
          if (!Number.isNaN(v) && v !== value) onSave(v);
        }}
        className={`${inputCls} text-right tabular-nums`}
      />
    </div>
  );
}

/* 1. Pockets */
function Pockets() {
  const { data = [], isLoading } = useAccounts(true);
  const patch = (id: string, json: object) =>
    run(() => api(`/finance/accounts/${id}`, { method: "PATCH", json }));
  async function add(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      f = new FormData(form);
    if (
      await run(
        () =>
          api("/finance/accounts", {
            method: "POST",
            json: {
              name: String(f.get("name")).trim(),
              type: f.get("type"),
              initial_balance: Number(f.get("initial") || 0),
            },
          }),
        "Pocket ditambahkan",
      )
    )
      form.reset();
  }
  return (
    <Section
      title="Pockets"
      hint="Cash, bank, e-wallet dan tabungan beserta saldo awal"
    >
      {isLoading ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <ul className="divide-y divide-line">
          {data.map((a) => (
            <li key={a.id} className="flex flex-wrap items-center gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="font-semibold">
                  {a.name} {a.is_default && <Badge tone="info">Default</Badge>}{" "}
                  {!a.is_active && <Badge>Nonaktif</Badge>}
                </p>
                <p className="text-xs text-muted">{POCKET_LABEL[a.type]}</p>
              </div>
              <InlineNumber
                label={`Saldo awal ${a.name}`}
                value={Number(a.initial_balance)}
                onSave={(v) => patch(a.id, { initial_balance: v })}
              />
              {!a.is_default && (
                <Button
                  variant="ghost"
                  onClick={() => patch(a.id, { is_active: !a.is_active })}
                >
                  {a.is_active ? "Nonaktifkan" : "Aktifkan"}
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      <form
        onSubmit={add}
        className="mt-4 grid gap-3 sm:grid-cols-[1.4fr_1fr_1fr_auto] sm:items-end"
      >
        <Field label="Nama">
          <input
            name="name"
            required
            maxLength={40}
            placeholder="BCA, GoPay…"
            className={inputCls}
          />
        </Field>
        <Field label="Jenis">
          <select name="type" className={inputCls}>
            {(Object.keys(POCKET_LABEL) as PocketType[]).map((t) => (
              <option key={t} value={t}>
                {POCKET_LABEL[t]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Saldo awal">
          <input
            name="initial"
            type="number"
            inputMode="numeric"
            defaultValue={0}
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <Button type="submit">Tambah</Button>
      </form>
    </Section>
  );
}

/* 2-3. Income targets, bills, daily budgets */
function BudgetList({
  group,
  title,
  hint,
}: {
  group: Budget["group_type"];
  title: string;
  hint: string;
}) {
  const { data = [], isLoading } = useBudgets();
  const rows = data.filter((b) => b.group_type === group);
  const put = (category: string, amount: number) =>
    run(() =>
      api("/finance/budgets", {
        method: "PUT",
        json: { group_type: group, category, budget_amount: amount },
      }),
    );
  async function add(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      f = new FormData(form);
    if (
      await put(String(f.get("category")).trim(), Number(f.get("amount") || 0))
    )
      form.reset();
  }
  return (
    <Section title={title} hint={hint}>
      {isLoading ? (
        <Skeleton className="h-20 w-full" />
      ) : rows.length === 0 ? (
        <p className="text-sm text-muted">Belum ada kategori.</p>
      ) : (
        <ul className="divide-y divide-line">
          {rows.map((b) => (
            <li key={b.id} className="flex items-center gap-3 py-2.5">
              <span className="min-w-0 flex-1 truncate font-semibold">
                {titleCase(b.category)}
              </span>
              <InlineNumber
                label={`${title} ${b.category}`}
                value={Number(b.budget_amount)}
                onSave={(v) => put(b.category, v)}
              />
              <button
                aria-label={`Hapus ${b.category}`}
                onClick={() =>
                  run(
                    () => api(`/finance/budgets/${b.id}`, { method: "DELETE" }),
                    "Dihapus",
                  )
                }
                className="grid size-11 place-items-center rounded-xl text-muted hover:bg-danger/10 hover:text-danger"
              >
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      <form
        onSubmit={add}
        className="mt-4 grid gap-3 sm:grid-cols-[1.4fr_1fr_auto] sm:items-end"
      >
        <Field label="Kategori">
          <input name="category" required maxLength={60} className={inputCls} />
        </Field>
        <Field label="Per bulan">
          <input
            name="amount"
            type="number"
            inputMode="numeric"
            min={0}
            required
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <Button type="submit">Simpan</Button>
      </form>
    </Section>
  );
}

/* 4. Savings plans */
function SavingsPlans() {
  const { data = [], isLoading } = useBudgets();
  const plans = data.filter((b) => b.group_type === "tabungan");
  const [f, setF] = useState({
    category: "",
    total: "",
    start: todayWIB(),
    target: "",
  });
  const ok = Number(f.total) > 0 && f.start && f.target && f.target >= f.start;
  const nominal = ok ? monthlyNominal(Number(f.total), f.start, f.target) : 0;
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (
      await run(
        () =>
          api("/finance/budgets", {
            method: "PUT",
            json: {
              group_type: "tabungan",
              category: f.category.trim(),
              total_target: Number(f.total),
              start_date: f.start,
              target_date: f.target,
            },
          }),
        "Rencana tersimpan",
      )
    )
      setF({ category: "", total: "", start: todayWIB(), target: "" });
  }
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setF({ ...f, [k]: e.target.value });
  return (
    <Section
      title="Rencana Tabungan"
      hint="Nominal / bulan dihitung otomatis dari target dan rentang tanggal"
    >
      {isLoading ? (
        <Skeleton className="h-20 w-full" />
      ) : plans.length === 0 ? (
        <p className="text-sm text-muted">Belum ada rencana.</p>
      ) : (
        <ul className="divide-y divide-line">
          {plans.map((p) => (
            <li key={p.id} className="flex flex-wrap items-center gap-3 py-3">
              <button
                className="min-w-0 flex-1 text-left"
                onClick={() =>
                  setF({
                    category: titleCase(p.category),
                    total: String(p.total_target ?? ""),
                    start: p.start_date ?? todayWIB(),
                    target: p.target_date ?? "",
                  })
                }
              >
                <p className="font-semibold">{titleCase(p.category)}</p>
                <p className="text-xs text-muted tabular-nums">
                  {idr(p.total_target ?? 0)} · {p.start_date?.slice(0, 7)} →{" "}
                  {p.target_date?.slice(0, 7)}
                </p>
              </button>
              <p className="text-sm font-bold tabular-nums">
                {idr(p.budget_amount)}
                <span className="font-normal text-muted"> /bln</span>
              </p>
              <button
                aria-label={`Hapus ${p.category}`}
                onClick={() =>
                  run(
                    () => api(`/finance/budgets/${p.id}`, { method: "DELETE" }),
                    "Dihapus",
                  )
                }
                className="grid size-11 place-items-center rounded-xl text-muted hover:bg-danger/10 hover:text-danger"
              >
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={save} className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field label="Kategori">
          <input
            required
            maxLength={60}
            value={f.category}
            onChange={set("category")}
            placeholder="Dana Darurat"
            className={inputCls}
          />
        </Field>
        <Field label="Total target (IDR)">
          <input
            required
            type="number"
            inputMode="numeric"
            min={1}
            value={f.total}
            onChange={set("total")}
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <Field label="Mulai">
          <input
            required
            type="date"
            value={f.start}
            onChange={set("start")}
            className={inputCls}
          />
        </Field>
        <Field label="Target tercapai">
          <input
            required
            type="date"
            value={f.target}
            min={f.start}
            onChange={set("target")}
            className={inputCls}
          />
        </Field>
        <div className="flex items-center justify-between gap-3 sm:col-span-2">
          <p className="text-sm">
            Nominal / Bulan{" "}
            <b className="text-primary tabular-nums">
              {ok ? idr(nominal) : "–"}
            </b>
          </p>
          <Button type="submit" disabled={!ok || !f.category.trim()}>
            Simpan rencana
          </Button>
        </div>
        <p className="text-xs text-muted sm:col-span-2">
          Klik rencana di atas untuk mengubahnya, lalu simpan dengan kategori
          yang sama.
        </p>
      </form>
    </Section>
  );
}

/* 5. Debts */
const DEBT_CATS = ["Usaha", "Mobil", "Rumah", "Lain-lain"];

function DebtSetup() {
  const { data = [], isLoading } = useDebts();
  const patch = (id: string, json: object) =>
    run(() => api(`/finance/debts/${id}`, { method: "PATCH", json }));
  async function add(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      f = new FormData(form);
    if (
      await run(
        () =>
          api("/finance/debts", {
            method: "POST",
            json: {
              category: f.get("category"),
              description: f.get("description") || null,
              total_amount: Number(f.get("total")),
              paid_amount: Number(f.get("paid") || 0),
              monthly_payment: Number(f.get("monthly") || 0),
            },
          }),
        "Hutang ditambahkan",
      )
    )
      form.reset();
  }
  return (
    <Section
      title="Debt Setup"
      hint="Total hutang dan cicilan per bulan (dipakai sebagai budget Hutang)"
    >
      {isLoading ? (
        <Skeleton className="h-20 w-full" />
      ) : data.length === 0 ? (
        <p className="text-sm text-muted">Belum ada hutang.</p>
      ) : (
        <ul className="divide-y divide-line">
          {data.map((d) => (
            <li key={d.id} className="flex flex-wrap items-center gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="font-semibold">
                  {titleCase(d.category)}{" "}
                  {d.status === "paid" && <Badge tone="success">Lunas</Badge>}
                </p>
                <p className="truncate text-xs text-muted">
                  {d.description ?? "–"} · terbayar {idr(d.paid_amount)}
                </p>
              </div>
              <label className="text-xs text-muted">
                Total
                <InlineNumber
                  label={`Total ${d.category}`}
                  value={d.total_amount}
                  onSave={(v) => patch(d.id, { total_amount: v })}
                />
              </label>
              <label className="text-xs text-muted">
                Cicilan/bln
                <InlineNumber
                  label={`Cicilan ${d.category}`}
                  value={d.monthly_payment}
                  onSave={(v) => patch(d.id, { monthly_payment: v })}
                />
              </label>
              <button
                aria-label={`Hapus hutang ${d.category}`}
                onClick={() =>
                  run(
                    () => api(`/finance/debts/${d.id}`, { method: "DELETE" }),
                    "Dihapus",
                  )
                }
                className="grid size-11 place-items-center rounded-xl text-muted hover:bg-danger/10 hover:text-danger"
              >
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={add} className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field label="Kategori">
          <select name="category" className={inputCls}>
            {DEBT_CATS.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </Field>
        <Field label="Deskripsi">
          <input name="description" maxLength={200} className={inputCls} />
        </Field>
        <Field label="Total hutang">
          <input
            name="total"
            type="number"
            inputMode="numeric"
            min={1}
            required
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <Field label="Sudah dibayar">
          <input
            name="paid"
            type="number"
            inputMode="numeric"
            min={0}
            defaultValue={0}
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <Field label="Cicilan / bulan">
          <input
            name="monthly"
            type="number"
            inputMode="numeric"
            min={0}
            defaultValue={0}
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <div className="flex items-end">
          <Button type="submit" className="w-full sm:w-auto">
            Tambah hutang
          </Button>
        </div>
      </form>
    </Section>
  );
}

export function Setup() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Pockets />
      <BudgetList
        group="pemasukan"
        title="Target Pemasukan"
        hint="Kategori pemasukan dan target per bulan"
      />
      <BudgetList
        group="tagihan"
        title="Budget Tagihan"
        hint="Listrik, sewa/KPR, internet, dan tagihan tetap lain"
      />
      <BudgetList
        group="pengeluaran_harian"
        title="Budget Pengeluaran Harian"
        hint="Makan, transportasi, kesehatan, hiburan, dan lain-lain"
      />
      <SavingsPlans />
      <DebtSetup />
    </div>
  );
}
