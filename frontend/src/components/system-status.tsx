"use client";
import useSWR from "swr";
import { cn } from "@/lib/cn";

type H = { ok: boolean; status: number; ms: number };

export function SystemStatus() {
  const { data, isLoading } = useSWR<H>(
    "health",
    () => fetch("/api/health").then((r) => r.json()),
    { refreshInterval: 60_000 },
  );
  const [label, tone] = isLoading
    ? [
        "Menghubungkan… (server bisa butuh ~50 dtk)",
        "bg-warning/10 text-warning",
      ]
    : data?.ok
      ? [`API online · ${data.ms} ms`, "bg-success/10 text-success"]
      : ["API offline", "bg-danger/10 text-danger"];
  return (
    <span className={cn("rounded-full px-3 py-1 text-xs font-bold", tone)}>
      {label}
    </span>
  );
}
