export async function api<T>(path: string): Promise<T> {
  const r = await fetch(`${process.env.API_URL}/api/v1${path}`, {
    headers: { "X-API-Key": process.env.ADMIN_API_KEY! },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}
export const idr = (v: number | string) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(Number(v));
