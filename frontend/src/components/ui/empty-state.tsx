import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="glass mx-auto flex max-w-lg flex-col items-center gap-3 rounded-2xl px-6 py-14 text-center">
      <div className="relative mb-2 grid size-28 place-items-center">
        <span className="absolute inset-0 rounded-full bg-primary/10" />
        <span className="absolute inset-3 rounded-full bg-primary/15" />
        <span className="btn-brand relative grid size-16 place-items-center rounded-2xl text-white shadow-lg shadow-primary/30">
          <Icon size={30} />
        </span>
      </div>
      <h2 className="text-xl font-extrabold">{title}</h2>
      <p className="max-w-xs text-sm text-muted">{description}</p>
      {action}
    </div>
  );
}
