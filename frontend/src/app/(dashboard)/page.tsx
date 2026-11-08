import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { SystemStatus } from "@/components/system-status";

export const metadata = { title: "Dashboard" };

export default function Dashboard() {
  return (
    <>
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-extrabold">Dashboard</h1>
        <SystemStatus />
      </header>
      <section className="grid gap-4 sm:grid-cols-3">
        {["Revenue", "Expenses", "Profit"].map((l) => (
          <GlassCard key={l} className="p-5">
            <p className="text-sm text-muted">{l}</p>
            <Skeleton className="mt-3 h-8 w-32" />
          </GlassCard>
        ))}
      </section>
      <GlassCard className="mt-4 h-72 p-5">
        <Skeleton className="size-full" />
      </GlassCard>
    </>
  );
}
