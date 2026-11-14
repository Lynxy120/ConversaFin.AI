import { cn } from "@/lib/cn";

const V = {
  primary:
    "btn-brand font-semibold text-white shadow-lg shadow-primary/25 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-primary/35",
  ghost:
    "border border-slate-300/80 text-ink hover:bg-primary/10 dark:border-white/15 dark:hover:bg-white/10",
  quiet: "bg-slate-500/10 text-ink hover:bg-slate-500/20",
  danger:
    "bg-danger font-semibold text-white shadow-lg shadow-danger/25 hover:-translate-y-0.5",
} as const;

export function Button({
  variant = "primary",
  className,
  ...p
}: React.ComponentProps<"button"> & { variant?: keyof typeof V }) {
  return (
    <button
      className={cn(
        "inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-5 text-sm transition duration-200 disabled:pointer-events-none disabled:opacity-50",
        V[variant],
        className,
      )}
      {...p}
    />
  );
}
