import { GlassCard } from "@/components/ui/glass-card";
import type { Insights } from "@/lib/types";

export function HealthRing({ health }: { health: Insights["health"] }) {
  const R = 52,
    C = 2 * Math.PI * R;
  return (
    <GlassCard className="flex flex-col gap-5 p-5">
      <div>
        <h2 className="font-bold">Business health</h2>
        <p className="text-xs text-muted">
          Margin, growth, loyalty and payment conversion
        </p>
      </div>
      <div className="flex items-center gap-5">
        <div className="relative size-32 shrink-0">
          <svg
            viewBox="0 0 120 120"
            className="size-full -rotate-90"
            role="img"
            aria-label={`Health score ${health.score} out of 100`}
          >
            <defs>
              <linearGradient id="hg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#0EA5E9" />
                <stop offset="100%" stopColor="#3B82F6" />
              </linearGradient>
            </defs>
            <circle
              cx="60"
              cy="60"
              r={R}
              fill="none"
              stroke="var(--line)"
              strokeWidth="10"
            />
            <circle
              cx="60"
              cy="60"
              r={R}
              fill="none"
              stroke="url(#hg)"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${(C * health.score) / 100} ${C}`}
              className="dark:drop-shadow-[0_0_6px_rgba(14,165,233,.6)]"
            />
          </svg>
          <div className="absolute inset-0 grid place-items-center text-center">
            <div>
              <p className="text-3xl font-extrabold tabular-nums">
                {health.score}
              </p>
              <p className="text-[11px] font-semibold text-primary">
                {health.label}
              </p>
            </div>
          </div>
        </div>
        <ul className="min-w-0 flex-1 space-y-3">
          {health.parts.map((p) => (
            <li key={p.key}>
              <div className="mb-1 flex justify-between text-xs">
                <span className="font-semibold">{p.label}</span>
                <span className="tabular-nums text-muted">
                  {p.value == null
                    ? "n/a"
                    : `${p.value}${p.key === "growth" || p.key === "margin" || p.key === "loyalty" || p.key === "conversion" ? "%" : ""}`}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-slate-500/15">
                <div
                  className="btn-brand h-full rounded-full"
                  style={{ width: `${p.score}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </GlassCard>
  );
}
