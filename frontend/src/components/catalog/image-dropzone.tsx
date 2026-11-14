"use client";
import { ImagePlus, Trash2 } from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";
import { cn } from "@/lib/cn";

const OK = ["image/jpeg", "image/png"];
const MAX = 8 * 1024 * 1024;

export function ImageDropzone({
  file,
  existingUrl,
  onFile,
  onClear,
}: {
  file: File | null;
  existingUrl?: string | null;
  onFile: (f: File) => void;
  onClear: () => void;
}) {
  const id = useId();
  const [over, setOver] = useState(false);
  const [err, setErr] = useState("");
  const preview = useMemo(
    () => (file ? URL.createObjectURL(file) : null),
    [file],
  );
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );
  const shown = preview ?? existingUrl ?? null;

  function take(f: File) {
    if (!OK.includes(f.type)) return setErr("Use a JPG or PNG image.");
    if (f.size > MAX) return setErr("Image must be 8 MB or smaller.");
    setErr("");
    onFile(f);
  }

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-semibold">Product photo</span>
      <label
        htmlFor={id}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) take(f);
        }}
        className={cn(
          "relative grid aspect-video cursor-pointer place-items-center overflow-hidden rounded-2xl border-2 border-dashed text-center transition focus-within:outline-2 focus-within:outline-primary",
          over
            ? "border-primary bg-primary/10"
            : "border-line hover:border-primary/60 hover:bg-primary/5",
        )}
      >
        <input
          id={id}
          type="file"
          accept="image/jpeg,image/png"
          className="sr-only"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) take(f);
            e.target.value = "";
          }}
        />
        {shown ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={shown}
            alt="Product preview"
            className="size-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center gap-1 px-4 text-sm">
            <span className="mb-1 grid size-12 place-items-center rounded-2xl bg-primary/10 text-primary">
              <ImagePlus size={24} />
            </span>
            <p className="font-semibold">
              Drop a photo here or <span className="text-primary">browse</span>
            </p>
            <p className="text-xs text-muted">
              JPG or PNG, up to 8 MB. Saved as WebP.
            </p>
          </div>
        )}
      </label>
      {shown && (
        <button
          type="button"
          onClick={() => {
            setErr("");
            onClear();
          }}
          className="flex min-h-11 items-center gap-2 self-start rounded-lg px-2 text-sm font-semibold text-danger hover:bg-danger/10"
        >
          <Trash2 size={16} /> Remove photo
        </button>
      )}
      {err && (
        <p role="alert" className="text-xs font-medium text-danger">
          {err}
        </p>
      )}
    </div>
  );
}
