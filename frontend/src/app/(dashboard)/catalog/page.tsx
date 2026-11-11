"use client";
import { useState } from "react";
import {
  Package,
  Pencil,
  Plus,
  Power,
  Search,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { ProductDialog } from "@/components/catalog/product-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Fab } from "@/components/ui/fab";
import { inputCls } from "@/components/ui/field";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProducts } from "@/hooks/use-data";
import { api } from "@/lib/api";
import { idr } from "@/lib/format";
import type { Product } from "@/lib/types";


export default function Catalog() {
  const { data, error, isLoading, mutate } = useProducts();
  const [dialog, setDialog] = useState<{ product: Product | null } | null>(
    null,
  );
  const [del, setDel] = useState<Product | null>(null);
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState("");

  const list = (data ?? []).filter((p) =>
    `${p.name} ${p.sku}`.toLowerCase().includes(q.trim().toLowerCase()),
  );

  async function remove() {
    if (!del) return;
    setBusy(true);
    try {
      await api(`/products/${del.id}`, { method: "DELETE" });
      toast.success("Product deleted");
      await mutate();
      setDel(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setBusy(false);
    }
  }

  async function activate(p: Product) {
    try {
      await api(`/products/${p.id}`, {
        method: "PATCH",
        json: { is_active: true },
      });
      toast.success("Product activated");
      await mutate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    }
  }

  return (
    <>
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-extrabold">Catalog</h1>
        <Button
          className="hidden lg:inline-flex"
          onClick={() => setDialog({ product: null })}
        >
          <Plus size={18} /> Add product
        </Button>
      </header>

      {data && data.length > 0 && (
        <div className="relative mb-4 max-w-sm">
          <Search
            size={16}
            className="absolute top-1/2 left-3 -translate-y-1/2 text-muted"
          />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search name or SKU…"
            className={`${inputCls} pl-9`}
          />
        </div>
      )}

      {error ? (
        <GlassCard className="flex flex-col items-center gap-3 p-10 text-center">
          <p className="font-bold">Couldn&apos;t load products</p>
          <p className="text-sm text-muted">{error.message}</p>
          <Button onClick={() => mutate()}>Retry</Button>
        </GlassCard>
      ) : isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <GlassCard key={i} className="p-4">
              <Skeleton className="aspect-4/3 w-full" />
              <Skeleton className="mt-4 h-5 w-2/3" />
              <Skeleton className="mt-2 h-4 w-1/3" />
            </GlassCard>
          ))}
        </div>
      ) : !data?.length ? (
        <EmptyState
          icon={Package}
          title="No products yet"
          description="Add your best-sellers now!"
          action={
            <Button onClick={() => setDialog({ product: null })}>
              <Plus size={18} /> Add product
            </Button>
          }
        />
      ) : list.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No matches"
          description={`Nothing found for “${q}”.`}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {list.map((p) => (
            <GlassCard
              key={p.id}
              className={`flex flex-col overflow-hidden ${p.is_active ? "" : "opacity-75"}`}
            >
              <div className="grid aspect-4/3 place-items-center bg-primary-light/60">
                {p.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={p.image_url}
                    alt={p.name}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    className="size-full object-cover"
                  />
                ) : (
                  <Package size={40} className="text-primary/50" />
                )}
              </div>
              <div className="flex flex-1 flex-col gap-1 p-4">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="font-bold">{p.name}</h2>
                  <Badge tone={p.is_active ? "success" : "neutral"}>
                    {p.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <p className="font-mono text-xs text-muted">{p.sku}</p>
                {p.description && (
                  <p className="line-clamp-2 text-sm text-muted">
                    {p.description}
                  </p>
                )}
                <p className="mt-2 text-lg font-extrabold tabular-nums">
                  {idr(p.price)}
                </p>
                <div className="mt-auto flex gap-2 pt-3">
                  <Button
                    variant="ghost"
                    className="flex-1"
                    onClick={() => setDialog({ product: p })}
                  >
                    <Pencil size={16} /> Edit
                  </Button>
                  {p.is_active ? (
                    <Button
                      variant="ghost"
                      className="flex-1 text-danger"
                      onClick={() => setDel(p)}
                    >
                      <Trash2 size={16} /> Delete
                    </Button>
                  ) : (
                    <Button
                      variant="ghost"
                      className="flex-1 text-success"
                      onClick={() => activate(p)}
                    >
                      <Power size={16} /> Activate
                    </Button>
                  )}
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      <Fab label="Add product" onClick={() => setDialog({ product: null })} />

      {dialog && (
        <ProductDialog
          key={dialog.product?.id ?? "new"}
          product={dialog.product}
          onClose={() => setDialog(null)}
          onSaved={() => mutate()}
        />
      )}
      <ConfirmDialog
        open={!!del}
        busy={busy}
        title={`Delete “${del?.name ?? ""}”?`}
        description="The product will be hidden from the Telegram catalog. Existing orders keep their data. You can re-activate it later."
        onConfirm={remove}
        onCancel={() => setDel(null)}
      />
    </>
  );
}
