import { BottomNav } from "./bottom-nav";
import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh lg:pl-65">
      <Sidebar />
      <TopBar />
      <main className="mx-auto max-w-6xl px-4 pt-6 pb-[calc(env(safe-area-inset-bottom)+7rem)] md:px-8 lg:pb-10">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
