const F = new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0,
});
export const idr = (v: number | string) => F.format(Number(v));
export const dateShort = (iso: string) =>
  new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Jakarta",
  }).format(new Date(iso));
const C = new Intl.NumberFormat("id-ID", {
  notation: "compact",
  maximumFractionDigits: 1,
});
export const compact = (v: number) => C.format(v);
export const dayLabel = (iso: string) =>
  `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
export const todayWIB = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Jakarta" }).format(
    new Date(),
  );
export const shiftDays = (iso: string, d: number) => {
  const t = new Date(`${iso}T00:00:00Z`);
  t.setUTCDate(t.getUTCDate() + d);
  return t.toISOString().slice(0, 10);
};
export const catLabel = (c?: string | null) =>
  (c ?? "other").replace(/_/g, " ").replace(/^\w/, (m) => m.toUpperCase());
