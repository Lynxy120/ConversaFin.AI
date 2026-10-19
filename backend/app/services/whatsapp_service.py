import asyncio
import json
import logging
import re
from collections import deque
from datetime import datetime, timezone
from enum import StrEnum
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.repositories import orders as orders_repo
from app.repositories import products as products_repo
from app.schemas.webhooks import Message, WebhookPayload
from app.services.catalog_service import CatalogError, get_catalog_service

logger = logging.getLogger("conversafin.whatsapp")

_MAX_SEEN_IDS = 5000
MAX_LIST_ITEMS = 30
CATALOG_KEYWORDS = {
    "katalog", "catalog", "menu", "produk", "products", "halo", "hai", "hi", "hello", "start", "/katalog",
}


class Role(StrEnum):
    OWNER = "owner"
    CUSTOMER = "customer"


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    return digits


def rupiah(value: Any) -> str:
    return "Rp" + f"{int(float(value)):,}".replace(",", ".")


class WhatsAppService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        self._seen_ids: dict[str, None] = {}
        self.events: deque[dict[str, Any]] = deque(maxlen=200)
        self._owner_numbers: set[str] = {
            normalize_phone(n) for n in self._settings.wa_owner_number.split(",") if n.strip()
        }

    # ---------- HTTP ----------
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

    async def _send(self, payload: dict[str, Any], *, retries: int = 2) -> dict[str, Any]:
        if self._settings.wa_dry_run:
            logger.info("[dry-run] -> %s", json.dumps(payload, ensure_ascii=False)[:500])
            return {"ok": True, "dry_run": True}

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

    async def send_text_message(self, to: str, body: str, *, retries: int = 2) -> dict[str, Any]:
        return await self._send(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": normalize_phone(to),
                "type": "text",
                "text": {"preview_url": False, "body": body},
            },
            retries=retries,
        )

    async def send_product_list(
        self,
        to: str,
        retailer_ids: list[str],
        *,
        header: str = "Katalog Produk",
        body: str = "Pilih produk, tambahkan ke keranjang, lalu kirim pesanan Anda.",
        footer: str | None = "ConversaFin.AI",
        section_title: str = "Produk",
    ) -> dict[str, Any]:
        interactive: dict[str, Any] = {
            "type": "product_list",
            "header": {"type": "text", "text": header[:60]},
            "body": {"text": body[:1024]},
            "action": {
                "catalog_id": self._settings.wa_catalog_id,
                "sections": [
                    {
                        "title": section_title[:24],
                        "product_items": [{"product_retailer_id": r} for r in retailer_ids[:MAX_LIST_ITEMS]],
                    }
                ],
            },
        }
        if footer:
            interactive["footer"] = {"text": footer[:60]}
        return await self._send(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": normalize_phone(to),
                "type": "interactive",
                "interactive": interactive,
            }
        )

    async def send_catalog(self, to: str) -> dict[str, Any]:
        products = await products_repo.list_products(active_only=True, limit=MAX_LIST_ITEMS)
        if not products:
            res = await self.send_text_message(to, "Katalog masih kosong. Silakan hubungi kami kembali nanti.")
            return {"action": "catalog_empty", **res}
        res = await self.send_product_list(to, [p["retailer_id"] for p in products])
        return {"action": "catalog_sent", "count": len(products), **res}

    # ---------- inbound ----------
    async def process_payload(self, payload: WebhookPayload) -> None:
        for entry in payload.entry:
            for change in entry.changes:
                if change.field != "messages":
                    continue
                names = {
                    c.wa_id: c.profile.name for c in change.value.contacts if c.profile and c.profile.name
                }
                for status in change.value.statuses:
                    logger.info("WA status %s -> %s", status.id, status.status)
                for message in change.value.messages:
                    try:
                        await self._process_message(message, names.get(message.from_))
                    except Exception:
                        logger.exception("Failed processing message %s", message.id)

    def _is_duplicate(self, message_id: str) -> bool:
        if message_id in self._seen_ids:
            return True
        self._seen_ids[message_id] = None
        if len(self._seen_ids) > _MAX_SEEN_IDS:
            self._seen_ids.pop(next(iter(self._seen_ids)))
        return False

    async def _process_message(self, message: Message, customer_name: str | None) -> None:
        if self._is_duplicate(message.id):
            logger.info("Duplicate message %s ignored", message.id)
            return

        role = self.resolve_role(message.from_)
        text = message.body_text
        try:
            result = await self._dispatch(message, role, text, customer_name)
        except Exception:
            logger.exception("Handler error for message %s", message.id)
            result = {"action": "error", "ok": False}

        self.events.append(
            {
                "message_id": message.id,
                "from": normalize_phone(message.from_),
                "role": role.value,
                "type": message.type,
                "text": text[:80],
                "action": result.get("action"),
                "order_id": result.get("order_id"),
                "reply_ok": bool(result.get("ok")),
                "handled_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _dispatch(self, message: Message, role: Role, text: str, customer_name: str | None) -> dict[str, Any]:
        if message.type == "order" and message.order:
            return await self._handle_order(message, customer_name)

        if message.type not in {"text", "interactive"}:
            res = await self.send_text_message(message.from_, "Saat ini hanya pesan teks dan keranjang yang didukung.")
            return {"action": "unsupported", **res}

        command = re.sub(r"[^\w/\s]", "", text).strip().lower()

        if role is Role.OWNER and command.startswith("/"):
            return await self._handle_owner_command(message, command)

        if command in CATALOG_KEYWORDS:
            return await self.send_catalog(message.from_)

        if role is Role.OWNER:
            res = await self.send_text_message(message.from_, f"[Owner] Pesan diterima: {text[:200]}")
        else:
            res = await self.send_text_message(
                message.from_,
                "Halo! Terima kasih telah menghubungi kami. Ketik *katalog* untuk melihat produk.",
            )
        return {"action": f"{role.value}_reply", **res}

    async def _handle_order(self, message: Message, customer_name: str | None) -> dict[str, Any]:
        order_in = message.order
        assert order_in is not None
        items = [
            {"retailer_id": i.product_retailer_id, "quantity": i.quantity} for i in order_in.product_items
        ]
        try:
            order = await orders_repo.create_order(
                phone=normalize_phone(message.from_),
                name=customer_name,
                wa_message_id=message.id,
                catalog_id=order_in.catalog_id,
                note=order_in.text,
                items=items,
            )
        except orders_repo.OrderRejected as exc:
            logger.warning("Order rejected for %s: %s", message.id, exc)
            res = await self.send_text_message(
                message.from_,
                "Maaf, sebagian produk di keranjang tidak tersedia. Ketik *katalog* untuk melihat produk terbaru.",
            )
            return {"action": "order_rejected", **res}

        lines = [
            f"• {i['product_name']} x{i['quantity']} = {rupiah(i['subtotal'])}" for i in order["order_items"]
        ]
        summary = (
            f"Pesanan #{order['id'][:8].upper()} diterima ✅\n"
            + "\n".join(lines)
            + f"\nTotal: {rupiah(order['total_price'])}\nLink pembayaran akan dikirim segera."
        )
        res = await self.send_text_message(message.from_, summary)
        return {"action": "order_created", "order_id": order["id"], **res}

    async def _handle_owner_command(self, message: Message, command: str) -> dict[str, Any]:
        if command == "/sync":
            try:
                r = await get_catalog_service().sync_all()
                text = f"Sync dikirim: {r['synced']} produk, {len(r['skipped_no_image'])} dilewati (tanpa gambar)."
            except CatalogError as exc:
                text = f"Sync gagal: {exc}"
            res = await self.send_text_message(message.from_, text)
            return {"action": "owner_sync", **res}

        if command == "/orders":
            rows = await orders_repo.list_orders(limit=5)
            text = "5 pesanan terakhir:\n" + (
                "\n".join(
                    f"#{o['id'][:8].upper()} | {o.get('customer_phone')} | {rupiah(o['total_price'])} | {o['status']}"
                    for o in rows
                )
                or "(belum ada pesanan)"
            )
            res = await self.send_text_message(message.from_, text)
            return {"action": "owner_orders", **res}

        res = await self.send_text_message(message.from_, "Perintah owner: /sync, /orders, katalog")
        return {"action": "owner_help", **res}


@lru_cache
def get_whatsapp_service() -> WhatsAppService:
    return WhatsAppService()