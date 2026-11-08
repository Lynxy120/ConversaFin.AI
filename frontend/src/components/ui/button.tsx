import { cn } from "@/lib/cn";

const V = {
  primary:
    "bg-linear-135 from-primary to-blue-500 font-bold text-white shadow-sm hover:-translate-y-px hover:shadow-md",
  ghost:
    "border border-slate-200 bg-transparent text-ink hover:bg-primary-light",
  danger: "bg-danger font-bold text-white hover:-translate-y-px",
} as const;

export function Button({
  variant = "primary",
  className,
  ...p
}: React.ComponentProps<"button"> & { variant?: keyof typeof V }) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm transition duration-150",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:pointer-events-none disabled:opacity-50",
        V[variant],
        className,
      )}
      {...p}
    />
  );
}
