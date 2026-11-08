import { LogoutButton } from "@/components/layout/logout-button";
import { GlassCard } from "@/components/ui/glass-card";

export const metadata = { title: "Settings" };

export default function Settings() {
  return (
    <>
      <h1 className="mb-6 text-2xl font-extrabold">Settings</h1>
      <GlassCard className="flex flex-col gap-4 p-5">
        <p className="text-sm text-muted">KasirChat.AI · Seller dashboard</p>
        <LogoutButton className="w-full sm:w-40" />
      </GlassCard>
    </>
  );
}
