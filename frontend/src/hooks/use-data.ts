import useSWR from "swr";
import { qs } from "@/lib/api";
import type { FinanceRecord, Page, Product, Summary } from "@/lib/types";

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
