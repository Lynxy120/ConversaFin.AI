"use client";
import { X } from "lucide-react";
import { useEffect, useRef } from "react";

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && ref.current?.close()}
      className="glass m-auto max-h-[90dvh] w-[calc(100%-2rem)] max-w-lg overflow-y-auto rounded-3xl p-0 text-ink backdrop:bg-slate-900/40 backdrop:backdrop-blur-md dark:backdrop:bg-black/60"
    >
      <div className="flex items-center justify-between px-6 pt-5">
        <h2 className="text-lg font-bold">{title}</h2>
        <button
          type="button"
          aria-label="Tutup"
          onClick={() => ref.current?.close()}
          className="grid size-11 place-items-center rounded-xl text-muted hover:bg-primary/10"
        >
          <X size={20} />
        </button>
      </div>
      <div className="p-6 pt-3">{children}</div>
    </dialog>
  );
}
