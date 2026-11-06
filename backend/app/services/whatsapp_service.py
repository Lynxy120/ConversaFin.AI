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
from postgrest.exceptions import APIError

from app.core.config import Settings, get_settings
from app.repositories import carts as carts_repo
from app.repositories import orders as orders_repo
from app.repositories import products as products_repo
from app.schemas.webhooks import Message, WebhookPayload
from app.services.finance_service import Outcome, get_finance_service

log = logging.getLogger("conversafin.wa")
MAX_ROWS = 10  # WhatsApp list message hard limit
KEYWORDS = {"katalog", "catalog", "menu", "produk", "halo", "hai", "hi", "hello", "start"}


class Role(StrEnum):
    OWNER = "owner"
    CUSTOMER = "customer"


def normalize_phone(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    return "62" + d[1:] if d.startswith("0") else d


def rupiah(v: Any) -> str:
    return "Rp" + f"{int(float(v)):,}".replace(",", ".")


class WhatsAppService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        self._seen: dict[str, None] = {}
        self.events: deque[dict[str, Any]] = deque(maxlen=200)
        self._owners = {normalize_phone(n) for n in self._s.wa_owner_number.split(",") if n.strip()}

    @property
    def owner_numbers(self) -> set[str]:
        return self._owners

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"https://graph.facebook.com/{self._s.wa_graph_version}",
                timeout=httpx.Timeout(10.0, connect=5.0),
                headers={"Authorization": f"Bearer {self._s.wa_access_token}"},
            )
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def resolve_role(self, phone: str) -> Role:
        return Role.OWNER if normalize_phone(phone) in self._owners else Role.CUSTOMER

    # ---------- outbound ----------
    @staticmethod
    def _wrap(to: str, typ: str, content: dict[str, Any]) -> dict[str, Any]:
        return {"messaging_product": "whatsapp", "recipient_type": "individual", "to": normalize_phone(to), "type": typ, typ: content}

    async def _send(self, payload: dict[str, Any], retries: int = 2) -> dict[str, Any]:
        if self._s.wa_dry_run:
            log.info("[dry-run] %s", json.dumps(payload, ensure_ascii=False)[:400])
            return {"ok": True, "dry_run": True}
        last: dict[str, Any] = {"ok": False}
        for i in range(retries + 1):
            try:
                r = await self.client.post(f"/{self._s.wa_phone_number_id}/messages", json=payload)
            except httpx.TransportError as e:
                last = {"ok": False, "error": repr(e)}
            else:
                if r.status_code < 400:
                    return {"ok": True, "data": r.json()}
                last = {"ok": False, "status": r.status_code, "error": r.text[:300]}
                log.error("WA send rejected %s: %s", r.status_code, r.text[:300])
                if r.status_code < 500 and r.status_code != 429:
                    return last
            if i < retries:
                await asyncio.sleep(0.5 * 2**i)
        return last

    async def send_text_message(self, to: str, body: str) -> dict[str, Any]:
        return await self._send(self._wrap(to, "text", {"preview_url": False, "body": body}))

    async def send_buttons(self, to: str, body: str, buttons: list[tuple[str, str]]) -> dict[str, Any]:
        return await self._send(self._wrap(to, "interactive", {
            "type": "button", "body": {"text": body[:1024]},
            "action": {"buttons": [{"type": "reply", "reply": {"id": i, "title": t[:20]}} for i, t in buttons[:3]]},
        }))

    async def send_image(self, to: str, link: str, caption: str | None = None) -> dict[str, Any]:
        return await self._send(self._wrap(to, "image", {"link": link, **({"caption": caption[:1024]} if caption else {})}))

    async def send_document(self, to: str, link: str, filename: str, caption: str | None = None) -> dict[str, Any]:
        return await self._send(self._wrap(to, "document", {"link": link, "filename": filename, **({"caption": caption[:1024]} if caption else {})}))

    async def send_catalog(self, to: str) -> dict[str, Any]:
        prods = await products_repo.list_products(limit=MAX_ROWS)
        if not prods:
            return {"action": "catalog_empty", **await self.send_text_message(to, "Katalog masih kosong.")}
        rows = [{
            "id": f"p:{p['sku']}"[:200], "title": p["name"][:24],
            "description": f"{rupiah(p['price'])} {p.get('description') or ''}".strip()[:72],
        } for p in prods]
        res = await self._send(self._wrap(to, "interactive", {
            "type": "list",
            "header": {"type": "text", "text": "Katalog Produk"},
            "body": {"text": "Pilih produk untuk ditambahkan ke keranjang."},
            "footer": {"text": self._s.brand[:60]},
            "action": {"button": "Lihat Produk", "sections": [{"title": "Produk", "rows": rows}]},
        }))
        return {"action": "catalog_sent", "count": len(rows), **res}

    # ---------- inbound ----------
    async def process_payload(self, payload: WebhookPayload) -> None:
        for entry in payload.entry:
            for ch in entry.changes:
                if ch.field != "messages":
                    continue
                names = {c.wa_id: c.profile.name for c in ch.value.contacts if c.profile and c.profile.name}
                for st in ch.value.statuses:
                    log.info("WA status %s -> %s", st.id, st.status)
                for m in ch.value.messages:
                    await self._process(m, names.get(m.from_))

    async def _process(self, m: Message, name: str | None) -> None:
        if m.id in self._seen:
            return
        self._seen[m.id] = None
        if len(self._seen) > 5000:
            self._seen.pop(next(iter(self._seen)))
        role = self.resolve_role(m.from_)
        try:
            res = await self._dispatch(m, role, name)
        except Exception:
            log.exception("handler error %s", m.id)
            res = {"action": "error"}
        self.events.append({
            "message_id": m.id, "from": normalize_phone(m.from_), "role": role.value, "type": m.type,
            "text": m.body_text[:80], "action": res.get("action"), "order_id": res.get("order_id"),
            "reply_ok": bool(res.get("ok")), "handled_at": datetime.now(timezone.utc).isoformat(),
        })

    async def _dispatch(self, m: Message, role: Role, name: str | None) -> dict[str, Any]:
        to, rid, owner = m.from_, m.reply_id, role is Role.OWNER
        if rid and rid.startswith("p:"):
            return await self._add_to_cart(to, rid[2:])
        if rid == "cart:catalog":
            return await self.send_catalog(to)
        if rid == "cart:checkout":
            return await self._checkout(m, name)
        if rid == "cart:clear":
            await carts_repo.clear(normalize_phone(to))
            return {"action": "cart_cleared", **await self.send_text_message(to, "Keranjang dikosongkan.")}

        fs = get_finance_service()
        if owner and rid and rid.startswith("fin:"):
            return await self._reply(to, await fs.handle_action(rid))

        cmd = re.sub(r"[^\w/\s]", "", m.body_text).strip().lower() if m.type in {"text", "interactive"} else ""
        if owner and cmd == "/orders":
            rows = await orders_repo.list_orders(limit=5)
            txt = "5 pesanan terakhir:\n" + ("\n".join(f"#{o['id'][:8].upper()} {rupiah(o['total_price'])} {o['status']}" for o in rows) or "-")
            return {"action": "owner_orders", **await self.send_text_message(to, txt)}
        if cmd in KEYWORDS:
            return await self.send_catalog(to)
        if cmd in {"keranjang", "cart"}:
            return await self._show_cart(to, "cart_view")

        # Owner free-form text / voice note / receipt photo -> AI financial engine
        if owner and m.type in {"text", "audio", "image"}:
            return await self._reply(to, await fs.handle_message(m))

        if m.type not in {"text", "interactive"}:
            return {"action": "unsupported", **await self.send_text_message(to, "Hanya pesan teks yang didukung.")}
        return {"action": f"{role.value}_reply", **await self.send_text_message(to, "Ketik *katalog* untuk produk atau *keranjang* untuk keranjang.")}
    
    async def _add_to_cart(self, to: str, sku: str) -> dict[str, Any]:
        try:
            await carts_repo.add(normalize_phone(to), sku)
        except APIError as e:
            if "UNKNOWN_PRODUCT" in str(e):
                return {"action": "cart_rejected", **await self.send_text_message(to, "Produk tidak tersedia. Ketik *katalog*.")}
            raise
        return await self._show_cart(to, "cart_added")

    async def _show_cart(self, to: str, action: str) -> dict[str, Any]:
        items = await carts_repo.items(normalize_phone(to))
        if not items:
            return {"action": "cart_empty", **await self.send_text_message(to, "Keranjang kosong. Ketik *katalog*.")}
        total = sum(float(i["products"]["price"]) * i["quantity"] for i in items)
        lines = [f"• {i['products']['name']} x{i['quantity']} = {rupiah(float(i['products']['price']) * i['quantity'])}" for i in items]
        res = await self.send_buttons(to, "🛒 Keranjang:\n" + "\n".join(lines) + f"\nTotal: {rupiah(total)}",
                                      [("cart:catalog", "Tambah Produk"), ("cart:checkout", "Checkout"), ("cart:clear", "Kosongkan")])
        return {"action": action, **res}

    async def _checkout(self, m: Message, name: str | None) -> dict[str, Any]:
        from app.services.payment_service import PaymentError, get_payment_service  # circular-import guard

        to = m.from_
        try:
            order = await orders_repo.checkout(normalize_phone(to), name, m.id)
        except orders_repo.EmptyCart:
            return {"action": "checkout_empty", **await self.send_text_message(to, "Keranjang kosong. Ketik *katalog*.")}
        lines = [f"• {i['product_name']} x{i['quantity']} = {rupiah(i['subtotal'])}" for i in order["order_items"]]
        res = await self.send_text_message(to, f"Pesanan #{order['id'][:8].upper()} ✅\n" + "\n".join(lines) + f"\nTotal: {rupiah(order['total_price'])}\nQRIS dikirim berikutnya.")
        try:
            pay = await get_payment_service().create_qris(order)
            cap = f"Scan QRIS untuk membayar {rupiah(order['total_price'])}. Berlaku hingga {pay['expires_label']}."
            r = await self.send_image(to, pay["qr_url"], cap)
            if not r.get("ok"):
                await self.send_text_message(to, f"{cap}\n{pay['qr_url']}")
        except PaymentError as e:
            log.error("QRIS failed %s: %s", order["id"], e)
            await self.send_text_message(to, "QRIS belum dapat dibuat. Tim kami akan menghubungi Anda.")
        return {"action": "order_created", "order_id": order["id"], **res}

    async def _reply(self, to: str, out: Outcome) -> dict[str, Any]:
        res = await (self.send_buttons(to, out.text[:1024], out.buttons) if out.buttons
                     else self.send_text_message(to, out.text))
        return {"action": out.action, **res}


@lru_cache
def get_whatsapp_service() -> WhatsAppService:
    return WhatsAppService()