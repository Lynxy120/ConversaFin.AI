import useSWR from "swr";
import { qs } from "@/lib/api";
import type {
  FinanceRecord,
  Page,
  Product,
  Summary,
  Insights,
  Account,
  Budget,
  CashDashboard,
  DebtRow,
  LedgerPage,
  TxType,
  Yearly,
} from "@/lib/types";

export const useSummary = (from: string, to: string, domain?: string) =>
  useSWR<Summary>(`/finance/summary${qs({ from, to, domain })}`, {
    keepPreviousData: true,
  });

export type RecordParams = {
  from: string;
  to: string;
  domain?: string;
  type?: string;
  category?: string;
  q?: string;
  limit: number;
  offset: number;
};
export const useRecords = (p: RecordParams | null) =>
  useSWR<Page<FinanceRecord>>(p ? `/finance/records${qs(p)}` : null, {
    keepPreviousData: true,
  });

export const useProducts = () => useSWR<Product[]>("/products/all?limit=200");

export const useInsights = (days: number) =>
  useSWR<Insights>(`/analytics/insights?days=${days}`, {
    keepPreviousData: true,
  });

export const useCashDashboard = (month: string) =>
  useSWR<CashDashboard>(`/finance/dashboard?month=${month}`, {
    keepPreviousData: true,
  });
export const useYearly = (year: number) =>
  useSWR<Yearly>(`/finance/yearly?year=${year}`, { keepPreviousData: true });
export const useAccounts = (all = false) =>
  useSWR<Account[]>(`/finance/accounts${all ? "?include_inactive=true" : ""}`);
export const useBudgets = (month = "default") =>
  useSWR<Budget[]>(`/finance/budgets?month=${month}`);
export const useDebts = () => useSWR<DebtRow[]>("/finance/debts");
export const useLedger = (q: {
  month: string;
  type?: TxType | "";
  account_id?: string;
  limit: number;
  offset: number;
}) => useSWR<LedgerPage>(`/finance/ledger${qs(q)}`, { keepPreviousData: true });
