"use client";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { Segmented } from "@/components/ui/segmented";
import { api } from "@/lib/api";
import { refreshFinance, titleCase } from "@/lib/finance";
import { todayWIB } from "@/lib/format";
import type { Account, TxType } from "@/lib/types";

const TYPES: { v: TxType; l: string }[] = [
  { v: "expense", l: "Expense" },
  { v: "income", l: "Income" },
  { v: "in", l: "In" },
  { v: "out", l: "Out" },
];
const HINT: Record<TxType, string> = {
  expense: "Uang keluar",
  income: "Uang masuk dari pemasukan",
  in: "Transfer masuk / saldo awal",
  out: "Transfer keluar / alokasi tabungan",
};

export function TxDialog({
  accounts,
  categories,
  onClose,
}: {
  accounts: Account[];
  categories: string[];
  onClose: () => void;
}) {
  const [type, setType] = useState<TxType>("expense");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    const f = new FormData(e.currentTarget);
    try {
      await api("/finance/ledger", {
        method: "POST",
        json: {
          type,
          date: f.get("date"),
          account_id: f.get("account_id") || null,
          group_type: f.get("group_type") || null,
          category: String(f.get("category")).trim(),
          description: f.get("description") || null,
          amount: Number(f.get("amount")),
          notes: f.get("notes") || null,
        },
      });
      toast.success("Transaksi tersimpan");
      await refreshFinance();
      onClose();
    } catch (x) {
      setErr(x instanceof Error ? x.message : "Gagal menyimpan");
      setBusy(false);
    }
  }

  return (
    <Modal title="Add Transaction" onClose={onClose}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div>
          <Segmented
            label="Tipe transaksi"
            value={type}
            onChange={setType}
            options={TYPES}
          />
          <p className="mt-2 text-xs text-muted">{HINT[type]}</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Tanggal">
            <input
              name="date"
              type="date"
              required
              defaultValue={todayWIB()}
              className={inputCls}
            />
          </Field>
          <Field label="Jumlah (IDR)">
            <input
              name="amount"
              type="number"
              inputMode="numeric"
              required
              min={1}
              className={`${inputCls} tabular-nums`}
            />
          </Field>
        </div>
        <Field label="Pocket">
          <select
            name="account_id"
            className={inputCls}
            defaultValue={accounts.find((a) => a.is_default)?.id}
          >
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </Field>
        {type === "expense" && (
          <Field label="Kelompok">
            <select
              name="group_type"
              className={inputCls}
              defaultValue="pengeluaran_harian"
            >
              <option value="pengeluaran_harian">Pengeluaran harian</option>
              <option value="tagihan">Tagihan</option>
            </select>
          </Field>
        )}
        {(type === "in" || type === "out") && (
          <Field label="Kelompok">
            <select name="group_type" className={inputCls} defaultValue="">
              <option value="">Transfer biasa</option>
              <option value="tabungan">Tabungan</option>
            </select>
          </Field>
        )}
        <Field label="Kategori">
          <input
            name="category"
            required
            maxLength={60}
            list="tx-cats"
            className={inputCls}
          />
          <datalist id="tx-cats">
            {categories.map((c) => (
              <option key={c} value={titleCase(c)} />
            ))}
          </datalist>
        </Field>
        <Field label="Deskripsi">
          <input name="description" maxLength={200} className={inputCls} />
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
            {busy ? "Menyimpan…" : "Simpan"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
