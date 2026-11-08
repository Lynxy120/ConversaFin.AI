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
      className="fixed right-4 bottom-[calc(env(safe-area-inset-bottom)+5rem)] z-20 grid size-14 place-items-center rounded-full bg-linear-135 from-primary to-blue-500 text-white shadow-lg transition hover:-translate-y-px lg:right-8 lg:bottom-8"
    >
      <Plus size={26} />
    </button>
  );
}
