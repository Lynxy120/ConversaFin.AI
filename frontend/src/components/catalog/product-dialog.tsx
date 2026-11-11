"use client";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";

export function ProductDialog({
  product,
  onClose,
  onSaved,
}: {
  product: Product | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    const f = new FormData(e.currentTarget);
    const t = (k: string) => String(f.get(k) ?? "").trim();
    const body = {
      name: t("name"),
      description: t("description") || null,
      price: Number(f.get("price")),
      image_url: t("image_url") || null,
      is_active: f.get("is_active") === "on",
    };
    try {
      if (product)
        await api(`/products/${product.id}`, { method: "PATCH", json: body });
      else
        await api("/products", {
          method: "POST",
          json: { sku: t("sku"), ...body },
        });
      toast.success(
        product ? "Product updated successfully" : "Product added successfully",
      );
      onSaved();
      ref.current?.close();
    } catch (x) {
      setErr(x instanceof Error ? x.message : "Failed to save");
      setBusy(false);
    }
  }

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && ref.current?.close()}
      className="glass m-auto max-h-[90dvh] w-[calc(100%-2rem)] max-w-md overflow-y-auto rounded-2xl p-0 text-ink backdrop:bg-slate-900/30 backdrop:backdrop-blur-sm"
    >
      <form onSubmit={submit} className="flex flex-col gap-4 p-6">
        <h2 className="text-lg font-bold">
          {product ? "Edit product" : "Add product"}
        </h2>
        <Field label="Name">
          <input
            name="name"
            required
            maxLength={150}
            defaultValue={product?.name}
            className={inputCls}
          />
        </Field>
        <Field
          label="SKU"
          hint={
            product ? "SKU cannot be changed" : "Letters, numbers, - and _ only"
          }
        >
          <input
            name="sku"
            required
            pattern="[A-Za-z0-9_\-]{1,100}"
            defaultValue={product?.sku}
            readOnly={!!product}
            className={inputCls}
          />
        </Field>
        <Field label="Price (IDR)">
          <input
            name="price"
            type="number"
            inputMode="numeric"
            required
            min={0}
            max={999999999999}
            step={1}
            defaultValue={
              product ? Math.round(Number(product.price)) : undefined
            }
            className={inputCls}
          />
        </Field>
        <Field label="Image URL" hint="Optional. Public https link.">
          <input
            name="image_url"
            type="url"
            defaultValue={product?.image_url ?? ""}
            placeholder="https://…"
            className={inputCls}
          />
        </Field>
        <Field label="Description">
          <textarea
            name="description"
            rows={3}
            maxLength={500}
            defaultValue={product?.description ?? ""}
            className={`${inputCls} py-2`}
          />
        </Field>
        <label className="flex min-h-11 items-center gap-3 text-sm font-semibold">
          <input
            name="is_active"
            type="checkbox"
            defaultChecked={product?.is_active ?? true}
            className="size-5 accent-primary"
          />
          Active (shown in Telegram catalog)
        </label>
        {err && (
          <p role="alert" className="text-sm text-danger">
            {err}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="ghost"
            onClick={() => ref.current?.close()}
            disabled={busy}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </dialog>
  );
}
