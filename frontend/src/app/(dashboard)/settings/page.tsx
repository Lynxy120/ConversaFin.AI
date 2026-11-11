"use client";
import useSWR from "swr";
import { ExternalLink } from "lucide-react";
import { LogoutButton } from "@/components/layout/logout-button";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";

type Status = {
  bot: { id: number; username: string; name: string };
  webhook: {
    url: string | null;
    pending: number;
    last_error: string | null;
    last_error_at: number | null;
  };
};

export default function Settings() {
  const { data, error, isLoading } = useSWR<Status>("/bot/status", {
    refreshInterval: 60_000,
  });
  const healthy = !!data?.webhook.url && !data.webhook.last_error;
  return (
    <>
      <h1 className="mb-6 text-2xl font-extrabold">Settings</h1>
      <GlassCard className="mb-4 flex flex-col gap-3 p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-bold">Telegram bot</h2>
          {data && (
            <Badge tone={healthy ? "success" : "danger"}>
              {healthy ? "Connected" : "Needs attention"}
            </Badge>
          )}
        </div>
        {isLoading && <Skeleton className="h-16 w-full" />}
        {error && <p className="text-sm text-danger">{error.message}</p>}
        {data && (
          <>
            <a
              href={`https://t.me/${data.bot.username}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 font-semibold text-primary"
            >
              @{data.bot.username} <ExternalLink size={14} />
            </a>
            <p className="text-xs break-all text-muted">
              Webhook: {data.webhook.url ?? "not set"}
            </p>
            <p className="text-xs text-muted">
              Pending updates: {data.webhook.pending}
            </p>
            {data.webhook.last_error && (
              <p className="text-xs text-danger">
                Last error: {data.webhook.last_error}
              </p>
            )}
          </>
        )}
      </GlassCard>
      <GlassCard className="flex flex-col gap-4 p-5">
        <p className="text-sm text-muted">KasirChat.AI · Seller dashboard</p>
        <LogoutButton className="w-full sm:w-40" />
      </GlassCard>
    </>
  );
}
