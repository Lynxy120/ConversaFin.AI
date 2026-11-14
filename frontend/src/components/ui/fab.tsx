"use client";
import { Plus } from "lucide-react";

export function Fab({
  label,
  onClick,
}: {
  label: string;
  onClick?: () => void;
}) {
  return (
    <button
      aria-label={label}
      onClick={onClick}
      className="glass fixed right-4 bottom-[calc(env(safe-area-inset-bottom)+6rem)] z-30 grid size-14 place-items-center rounded-2xl text-primary shadow-xl shadow-primary/30 ring-1 ring-primary/30 transition hover:-translate-y-0.5 lg:hidden"
    >
      <Plus size={26} strokeWidth={2.4} />
    </button>
  );
}
