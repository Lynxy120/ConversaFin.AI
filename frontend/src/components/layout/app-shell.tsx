import { BottomNav } from "./bottom-nav";
import { Sidebar } from "./sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh lg:pl-[250px]">
      <Sidebar />
      <main className="mx-auto max-w-6xl px-4 pt-6 pb-[calc(env(safe-area-inset-bottom)+6rem)] md:px-8 lg:pb-10">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
