"use client";
import { cn } from "@/lib/cn";

export function Segmented<T extends string | number>({
  value,
  onChange,
  options,
  label,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { v: T; l: string }[];
  label: string;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className="glass inline-flex rounded-xl p-1"
    >
      {options.map((o) => (
        <button
          key={String(o.v)}
          aria-pressed={o.v === value}
          onClick={() => onChange(o.v)}
          className={cn(
            "min-h-10 rounded-lg px-4 text-sm font-semibold transition",
            o.v === value
              ? "btn-brand text-white shadow"
              : "text-muted hover:bg-primary/10",
          )}
        >
          {o.l}
        </button>
      ))}
    </div>
  );
}
