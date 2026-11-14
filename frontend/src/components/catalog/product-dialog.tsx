"use client";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { api } from "@/lib/api";
import { shrink } from "@/lib/image";
import type { Product } from "@/lib/types";
import { ImageDropzone } from "./image-dropzone";

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
  const [file, setFile] = useState<File | null>(null);
  const [dropExisting, setDropExisting] = useState(false);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    const f = new FormData(e.currentTarget);
    const fd = new FormData();
    fd.set("name", String(f.get("name") ?? "").trim());
    fd.set("price", String(f.get("price") ?? ""));
    fd.set("description", String(f.get("description") ?? "").trim());
    fd.set("is_active", f.get("is_active") === "on" ? "true" : "false");
    try {
      if (file) fd.set("image", await shrink(file));
      else if (dropExisting) fd.set("remove_image", "true");
      await api(product ? `/products/${product.id}` : "/products", {
        method: product ? "PATCH" : "POST",
        form: fd,
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
      className="glass m-auto max-h-[90dvh] w-[calc(100%-2rem)] max-w-md overflow-y-auto rounded-3xl p-0 text-ink backdrop:bg-slate-900/40 backdrop:backdrop-blur-md dark:backdrop:bg-black/60"
    >
      <form onSubmit={submit} className="flex flex-col gap-4 p-6">
        <h2 className="text-lg font-bold">
          {product ? "Edit product" : "Add product"}
        </h2>
        <ImageDropzone
          file={file}
          existingUrl={dropExisting ? null : product?.image_url}
          onFile={(f) => {
            setFile(f);
            setDropExisting(false);
          }}
          onClear={() => {
            setFile(null);
            setDropExisting(true);
          }}
        />
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
          label="Price (IDR)"
          hint={
            product ? `SKU ${product.sku}` : "SKU is generated automatically"
          }
        >
          <input
            name="price"
            type="number"
            inputMode="numeric"
            required
            min={0}
            step={1}
            defaultValue={
              product ? Math.round(Number(product.price)) : undefined
            }
            className={`${inputCls} tabular-nums`}
          />
        </Field>
        <Field label="Description">
          <textarea
            name="description"
            rows={3}
            maxLength={500}
            defaultValue={product?.description ?? ""}
            className={`${inputCls} py-3`}
          />
        </Field>
        <label className="flex min-h-12 items-center gap-3 text-sm font-semibold">
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
            variant="quiet"
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
