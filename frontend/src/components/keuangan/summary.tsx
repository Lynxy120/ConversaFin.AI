import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/cn";
import { idr } from "@/lib/format";
import type { CashDashboard } from "@/lib/types";

const UP = new Set(["pemasukan", "tabungan"]); // higher is better; otherwise lower is better

export function CoreSummary({ d }: { d: CashDashboard }) {
  const tone = (k: string, b: number, a: number) =>
    !b
      ? ""
      : UP.has(k)
        ? a >= b
          ? "text-success"
          : ""
        : a > b
          ? "text-danger"
          : "";
  return (
    <GlassCard className="p-5">
      <h2 className="mb-3 font-bold">Core Summary</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] text-sm">
          <thead>
            <tr className="text-left text-xs tracking-wider text-muted uppercase">
              <th className="py-2 font-semibold">Pilar</th>
              <th className="py-2 text-right font-semibold">Budget</th>
              <th className="py-2 text-right font-semibold">Aktual</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {d.summary.map((r) => (
              <tr key={r.key}>
                <th scope="row" className="py-3 text-left font-semibold">
                  {r.label}
                </th>
                <td className="py-3 text-right text-muted tabular-nums">
                  {idr(r.budget)}
                </td>
                <td
                  className={cn(
                    "py-3 text-right font-semibold tabular-nums",
                    tone(r.key, r.budget, r.actual),
                  )}
                >
                  {idr(r.actual)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-line text-base font-extrabold">
              <th scope="row" className="py-3 text-left">
                SISA
              </th>
              <td
                className={cn(
                  "py-3 text-right tabular-nums",
                  d.sisa.budget < 0 && "text-danger",
                )}
              >
                {idr(d.sisa.budget)}
              </td>
              <td
                className={cn(
                  "py-3 text-right tabular-nums",
                  d.sisa.actual < 0 ? "text-danger" : "text-success",
                )}
              >
                {idr(d.sisa.actual)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </GlassCard>
  );
}
