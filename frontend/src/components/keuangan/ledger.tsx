"use client";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { inputCls } from "@/components/ui/field";
import { useAccounts, useLedger } from "@/hooks/use-data";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { refreshFinance, titleCase } from "@/lib/finance";
import { dateShort, idr } from "@/lib/format";
import type { LedgerRow, TxType } from "@/lib/types";
import { TxDialog } from "./tx-dialog";

const LIMIT = 15;
const TONE = {
  income: "success",
  expense: "danger",
  in: "info",
  out: "warning",
} as const;
const FILTERS: { v: TxType | ""; l: string }[] = [
  { v: "", l: "Semua" },
  { v: "income", l: "Income" },
  { v: "expense", l: "Expense" },
  { v: "in", l: "In" },
  { v: "out", l: "Out" },
];

export function Ledger({
  month,
  categories,
}: {
  month: string;
  categories: string[];
}) {
  const [type, setType] = useState<TxType | "">("");
  const [account, setAccount] = useState("");
  const [offset, setOffset] = useState(0);
  const [add, setAdd] = useState(false);
  const [del, setDel] = useState<LedgerRow | null>(null);
  const [busy, setBusy] = useState(false);
  const { data: accounts = [] } = useAccounts();
  const { data, isLoading } = useLedger({
    month,
    type,
    account_id: account,
    limit: LIMIT,
    offset,
  });
  const total = data?.total ?? 0;

  async function remove() {
    if (!del) return;
    setBusy(true);
    try {
      await api(`/finance/ledger/${del.id}`, { method: "DELETE" });
      toast.success("Transaksi dihapus");
      await refreshFinance();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Gagal menghapus");
    } finally {
      setBusy(false);
      setDel(null);
    }
  }

  return (
    <GlassCard className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-bold">REKAPAN TRANSAKSI</h2>
        <Button onClick={() => setAdd(true)}>
          <Plus size={18} />
          Add Transaction
        </Button>
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div
          role="group"
          aria-label="Filter tipe"
          className="no-scrollbar flex gap-1 overflow-x-auto"
        >
          {FILTERS.map((f) => (
            <button
              key={f.v}
              aria-pressed={type === f.v}
              onClick={() => {
                setType(f.v);
                setOffset(0);
              }}
              className={cn(
                "min-h-11 shrink-0 rounded-xl px-3 text-sm font-semibold transition",
                type === f.v
                  ? "btn-brand text-white"
                  : "text-muted hover:bg-primary/10",
              )}
            >
              {f.l}
            </button>
          ))}
        </div>
        <select
          aria-label="Filter pocket"
          value={account}
          onChange={(e) => {
            setAccount(e.target.value);
            setOffset(0);
          }}
          className={`${inputCls} max-w-44`}
        >
          <option value="">Semua pocket</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : !data?.items.length ? (
        <EmptyState
          icon={Plus}
          title="Belum ada transaksi"
          description="Catat lewat tombol Add Transaction atau kirim ke bot Telegram."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="text-left text-xs tracking-wider text-muted uppercase">
                {[
                  "Type",
                  "Date",
                  "Account",
                  "Category",
                  "Description",
                  "Amount",
                  "Notes",
                  "",
                ].map((h, i) => (
                  <th
                    key={i}
                    className={cn(
                      "py-2 pr-3 font-semibold",
                      h === "Amount" && "text-right",
                    )}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.items.map((r) => {
                const plus = r.type === "income" || r.type === "in";
                return (
                  <tr key={r.id}>
                    <td className="py-3 pr-3">
                      <Badge tone={TONE[r.type]}>{titleCase(r.type)}</Badge>
                    </td>
                    <td className="py-3 pr-3 whitespace-nowrap tabular-nums">
                      {dateShort(r.transaction_date)}
                    </td>
                    <td className="py-3 pr-3">
                      {r.finance_accounts?.name ?? "–"}
                    </td>
                    <td className="py-3 pr-3">
                      {titleCase(r.category ?? "lainnya")}
                    </td>
                    <td className="max-w-48 truncate py-3 pr-3 text-muted">
                      {r.description ?? "–"}
                    </td>
                    <td
                      className={cn(
                        "py-3 pr-3 text-right font-semibold whitespace-nowrap tabular-nums",
                        plus ? "text-success" : "text-danger",
                      )}
                    >
                      {plus ? "+" : "−"}
                      {idr(r.amount)}
                    </td>
                    <td className="max-w-40 truncate py-3 pr-3 text-muted">
                      {r.notes ?? ""}
                    </td>
                    <td className="py-1">
                      {!r.debt_id && (
                        <button
                          aria-label="Hapus transaksi"
                          onClick={() => setDel(r)}
                          className="grid size-11 place-items-center rounded-xl text-muted hover:bg-danger/10 hover:text-danger"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {total > LIMIT && (
        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-muted tabular-nums">
            {offset + 1}–{Math.min(offset + LIMIT, total)} dari {total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
            >
              Sebelumnya
            </Button>
            <Button
              variant="ghost"
              disabled={offset + LIMIT >= total}
              onClick={() => setOffset(offset + LIMIT)}
            >
              Berikutnya
            </Button>
          </div>
        </div>
      )}

      {add && (
        <TxDialog
          accounts={accounts}
          categories={categories}
          onClose={() => setAdd(false)}
        />
      )}
      <ConfirmDialog
        open={!!del}
        busy={busy}
        confirmLabel="Hapus"
        title="Hapus transaksi ini?"
        description="Saldo pocket akan dihitung ulang. Tindakan ini tidak bisa dibatalkan."
        onConfirm={remove}
        onCancel={() => setDel(null)}
      />
    </GlassCard>
  );
}
