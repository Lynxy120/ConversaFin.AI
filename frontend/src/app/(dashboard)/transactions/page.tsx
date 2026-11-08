"use client";
import { useEffect, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  FileSpreadsheet,
  FileText,
  ReceiptText,
  RotateCcw,
  Search,
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { inputCls } from "@/components/ui/field";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRecords } from "@/hooks/use-data";
import { cn } from "@/lib/cn";
import { CATEGORIES } from "@/lib/constants";
import {
  exportPdf,
  exportXlsx,
  fetchAll,
  type RecordFilters,
} from "@/lib/export";
import { catLabel, dateShort, idr, shiftDays, todayWIB } from "@/lib/format";
import type { FinanceRecord } from "@/lib/types";

const PAGE = 25;
const init = (): RecordFilters => {
  const to = todayWIB();
  return {
    from: shiftDays(to, -29),
    to,
    domain: "",
    type: "",
    category: "",
    q: "",
  };
};
const SRC: Record<
  string,
  { l: string; t: "info" | "success" | "warning" | "neutral" }
> = {
  whatsapp: { l: "WhatsApp", t: "info" },
  midtrans: { l: "QRIS", t: "success" },
  ai: { l: "AI", t: "warning" },
  manual: { l: "Manual", t: "neutral" },
};

const Amount = ({ r }: { r: FinanceRecord }) => (
  <span
    className={cn(
      "font-bold tabular-nums",
      r.type === "income" ? "text-success" : "text-danger",
    )}
  >
    {r.type === "income" ? "+" : "−"}
    {idr(r.amount)}
  </span>
);
const SourceBadge = ({ s }: { s: string }) => (
  <Badge tone={(SRC[s] ?? SRC.manual).t}>{(SRC[s] ?? { l: s }).l}</Badge>
);
const DomainBadge = ({ d }: { d: string }) => (
  <Badge tone={d === "business" ? "info" : "neutral"}>
    {d === "business" ? "Business" : "Personal"}
  </Badge>
);

export default function Transactions() {
  const [f, setF] = useState<RecordFilters>(init);
  const [page, setPage] = useState(0);
  const [qInput, setQInput] = useState("");
  const [exporting, setExporting] = useState<"xlsx" | "pdf" | null>(null);

  const set = (p: Partial<RecordFilters>) => {
    setF((s) => ({ ...s, ...p }));
    setPage(0);
  };

  useEffect(() => {
    const t = setTimeout(() => {
      setF((s) => (s.q === qInput.trim() ? s : { ...s, q: qInput.trim() }));
      setPage(0);
    }, 350);
    return () => clearTimeout(t);
  }, [qInput]);

  const span = (Date.parse(f.to) - Date.parse(f.from)) / 864e5;
  const rangeError =
    !f.from || !f.to
      ? "Select a date range"
      : span < 0
        ? "“From” must be before “To”"
        : span > 366
          ? "Max range is 366 days"
          : "";
  const { data, error, isLoading, isValidating, mutate } = useRecords(
    rangeError ? null : { ...f, limit: PAGE, offset: page * PAGE },
  );

  const total = data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE));
  const dirty = JSON.stringify(f) !== JSON.stringify(init());
  const reset = () => {
    setF(init());
    setQInput("");
    setPage(0);
  };

  async function run(kind: "xlsx" | "pdf") {
    if (rangeError) return toast.error(rangeError);
    setExporting(kind);
    try {
      const rows = await fetchAll(f);
      if (!rows.length) return void toast.info("No transactions to export");
      await (kind === "xlsx" ? exportXlsx : exportPdf)(rows, f);
      toast.success(`${kind.toUpperCase()} exported (${rows.length} rows)`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Export failed");
    } finally {
      setExporting(null);
    }
  }

  return (
    <>
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-extrabold">Transactions</h1>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            disabled={!!exporting || !!rangeError}
            onClick={() => run("xlsx")}
          >
            <FileSpreadsheet size={18} className="text-success" />{" "}
            {exporting === "xlsx" ? "Exporting…" : "XLSX"}
          </Button>
          <Button
            variant="ghost"
            disabled={!!exporting || !!rangeError}
            onClick={() => run("pdf")}
          >
            <FileText size={18} className="text-danger" />{" "}
            {exporting === "pdf" ? "Exporting…" : "PDF"}
          </Button>
        </div>
      </header>

      <GlassCard className="mb-4 grid grid-cols-2 gap-3 p-4 lg:grid-cols-6">
        <input
          type="date"
          aria-label="From"
          value={f.from}
          max={f.to}
          onChange={(e) => set({ from: e.target.value })}
          className={inputCls}
        />
        <input
          type="date"
          aria-label="To"
          value={f.to}
          min={f.from}
          onChange={(e) => set({ to: e.target.value })}
          className={inputCls}
        />
        <select
          aria-label="Domain"
          value={f.domain}
          onChange={(e) => set({ domain: e.target.value })}
          className={inputCls}
        >
          <option value="">All domains</option>
          <option value="business">Business</option>
          <option value="personal">Personal</option>
        </select>
        <select
          aria-label="Type"
          value={f.type}
          onChange={(e) => set({ type: e.target.value })}
          className={inputCls}
        >
          <option value="">Income & expense</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <select
          aria-label="Category"
          value={f.category}
          onChange={(e) => set({ category: e.target.value })}
          className={inputCls}
        >
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {catLabel(c)}
            </option>
          ))}
        </select>
        <div className="relative col-span-2 lg:col-span-1">
          <Search
            size={16}
            className="absolute top-1/2 left-3 -translate-y-1/2 text-muted"
          />
          <input
            aria-label="Search"
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
            placeholder="Search…"
            maxLength={100}
            className={`${inputCls} pl-9`}
          />
        </div>
        {(rangeError || dirty) && (
          <div className="col-span-2 flex items-center justify-between gap-3 lg:col-span-6">
            <p role="alert" className="text-sm text-danger">
              {rangeError}
            </p>
            {dirty && (
              <Button variant="ghost" onClick={reset}>
                <RotateCcw size={16} /> Reset
              </Button>
            )}
          </div>
        )}
      </GlassCard>

      {error ? (
        <GlassCard className="flex flex-col items-center gap-3 p-10 text-center">
          <p className="font-bold">Couldn&apos;t load transactions</p>
          <p className="text-sm text-muted">{error.message}</p>
          <Button onClick={() => mutate()}>Retry</Button>
        </GlassCard>
      ) : isLoading ? (
        <GlassCard className="space-y-3 p-4">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </GlassCard>
      ) : !data?.items.length ? (
        <EmptyState
          icon={ReceiptText}
          title={dirty ? "No matching transactions" : "No transactions yet"}
          description={
            dirty
              ? "Try a wider date range or clear some filters."
              : "Send a voice note or receipt photo to your WhatsApp bot to record one."
          }
          action={
            dirty ? (
              <Button variant="ghost" onClick={reset}>
                <RotateCcw size={16} /> Reset filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          {/* Desktop table */}
          <GlassCard
            className={cn(
              "hidden overflow-hidden md:block",
              isValidating && "opacity-70",
            )}
          >
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200/70 text-xs text-muted uppercase">
                <tr>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Domain</th>
                  <th className="px-4 py-3 text-right">Amount</th>
                  <th className="px-4 py-3">Source</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-slate-100/70 last:border-0 hover:bg-primary-light/40"
                  >
                    <td className="px-4 py-3 whitespace-nowrap tabular-nums">
                      {dateShort(r.transaction_date)}
                    </td>
                    <td className="max-w-xs px-4 py-3">
                      <p className="truncate font-semibold">
                        {r.description || "-"}
                      </p>
                      {r.merchant && (
                        <p className="truncate text-xs text-muted">
                          {r.merchant}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">{catLabel(r.category)}</td>
                    <td className="px-4 py-3">
                      <DomainBadge d={r.domain} />
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <Amount r={r} />
                    </td>
                    <td className="px-4 py-3">
                      <SourceBadge s={r.source} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>

          {/* Mobile card list */}
          <ul
            className={cn("space-y-3 md:hidden", isValidating && "opacity-70")}
          >
            {data.items.map((r) => (
              <li key={r.id}>
                <GlassCard
                  className={cn(
                    "border-l-4 p-4",
                    r.type === "income"
                      ? "border-l-success"
                      : "border-l-danger",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-semibold">{r.description || "-"}</p>
                    <Amount r={r} />
                  </div>
                  {r.merchant && (
                    <p className="text-xs text-muted">{r.merchant}</p>
                  )}
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
                    <span className="tabular-nums">
                      {dateShort(r.transaction_date)}
                    </span>
                    ·<span>{catLabel(r.category)}</span>
                    <DomainBadge d={r.domain} />
                    <SourceBadge s={r.source} />
                  </div>
                </GlassCard>
              </li>
            ))}
          </ul>

          <nav
            aria-label="Pagination"
            className="mt-4 flex items-center justify-between gap-3"
          >
            <p className="text-sm text-muted tabular-nums">
              {page * PAGE + 1}–{Math.min((page + 1) * PAGE, total)} of {total}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                aria-label="Previous page"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft size={18} />
              </Button>
              <span className="text-sm tabular-nums">
                {page + 1} / {pages}
              </span>
              <Button
                variant="ghost"
                aria-label="Next page"
                disabled={page + 1 >= pages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight size={18} />
              </Button>
            </div>
          </nav>
        </>
      )}
    </>
  );
}
