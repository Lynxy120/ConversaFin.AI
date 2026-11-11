import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from functools import lru_cache
from typing import Any

from app.core.config import Settings, get_settings
from app.integrations.telegram import TelegramClient, get_telegram_client, kb
from app.schemas.telegram import CallbackQuery, Message, Update
from app.core.format import rupiah
from app.repositories import orders as orders_repo
from app.services.payment_service import get_payment_service
from app.services.finance_service import Outcome, get_finance_service
from app.services.shop_service import (
    EmptyCart,
    UnknownProduct,
    get_shop_service,
    order_text,
)

log = logging.getLogger("conversafin.bot")

HELP_CUSTOMER = (
    "Halo! 👋\n/katalog - lihat produk\n/keranjang - lihat keranjang\n/help - bantuan"
)
HELP_OWNER = (
    HELP_CUSTOMER
    + "\n\nOwner: kirim teks / voice note / foto struk untuk mencatat transaksi.\n/orders - pesanan terakhir"
)

CATALOG_WORDS = {
    "katalog",
    "catalog",
    "menu",
    "produk",
    "products",
    "halo",
    "hai",
    "hi",
    "hello",
}


class Role(StrEnum):
    OWNER = "owner"
    CUSTOMER = "customer"


@dataclass(slots=True)
class Ctx:
    chat_id: int
    user_id: int
    name: str
    role: Role
    update_id: int
    message: Message | None = None
    callback: CallbackQuery | None = None


class BotService:
    def __init__(
        self, s: Settings | None = None, tg: TelegramClient | None = None
    ) -> None:
        self.shop = get_shop_service()
        self.payments = get_payment_service()
        self._s = s or get_settings()
        self.tg = tg or get_telegram_client()
        self.finance = get_finance_service()
        self._seen: dict[int, None] = {}
        self.events: deque[dict[str, Any]] = deque(maxlen=200)
        log.info(
            "BotService ready: owners=%d dry_run=%s",
            len(self._s.owner_ids),
            self._s.telegram_dry_run,
        )

    def role_of(self, user_id: int) -> Role:
        raw_owners = self._s.owner_ids
        if isinstance(raw_owners, (list, tuple, set)):
            owner_strs = [str(x).strip() for x in raw_owners]
        else:
            owner_strs = [x.strip() for x in str(raw_owners).split(",") if x.strip()]
        return Role.OWNER if str(user_id) in owner_strs else Role.CUSTOMER

    def _ctx(self, u: Update) -> Ctx | None:
        msg = cb = None
        if u.callback_query and u.callback_query.message:
            cb = u.callback_query
            user, chat = cb.from_, cb.message.chat
        elif u.message:
            msg = u.message
            user, chat = msg.from_, msg.chat
        else:
            return None
        if chat.type != "private" or user is None or user.is_bot:
            return None
        name = (
            " ".join(filter(None, [user.first_name, user.last_name]))
            or user.username
            or str(user.id)
        )
        return Ctx(chat.id, user.id, name, self.role_of(user.id), u.update_id, msg, cb)

    async def handle_update(self, u: Update) -> None:
        if u.update_id in self._seen:
            log.info("duplicate update %s ignored", u.update_id)
            return
        self._seen[u.update_id] = None
        if len(self._seen) > 5000:
            self._seen.pop(next(iter(self._seen)))
        c = self._ctx(u)
        if not c:
            log.info("update %s ignored (non-private / unsupported)", u.update_id)
            return
        kind = (
            "callback"
            if c.callback
            else ("text" if c.message and c.message.text else "media")
        )
        log.info(
            "TG update=%s chat=%s role=%s kind=%s text=%r",
            u.update_id,
            c.chat_id,
            c.role.value,
            kind,
            (c.callback.data if c.callback else (c.message.body if c.message else ""))[
                :80
            ],
        )
        try:
            res = await self._dispatch(c)
        except Exception:
            log.exception("handler error update=%s", u.update_id)
            res = {"action": "error", "ok": False}
            await self.tg.send_message(
                c.chat_id, "⚠️ Terjadi kesalahan. Coba lagi sebentar lagi."
            )
        self.events.append(
            {
                "update_id": u.update_id,
                "chat_id": c.chat_id,
                "role": c.role.value,
                "kind": kind,
                "action": res.get("action"),
                "order_id": res.get("order_id"),
                "ok": bool(res.get("ok")),
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )

    # ---------- routing ----------
    async def _dispatch(self, c: Ctx) -> dict[str, Any]:
        if c.callback:
            return await self._on_callback(c)
        text = (c.message.body or "").strip() if c.message else ""
        if text.startswith("/"):
            return await self._on_command(c, text.split()[0].split("@")[0].lower())
        return await self._on_message(c)

    async def _reply(
        self, c: Ctx, text: str, markup: dict | None = None, action: str = "reply"
    ) -> dict[str, Any]:
        return {"action": action, **await self.tg.send_message(c.chat_id, text, markup)}

    async def _on_command(self, c: Ctx, cmd: str) -> dict[str, Any]:
        if cmd in ("/start", "/help"):
            return await self._reply(
                c, HELP_OWNER if c.role is Role.OWNER else HELP_CUSTOMER, action="help"
            )
        if cmd == "/whoami":
            return await self._reply(
                c, f"chat_id={c.chat_id}\nrole={c.role.value}", action="whoami"
            )
        if cmd in ("/katalog", "/catalog", "/menu"):
            text, markup = await self.shop.catalog(0)
            return await self._reply(c, text, markup, "catalog_shown")
        if cmd in ("/keranjang", "/cart"):
            text, markup = await self.shop.cart(c.chat_id)
            return await self._reply(c, text, markup, "cart_view")
        if cmd == "/orders" and c.role is Role.OWNER:
            rows = await orders_repo.list_orders(limit=5)
            txt = "5 pesanan terakhir:\n" + (
                "\n".join(
                    f"#{o['id'][:8].upper()} {rupiah(o['total_price'])} {o['status']}"
                    for o in rows
                )
                or "-"
            )
            return await self._reply(c, txt, action="owner_orders")
        return await self._reply(
            c, "Perintah tidak dikenal. Ketik /help.", action="unknown_cmd"
        )

    async def _on_message(self, c: Ctx) -> dict[str, Any]:
        m = c.message
        t = (m.body or "").strip().lower() if m else ""
        if t in CATALOG_WORDS:
            text, markup = await self.shop.catalog(0)
            return await self._reply(c, text, markup, "catalog_shown")
        if t in {"keranjang", "cart"}:
            text, markup = await self.shop.cart(c.chat_id)
            return await self._reply(c, text, markup, "cart_view")
        if (
            c.role is Role.OWNER
            and m
            and (m.body or m.voice or m.audio or m.photo or m.document)
        ):
            await self.tg.chat_action(c.chat_id)
            return await self._send_outcome(
                c, await self.finance.handle_message(m, c.chat_id)
            )  # owner → AI engine
        return await self._reply(
            c,
            "Ketik /katalog untuk melihat produk atau /keranjang.",
            action=f"{c.role.value}_reply",
        )

    async def _on_callback(self, c: Ctx) -> dict[str, Any]:
        cb = c.callback
        d, mid = cb.data or "", (cb.message.message_id if cb.message else None)  # type: ignore[union-attr]
        if d.startswith("p:"):
            try:
                qty = await self.shop.add(c.chat_id, d[2:])
                await self.tg.answer_callback(cb.id, f"✅ Ditambahkan (×{qty})")  # type: ignore[union-attr]
                return {"action": "cart_added", "ok": True}
            except UnknownProduct:
                await self.tg.answer_callback(cb.id, "Produk tidak tersedia", alert=True)  # type: ignore[union-attr]
                return {"action": "cart_rejected", "ok": True}
        if d.startswith("fin:"):
            await self.tg.answer_callback(cb.id)  # type: ignore[union-attr]
            if c.role is not Role.OWNER:
                return {"action": "forbidden", "ok": True}
            return await self._send_outcome(c, await self.finance.handle_action(d))
        if d.startswith("cat:"):
            text, markup = await self.shop.catalog(int(d[4:]) if d[4:].isdigit() else 0)
            return {"action": "catalog_shown", **await self._show(c, text, markup, mid)}
        if d == "c:view":
            text, markup = await self.shop.cart(c.chat_id)
            return {"action": "cart_view", **await self._show(c, text, markup, mid)}
        if d == "c:clr":
            await self.shop.clear(c.chat_id)
            text, markup = await self.shop.cart(c.chat_id)
            return {"action": "cart_cleared", **await self._show(c, text, markup, mid)}
        if d == "c:co":
            try:
                order = await self.shop.checkout(c.chat_id, c.name, f"tg:{c.update_id}")
            except EmptyCart:
                return {
                    "action": "checkout_empty",
                    **await self._show(c, "🛒 Keranjang kosong.", None, mid),
                }
            r = await self._show(c, order_text(order), None, mid)
            await self.payments.send_qris(c.chat_id, order)
            return {"action": "order_created", "order_id": order["id"], **r}
        return {"action": "callback_noop", "ok": True}

    async def _show(
        self, c: Ctx, text: str, markup: dict | None = None, mid: int | None = None
    ) -> dict[str, Any]:
        r = (
            await self.tg.edit_message(c.chat_id, mid, text, markup)
            if mid
            else {"ok": False}
        )
        return r if r["ok"] else await self.tg.send_message(c.chat_id, text, markup)

    async def _send_outcome(self, c: Ctx, out: Outcome) -> dict[str, Any]:
        markup = (
            kb([[(label, cid) for cid, label in out.buttons]]) if out.buttons else None
        )  # buttons are (callback_id, label)
        return await self._reply(c, out.text, markup, out.action)


@lru_cache
def get_bot_service() -> BotService:
    return BotService()
