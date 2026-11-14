import asyncio
import io
import logging

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings
from app.core.supabase import get_supabase

log = logging.getLogger("conversafin.image")
MAX_BYTES = 8 * 1024 * 1024
MAX_SIDE = 1600
ALLOWED_FORMATS = {"JPEG", "PNG"}
Image.MAX_IMAGE_PIXELS = 40_000_000  # decompression-bomb guard


def _to_webp(raw: bytes) -> bytes:
    try:
        im = Image.open(io.BytesIO(raw))
        if (
            im.format not in ALLOWED_FORMATS
        ):  # real format sniffed from bytes, not from the client's content-type
            raise ValueError("Only JPG or PNG images are accepted")
        im = ImageOps.exif_transpose(im)
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        alpha = im.mode in ("RGBA", "LA") or (
            im.mode == "P" and "transparency" in im.info
        )
        im = im.convert("RGBA" if alpha else "RGB")
        out = io.BytesIO()
        im.save(out, "WEBP", quality=80, method=6)
        return out.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as e:
        raise ValueError("File is not a valid image") from e


async def prepare(file: UploadFile) -> bytes:
    raw = await file.read(MAX_BYTES + 1)
    if not raw:
        raise HTTPException(422, "Image is empty")
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "Image exceeds 8 MB")
    try:
        return await asyncio.to_thread(_to_webp, raw)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


async def upload(path: str, data: bytes) -> str:
    s = get_settings()
    try:
        c = await get_supabase()
        await c.storage.from_(s.product_image_bucket).upload(
            path, data, {"content-type": "image/webp", "cache-control": "31536000"}
        )
    except Exception as e:
        log.exception("storage upload failed")
        raise HTTPException(502, "Image upload failed") from e
    return f"{s.supabase_url.rstrip('/')}/storage/v1/object/public/{s.product_image_bucket}/{path}"


async def remove(path: str | None) -> None:
    if not path:
        return
    try:
        c = await get_supabase()
        await c.storage.from_(get_settings().product_image_bucket).remove([path])
    except Exception:
        log.warning("storage cleanup failed for %s", path)
