import { cn } from "@/lib/cn";

const T = {
  success: "bg-success/10 text-success",
  danger: "bg-danger/10 text-danger",
  warning: "bg-warning/10 text-warning",
  info: "bg-primary/10 text-primary",
  neutral: "bg-slate-100 text-muted",
} as const;

export const Badge = ({
  tone = "neutral",
  className,
  ...p
}: React.ComponentProps<"span"> & { tone?: keyof typeof T }) => (
  <span
    className={cn(
      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold",
      T[tone],
      className,
    )}
    {...p}
  />
);
