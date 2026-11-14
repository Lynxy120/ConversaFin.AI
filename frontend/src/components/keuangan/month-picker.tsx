"use client";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { ymLabel } from "@/lib/finance";

const M = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "Mei",
  "Jun",
  "Jul",
  "Agu",
  "Sep",
  "Okt",
  "Nov",
  "Des",
];

export function MonthPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [year, setYear] = useState(Number(value.slice(0, 4)));
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const away = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", away);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", away);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => {
          setYear(Number(value.slice(0, 4)));
          setOpen((o) => !o);
        }}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label="Pick Your Time"
        className="glass flex min-h-12 items-center gap-2 rounded-xl px-4 text-sm font-semibold"
      >
        <CalendarDays size={18} className="text-primary" /> {ymLabel(value)}
      </button>
      {open && (
        <div
          role="dialog"
          aria-label="Pick Your Time"
          className="glass absolute right-0 z-40 mt-2 w-72 rounded-2xl p-4 shadow-xl"
        >
          <div className="mb-3 flex items-center justify-between">
            <button
              aria-label="Tahun sebelumnya"
              onClick={() => setYear((y) => y - 1)}
              className="grid size-11 place-items-center rounded-xl hover:bg-primary/10"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="font-bold tabular-nums">{year}</span>
            <button
              aria-label="Tahun berikutnya"
              onClick={() => setYear((y) => y + 1)}
              className="grid size-11 place-items-center rounded-xl hover:bg-primary/10"
            >
              <ChevronRight size={18} />
            </button>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {M.map((m, i) => {
              const v = `${year}-${String(i + 1).padStart(2, "0")}`;
              return (
                <button
                  key={v}
                  onClick={() => {
                    onChange(v);
                    setOpen(false);
                  }}
                  className={cn(
                    "min-h-11 rounded-xl text-sm font-semibold transition",
                    v === value
                      ? "btn-brand text-white"
                      : "hover:bg-primary/10",
                  )}
                >
                  {m}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
