import { cn } from "@/lib/cn";

const T = {
  success:
    "bg-success/10 text-emerald-700 ring-success/25 dark:text-emerald-300",
  warning: "bg-warning/10 text-amber-700 ring-warning/25 dark:text-amber-300",
  danger: "bg-danger/10 text-red-600 ring-danger/25 dark:text-red-300",
  info: "bg-primary/10 text-sky-700 ring-primary/25 dark:text-sky-300",
  neutral: "bg-slate-500/10 text-muted ring-slate-500/20",
} as const;

export const Badge = ({
  tone = "neutral",
  className,
  ...p
}: React.ComponentProps<"span"> & { tone?: keyof typeof T }) => (
  <span
    className={cn(
      "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold whitespace-nowrap ring-1 ring-inset",
      T[tone],
      className,
    )}
    {...p}
  />
);
