"use client";
import { useState } from "react";
import useSWR from "swr";
import {
  Check,
  ChefHat,
  ClipboardCheck,
  Clock,
  PackageCheck,
  QrCode,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { ago, idr, minutesSince } from "@/lib/format";
import type { Bucket, Order, TaskBoard } from "@/lib/types";

type Move = "preparing" | "ready" | "completed" | "cancelled";

const TABS: { id: Bucket; label: string; icon: typeof Clock; empty: string }[] =
  [
    {
      id: "new",
      label: "To prepare",
      icon: ClipboardCheck,
      empty:
        "No paid orders waiting. New ones appear here the moment they are paid.",
    },
    {
      id: "preparing",
      label: "Preparing",
      icon: ChefHat,
      empty: "Nothing in preparation right now.",
    },
    {
      id: "ready",
      label: "Ready",
      icon: PackageCheck,
      empty: "No orders waiting for pickup.",
    },
    {
      id: "unpaid",
      label: "Awaiting payment",
      icon: QrCode,
      empty: "No unpaid orders. Everything placed has been paid.",
    },
  ];
const NEXT: Partial<Record<Bucket, { to: Move; label: string }>> = {
  new: { to: "preparing", label: "Start preparing" },
  preparing: { to: "ready", label: "Mark ready" },
  ready: { to: "completed", label: "Complete order" },
};
const DONE: Record<Move, string> = {
  preparing: "Order moved to preparing",
  ready: "Order is ready. Customer notified",
  completed: "Order completed",
  cancelled: "Order cancelled",
};
const bucketOf = (o: Order): Bucket =>
  o.status === "pending" ? "unpaid" : (o.fulfillment_status as Bucket);

export default function OrdersPage() {
  const { data, error, isLoading, mutate } = useSWR<TaskBoard>(
    "/orders/tasks",
    { refreshInterval: 15_000, revalidateOnFocus: true },
  );
  const [tab, setTab] = useState<Bucket>("new");
  const [busy, setBusy] = useState<string | null>(null);
  const [cancelFor, setCancelFor] = useState<Order | null>(null);

  async function move(o: Order, status: Move) {
    setBusy(o.id);
    try {
      await api(`/orders/${o.id}/fulfillment`, {
        method: "PATCH",
        json: { status },
      });
      toast.success(DONE[status]);
      await mutate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(null);
      setCancelFor(null);
    }
  }

  const items = (data?.items ?? []).filter((o) => bucketOf(o) === tab);
  const total = data
    ? Object.values(data.counts).reduce((s, n) => s + n, 0)
    : 0;
  const active = TABS.find((t) => t.id === tab)!;

  return (
    <>
      <header className="mb-6">
        <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
          Orders
        </h1>
        <p className="mt-1 text-sm text-muted">
          {total
            ? `${total} open ${total === 1 ? "task" : "tasks"}, oldest first`
            : "Track what still needs your attention"}
        </p>
      </header>

      <div
        role="tablist"
        aria-label="Order stages"
        className="no-scrollbar -mx-1 mb-5 flex gap-2 overflow-x-auto px-1 py-1"
      >
        {TABS.map((t) => {
          const on = tab === t.id;
          const n = data?.counts[t.id] ?? 0;
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={on}
              onClick={() => setTab(t.id)}
              className={cn(
                "flex min-h-12 shrink-0 items-center gap-2 rounded-xl px-4 text-sm font-semibold transition",
                on
                  ? "btn-brand text-white shadow-md shadow-primary/25"
                  : "glass text-muted hover:bg-primary/10",
              )}
            >
              <t.icon size={17} />
              {t.label}
              <span
                className={cn(
                  "grid min-w-6 place-items-center rounded-full px-1.5 text-xs tabular-nums",
                  on ? "bg-white/25" : "bg-primary/10 text-primary",
                )}
              >
                {n}
              </span>
            </button>
          );
        })}
      </div>

      {error ? (
        <GlassCard className="flex flex-col items-center gap-3 p-10 text-center">
          <p className="font-bold">Couldn&apos;t load orders</p>
          <p className="text-sm text-muted">{error.message}</p>
          <Button onClick={() => mutate()}>Retry</Button>
        </GlassCard>
      ) : isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <GlassCard key={i} className="space-y-3 p-5">
              <Skeleton className="h-5 w-1/2" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-12 w-full" />
            </GlassCard>
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={active.icon}
          title="All caught up"
          description={active.empty}
        />
      ) : (
        <ul className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((o) => {
            const b = bucketOf(o);
            const next = NEXT[b];
            const waiting = minutesSince(o.paid_at ?? o.created_at);
            const late = b === "new" && waiting >= 30;
            const qrisGone =
              b === "unpaid" &&
              !!o.payment_expires_at &&
              new Date(o.payment_expires_at) < new Date();
            return (
              <li key={o.id}>
                <GlassCard className="flex h-full flex-col gap-4 p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-bold">
                        #{o.id.slice(0, 8).toUpperCase()}
                      </p>
                      <p className="truncate text-sm text-muted">
                        {o.customer_name ?? "Customer"} · Telegram {o.chat_id}
                      </p>
                    </div>
                    {b === "unpaid" ? (
                      <Badge tone={qrisGone ? "neutral" : "warning"}>
                        {qrisGone ? "QRIS expired" : "Pending QRIS"}
                      </Badge>
                    ) : (
                      <Badge tone={late ? "warning" : "success"}>
                        {late ? `Waiting ${waiting} min` : "Paid"}
                      </Badge>
                    )}
                  </div>
                  <ul className="space-y-1.5 text-sm">
                    {o.order_items.map((i) => (
                      <li key={i.id} className="flex justify-between gap-3">
                        <span className="truncate">
                          {i.product_name}{" "}
                          <span className="text-muted">×{i.quantity}</span>
                        </span>
                        <span className="tabular-nums text-muted">
                          {idr(i.subtotal)}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-auto flex items-center justify-between border-t border-line pt-3">
                    <span className="flex items-center gap-1.5 text-xs text-muted">
                      <Clock size={14} />
                      {ago(o.paid_at ?? o.created_at)}
                    </span>
                    <span className="text-lg font-extrabold tabular-nums">
                      {idr(o.total_price)}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {next && (
                      <Button
                        className="flex-1"
                        disabled={busy === o.id}
                        onClick={() => move(o, next.to)}
                      >
                        <Check size={18} />
                        {busy === o.id ? "Saving…" : next.label}
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      className={cn(
                        !next && "flex-1",
                        "hover:bg-danger/10 hover:text-danger",
                      )}
                      disabled={busy === o.id}
                      aria-label={`Cancel order ${o.id.slice(0, 8)}`}
                      onClick={() => setCancelFor(o)}
                    >
                      <X size={18} />
                      {!next && "Cancel order"}
                    </Button>
                  </div>
                </GlassCard>
              </li>
            );
          })}
        </ul>
      )}

      <ConfirmDialog
        open={!!cancelFor}
        busy={!!busy}
        confirmLabel="Cancel order"
        title={`Cancel order #${cancelFor?.id.slice(0, 8).toUpperCase() ?? ""}?`}
        description={
          cancelFor?.status === "paid"
            ? "This customer already paid. Cancelling does not refund automatically: send the refund yourself. The customer is notified on Telegram."
            : "The QRIS code is voided so it can no longer be paid. The customer is notified on Telegram."
        }
        onConfirm={() => cancelFor && move(cancelFor, "cancelled")}
        onCancel={() => setCancelFor(null)}
      />
    </>
  );
}
