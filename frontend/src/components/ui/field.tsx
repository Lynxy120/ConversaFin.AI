export const inputCls =
  "min-h-11 w-full rounded-xl border border-slate-200 bg-white/80 px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/30 read-only:bg-slate-100 read-only:text-muted";

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-semibold text-ink">{label}</span>
      {children}
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </label>
  );
}
