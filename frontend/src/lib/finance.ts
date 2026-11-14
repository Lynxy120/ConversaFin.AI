import { mutate } from "swr";

export const refreshFinance = () =>
  mutate((k) => typeof k === "string" && k.startsWith("/finance/"));
export const titleCase = (s: string) =>
  s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
export const ymLabel = (ym: string) =>
  new Date(`${ym}-01T00:00:00`).toLocaleDateString("id-ID", {
    month: "short",
    year: "numeric",
  });
export const num = (v: number) =>
  v.toLocaleString("id-ID", { maximumFractionDigits: 0 });
export const monthsBetween = (a: string, b: string) => {
  const [ay, am] = a.split("-").map(Number),
    [by, bm] = b.split("-").map(Number);
  return Math.max(1, (by - ay) * 12 + bm - am + 1);
};
export const monthlyNominal = (total: number, start: string, target: string) =>
  Math.ceil(total / monthsBetween(start, target));
export const POCKET_LABEL = {
  cash: "Cash",
  bank: "Bank",
  ewallet: "E-wallet",
  savings: "Tabungan",
} as const;
export const MONTHS_ID = [
  "JANUARI",
  "FEBRUARI",
  "MARET",
  "APRIL",
  "MEI",
  "JUNI",
  "JULI",
  "AGUSTUS",
  "SEPTEMBER",
  "OKTOBER",
  "NOVEMBER",
  "DESEMBER",
];
