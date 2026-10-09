import asyncio
import logging
import re
from collections import deque
from datetime import datetime, timezone
from enum import StrEnum
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.schemas.webhooks import Message, WebhookPayload

logger = logging.getLogger("conversafin.whatsapp")

_MAX_SEEN_IDS = 5000


class Role(StrEnum):
    OWNER = "owner"
    CUSTOMER = "customer"


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    return digits


class WhatsAppService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        self._seen_ids: dict[str, None] = {}
        self.events: deque[dict[str, Any]] = deque(maxlen=200)
        self._owner_numbers: set[str] = {
            normalize_phone(n)
            for n in self._settings.wa_owner_number.split(",")
            if n.strip()
        }

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"https://graph.facebook.com/{self._settings.wa_graph_version}",
                timeout=httpx.Timeout(10.0, connect=5.0),
                headers={
                    "Authorization": f"Bearer {self._settings.wa_access_token}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def resolve_role(self, phone: str) -> Role:
        return Role.OWNER if normalize_phone(phone) in self._owner_numbers else Role.CUSTOMER

    async def send_text_message(self, to: str, body: str, *, retries: int = 2) -> dict[str, Any]:
        if self._settings.wa_dry_run:
            logger.info("[dry-run] -> %s: %s", to, body)
            return {"ok": True, "dry_run": True}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalize_phone(to),
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        url = f"/{self._settings.wa_phone_number_id}/messages"
        last: dict[str, Any] = {"ok": False, "error": "unknown"}

        for attempt in range(retries + 1):
            try:
                resp = await self.client.post(url, json=payload)
            except httpx.TransportError as exc:
                last = {"ok": False, "error": f"transport: {exc!r}"}
                logger.warning("WA send transport error (attempt %d): %r", attempt + 1, exc)
            else:
                if resp.status_code < 400:
                    return {"ok": True, "status": resp.status_code, "data": resp.json()}
                last = {"ok": False, "status": resp.status_code, "error": resp.text[:300]}
                if resp.status_code < 500 and resp.status_code != 429:
                    logger.error("WA send rejected %s: %s", resp.status_code, resp.text[:300])
                    return last
                logger.warning("WA send retryable %s (attempt %d)", resp.status_code, attempt + 1)
            if attempt < retries:
                await asyncio.sleep(0.5 * 2**attempt)
        return last

    async def process_payload(self, payload: WebhookPayload) -> None:
        for entry in payload.entry:
            for change in entry.changes:
                if change.field != "messages":
                    continue
                for status in change.value.statuses:
                    logger.info("WA status %s -> %s", status.id, status.status)
                for message in change.value.messages:
                    try:
                        await self._process_message(message)
                    except Exception:
                        logger.exception("Failed processing message %s", message.id)

    def _is_duplicate(self, message_id: str) -> bool:
        if message_id in self._seen_ids:
            return True
        self._seen_ids[message_id] = None
        if len(self._seen_ids) > _MAX_SEEN_IDS:
            self._seen_ids.pop(next(iter(self._seen_ids)))
        return False

    async def _process_message(self, message: Message) -> None:
        if self._is_duplicate(message.id):
            logger.info("Duplicate message %s ignored", message.id)
            return

        role = self.resolve_role(message.from_)
        text = message.body_text
        handler = self._handle_owner if role is Role.OWNER else self._handle_customer
        reply_result = await handler(message, text)

        self.events.append(
            {
                "message_id": message.id,
                "from": normalize_phone(message.from_),
                "role": role.value,
                "type": message.type,
                "text": text[:80],
                "reply_ok": bool(reply_result.get("ok")),
                "handled_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _handle_owner(self, message: Message, text: str) -> dict[str, Any]:
        if message.type not in {"text", "interactive"}:
            return await self.send_text_message(message.from_, "Saat ini hanya pesan teks yang didukung.")
        return await self.send_text_message(message.from_, f"[Owner] Pesan diterima: {text[:200]}")

    async def _handle_customer(self, message: Message, text: str) -> dict[str, Any]:
        if message.type not in {"text", "interactive"}:
            return await self.send_text_message(message.from_, "Saat ini hanya pesan teks yang didukung.")
        return await self.send_text_message(
            message.from_, "Halo! Terima kasih telah menghubungi kami. Pesan Anda sudah kami terima."
        )


@lru_cache
def get_whatsapp_service() -> WhatsAppService:
    return WhatsAppService()