import httpx

from app.core.config import get_settings

AUDIO_MIME = {"audio/ogg", "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/aac", "audio/flac", "audio/aiff"}
IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}


class MediaError(Exception): ...


def clean_mime(m: str | None) -> str:
    return (m or "").split(";")[0].strip().lower()  # "audio/ogg; codecs=opus" -> "audio/ogg"


def validate_media(kind: str, data: bytes, mime: str | None) -> str:
    mime = clean_mime(mime)
    if not data:
        raise MediaError("File kosong.")
    if len(data) > get_settings().media_max_mb * 1024 * 1024:
        raise MediaError(f"File melebihi {get_settings().media_max_mb} MB.")
    if mime not in (AUDIO_MIME if kind == "audio" else IMAGE_MIME):
        raise MediaError(f"Format {mime or 'unknown'} tidak didukung.")
    return mime


async def download_wa_media(media_id: str) -> tuple[bytes, str]:
    s = get_settings()
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=5.0), headers={"Authorization": f"Bearer {s.wa_access_token}"}
    ) as c:
        meta = await c.get(f"https://graph.facebook.com/{s.wa_graph_version}/{media_id}")
        if meta.status_code >= 400:
            raise MediaError(f"Gagal mengambil media dari WhatsApp ({meta.status_code}).")
        j = meta.json()
        if int(j.get("file_size") or 0) > s.media_max_mb * 1024 * 1024:
            raise MediaError(f"File melebihi {s.media_max_mb} MB.")
        r = await c.get(j["url"])  # URL expires in ~5 min; requires the same Bearer token
        if r.status_code >= 400:
            raise MediaError(f"Gagal mengunduh media ({r.status_code}).")
    return r.content, clean_mime(j.get("mime_type") or r.headers.get("content-type"))