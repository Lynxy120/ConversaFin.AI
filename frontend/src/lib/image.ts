const LIMIT = 3 * 1024 * 1024; // Vercel route handlers reject request bodies above 4.5 MB

export async function shrink(file: File, max = 1600): Promise<File> {
  if (file.size <= LIMIT) return file;
  const bmp = await createImageBitmap(file);
  const k = Math.min(1, max / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas");
  c.width = Math.round(bmp.width * k);
  c.height = Math.round(bmp.height * k);
  c.getContext("2d")!.drawImage(bmp, 0, 0, c.width, c.height);
  bmp.close();
  const blob = await new Promise<Blob | null>((r) =>
    c.toBlob(r, "image/jpeg", 0.85),
  );
  return blob
    ? new File([blob], file.name.replace(/\.\w+$/, "") + ".jpg", {
        type: "image/jpeg",
      })
    : file;
}
