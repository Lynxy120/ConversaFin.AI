import httpx

from app.core.config import get_settings

AUDIO_MIME = {
    "audio/ogg",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/aac",
    "audio/flac",
    "audio/aiff",
}
IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}


class MediaError(Exception): ...


def clean_mime(m: str | None) -> str:
    return (
        (m or "").split(";")[0].strip().lower()
    )  # "audio/ogg; codecs=opus" -> "audio/ogg"


def validate_media(kind: str, data: bytes, mime: str | None) -> str:
    mime = clean_mime(mime)
    if not data:
        raise MediaError("File kosong.")
    if len(data) > get_settings().media_max_mb * 1024 * 1024:
        raise MediaError(f"File melebihi {get_settings().media_max_mb} MB.")
    if mime not in (AUDIO_MIME if kind == "audio" else IMAGE_MIME):
        raise MediaError(f"Format {mime or 'unknown'} tidak didukung.")
    return mime


async def download_telegram_media(file_id: str) -> tuple[bytes, str]:
    s = get_settings()
    # Telegram API URLs
    meta_url = (
        f"https://api.telegram.org/bot{s.telegram_bot_token}/getFile?file_id={file_id}"
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as c:
        # 1. Fetch file path and metadata
        meta = await c.get(meta_url)
        if meta.status_code >= 400:
            raise MediaError(
                f"Gagal mengambil metadata media dari Telegram ({meta.status_code})."
            )

        j = meta.json()
        if not j.get("ok"):
            raise MediaError("Telegram API mengembalikan response tidak valid.")

        result = j.get("result", {})
        file_path = result.get("file_path")

        if not file_path:
            raise MediaError("File path tidak ditemukan dari Telegram API.")

        if int(result.get("file_size") or 0) > s.media_max_mb * 1024 * 1024:
            raise MediaError(f"File melebihi {s.media_max_mb} MB.")

        # 2. Download the actual binary file
        download_url = (
            f"https://api.telegram.org/file/bot{s.telegram_bot_token}/{file_path}"
        )
        r = await c.get(download_url)
        if r.status_code >= 400:
            raise MediaError(f"Gagal mengunduh media dari Telegram ({r.status_code}).")

    # Derive MIME type from response headers
    mime_type = clean_mime(r.headers.get("content-type"))
    return r.content, mime_type
