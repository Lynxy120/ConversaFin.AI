"use client";
import { HandCoins } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { GlassCard } from "@/components/ui/glass-card";
import { Modal } from "@/components/ui/modal";
import { api } from "@/lib/api";
import { refreshFinance, titleCase } from "@/lib/finance";
import { idr, todayWIB } from "@/lib/format";
import type { DebtRow, Pocket } from "@/lib/types";

function PayDialog({
  debt,
  pockets,
  onClose,
}: {
  debt: DebtRow;
  pockets: Pocket[];
  onClose: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    const f = new FormData(e.currentTarget);
    try {
      await api(`/finance/debts/${debt.id}/pay`, {
        method: "POST",
        json: {
          amount: Number(f.get("amount")),
          account_id: f.get("account_id") || null,
          date: f.get("date"),
          notes: f.get("notes") || null,
        },
      });
      toast.success("Pembayaran tercatat");
      await refreshFinance();
      onClose();
    } catch (x) {
      setErr(x instanceof Error ? x.message : "Gagal");
      setBusy(false);
    }
  }
  return (
    <Modal title={`Bayar hutang ${titleCase(debt.category)}`} onClose={onClose}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <p className="text-sm text-muted">Sisa {idr(debt.remaining)}</p>
        <Field label="Jumlah (IDR)">
          <input
            name="amount"
            type="number"
            inputMode="numeric"
            required
            min={1}
            max={debt.remaining}
            defaultValue={debt.monthly_payment || undefined}
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <Field label="Dari pocket">
          <select
            name="account_id"
            className={inputCls}
            defaultValue={pockets.find((p) => p.is_default)?.id}
          >
            {pockets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} · {idr(p.balance)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Tanggal">
          <input
            name="date"
            type="date"
            required
            defaultValue={todayWIB()}
            className={inputCls}
          />
        </Field>
        <Field label="Catatan">
          <input name="notes" maxLength={300} className={inputCls} />
        </Field>
        {err && (
          <p role="alert" className="text-sm text-danger">
            {err}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="quiet"
            onClick={onClose}
            disabled={busy}
          >
            Batal
          </Button>
          <Button type="submit" disabled={busy}>
            {busy ? "Menyimpan…" : "Catat pembayaran"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export function DebtTracker({
  debts,
  pockets,
}: {
  debts: DebtRow[];
  pockets: Pocket[];
}) {
  const [pay, setPay] = useState<DebtRow | null>(null);
  return (
    <GlassCard className="p-5">
      <h2 className="mb-4 font-bold">DEBT TRACKER</h2>
      {debts.length === 0 ? (
        <p className="text-sm text-muted">
          Belum ada hutang. Tambahkan di tab Budgeting.
        </p>
      ) : (
        <ul className="divide-y divide-line">
          {debts.map((d) => (
            <li
              key={d.id}
              className="grid gap-3 py-4 md:grid-cols-[1.2fr_repeat(3,1fr)_auto] md:items-center"
            >
              <div className="min-w-0">
                <p className="font-semibold">
                  {titleCase(d.category)}{" "}
                  {d.status === "paid" && <Badge tone="success">Lunas</Badge>}
                </p>
                {d.description && (
                  <p className="truncate text-xs text-muted">{d.description}</p>
                )}
              </div>
              {(
                [
                  ["Total Hutang", d.total_amount],
                  ["Terbayar", d.paid_amount],
                  ["Sisa", d.remaining],
                ] as const
              ).map(([l, v]) => (
                <div key={l}>
                  <p className="text-xs text-muted">{l}</p>
                  <p className="font-bold tabular-nums">{idr(v)}</p>
                </div>
              ))}
              <Button
                variant="ghost"
                disabled={d.status === "paid"}
                onClick={() => setPay(d)}
                className="min-h-11"
              >
                <HandCoins size={16} />
                Bayar
              </Button>
              <div
                role="progressbar"
                aria-label={`Pelunasan ${titleCase(d.category)}`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(d.pct)}
                className="h-2 overflow-hidden rounded-full bg-slate-500/15 md:col-span-5"
              >
                <div
                  className="btn-brand h-full rounded-full"
                  style={{ width: `${d.pct}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
      {pay && (
        <PayDialog debt={pay} pockets={pockets} onClose={() => setPay(null)} />
      )}
    </GlassCard>
  );
}
