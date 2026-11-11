import asyncio
import logging
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import Settings, get_settings

log = logging.getLogger("conversafin.telegram")
API = "https://api.telegram.org"
DRY = {
    "sendMessage",
    "sendPhoto",
    "sendDocument",
    "editMessageText",
    "answerCallbackQuery",
    "sendChatAction",
}


class TelegramError(Exception): ...


def kb(rows: list[list[tuple[str, str]]]) -> dict[str, Any]:
    """rows of (label, callback_data); callback_data <= 64 bytes."""
    return {
        "inline_keyboard": [
            [{"text": t, "callback_data": d} for t, d in r] for r in rows
        ]
    }


class TelegramClient:
    def __init__(self, s: Settings | None = None) -> None:
        self._s = s or get_settings()
        self._c: httpx.AsyncClient | None = None
        if self._s.telegram_dry_run:
            log.warning("TELEGRAM_DRY_RUN=true: outbound messages are logged, NOT sent")

    @property
    def http(self) -> httpx.AsyncClient:
        if self._c is None or self._c.is_closed:
            self._c = httpx.AsyncClient(timeout=httpx.Timeout(35.0, connect=5.0))
        return self._c

    async def aclose(self) -> None:
        if self._c and not self._c.is_closed:
            await self._c.aclose()

    async def call(
        self,
        method: str,
        *,
        payload: dict | None = None,
        data: dict | None = None,
        files: dict | None = None,
        retries: int = 2,
    ) -> dict[str, Any]:
        if self._s.telegram_dry_run and method in DRY:
            log.info("[dry-run] %s %s", method, str(payload or data)[:300])
            return {"ok": True, "dry_run": True, "result": {"message_id": 0}}
        if not self._s.telegram_bot_token:
            log.error("TELEGRAM_BOT_TOKEN is empty")
            return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}
        url = f"{API}/bot{self._s.telegram_bot_token}/{method}"  # never log url (contains token)
        last: dict[str, Any] = {"ok": False, "error": "unknown"}
        for i in range(retries + 1):
            try:
                r = await self.http.post(url, json=payload, data=data, files=files)
            except httpx.TransportError as e:
                last = {"ok": False, "error": f"transport: {e!r}"}
                log.warning("TG %s transport error attempt=%d: %r", method, i + 1, e)
            else:
                try:
                    j = r.json()
                except ValueError:
                    j = {"ok": False, "description": r.text[:200]}
                if j.get("ok"):
                    return {"ok": True, "result": j["result"]}
                code = int(j.get("error_code", r.status_code))
                log.error(
                    "TG %s REJECTED http=%s code=%s desc=%s",
                    method,
                    r.status_code,
                    code,
                    j.get("description"),
                )
                last = {"ok": False, "status": code, "error": j.get("description")}
                if code == 429:
                    await asyncio.sleep(
                        min(j.get("parameters", {}).get("retry_after", 1), 10)
                    )
                    continue
                if code < 500:
                    return last
            if i < retries:
                await asyncio.sleep(0.5 * 2**i)
        return last

    # ---- messaging ----
    async def send_message(
        self, chat_id: int | str, text: str, markup: dict | None = None
    ) -> dict[str, Any]:
        p: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text[:4096],
            "disable_web_page_preview": True,
        }
        if markup:
            p["reply_markup"] = markup
        return await self.call("sendMessage", payload=p)

    async def edit_message(
        self, chat_id: int, message_id: int, text: str, markup: dict | None = None
    ) -> dict[str, Any]:
        p: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text[:4096],
            "disable_web_page_preview": True,
        }
        if markup:
            p["reply_markup"] = markup
        r = await self.call("editMessageText", payload=p)
        if not r["ok"] and "not modified" in str(r.get("error")):
            return {"ok": True}
        return r

    async def answer_callback(
        self, cb_id: str, text: str | None = None, alert: bool = False
    ) -> dict[str, Any]:
        return await self.call(
            "answerCallbackQuery",
            payload={
                "callback_query_id": cb_id,
                "text": text or "",
                "show_alert": alert,
            },
        )

    async def chat_action(self, chat_id: int, action: str = "typing") -> dict[str, Any]:
        return await self.call(
            "sendChatAction", payload={"chat_id": chat_id, "action": action}
        )

    async def send_photo(
        self, chat_id: int, photo: bytes | str, caption: str | None = None
    ) -> dict[str, Any]:
        if isinstance(photo, str):
            return await self.call(
                "sendPhoto",
                payload={
                    "chat_id": chat_id,
                    "photo": photo,
                    **({"caption": caption[:1024]} if caption else {}),
                },
            )
        return await self.call(
            "sendPhoto",
            data={
                "chat_id": str(chat_id),
                **({"caption": caption[:1024]} if caption else {}),
            },
            files={"photo": ("qris.png", photo, "image/png")},
        )

    async def send_document(
        self, chat_id: int, content: bytes, filename: str, caption: str | None = None
    ) -> dict[str, Any]:
        return await self.call(
            "sendDocument",
            data={
                "chat_id": str(chat_id),
                **({"caption": caption[:1024]} if caption else {}),
            },
            files={"document": (filename, content, "application/pdf")},
        )

    async def get_file_bytes(self, file_id: str, max_bytes: int) -> bytes:
        r = await self.call("getFile", payload={"file_id": file_id})
        if not r["ok"]:
            raise TelegramError(f"getFile failed: {r.get('error')}")
        meta = r["result"]
        if int(meta.get("file_size") or 0) > max_bytes:
            raise TelegramError("File terlalu besar.")
        resp = await self.http.get(
            f"{API}/file/bot{self._s.telegram_bot_token}/{meta['file_path']}"
        )
        if resp.status_code != 200:
            raise TelegramError(f"download failed {resp.status_code}")
        return resp.content

    # ---- webhook admin ----
    async def set_webhook(self, url: str, secret: str) -> dict[str, Any]:
        return await self.call(
            "setWebhook",
            payload={
                "url": url,
                "secret_token": secret,
                "max_connections": 20,
                "allowed_updates": ["message", "callback_query"],
            },
        )

    async def get_webhook_info(self) -> dict[str, Any]:
        return await self.call("getWebhookInfo")

    async def get_me(self) -> dict[str, Any]:
        return await self.call("getMe")


@lru_cache
def get_telegram_client() -> TelegramClient:
    return TelegramClient()
