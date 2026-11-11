import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from functools import lru_cache
from typing import Any

from app.core.config import Settings, get_settings
from app.integrations.telegram import TelegramClient, get_telegram_client
from app.schemas.telegram import CallbackQuery, Message, Update

log = logging.getLogger("conversafin.bot")

HELP_CUSTOMER = (
    "Halo! 👋\n/katalog - lihat produk\n/keranjang - lihat keranjang\n/help - bantuan"
)
HELP_OWNER = (
    HELP_CUSTOMER
    + "\n\nOwner: kirim teks / voice note / foto struk untuk mencatat transaksi.\n/orders - pesanan terakhir"
)


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
        self._s = s or get_settings()
        self.tg = tg or get_telegram_client()
        self._seen: dict[int, None] = {}
        self.events: deque[dict[str, Any]] = deque(maxlen=200)
        log.info(
            "BotService ready: owners=%d dry_run=%s",
            len(self._s.owner_ids),
            self._s.telegram_dry_run,
        )

    def role_of(self, user_id: int) -> Role:
        return Role.OWNER if user_id in self._s.owner_ids else Role.CUSTOMER

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

    async def _on_command(self, c: Ctx, cmd: str) -> dict[str, Any]:  # replaced in W3
        if cmd in ("/start", "/help"):
            return await self._reply(
                c, HELP_OWNER if c.role is Role.OWNER else HELP_CUSTOMER, action="help"
            )
        if cmd == "/whoami":
            return await self._reply(
                c, f"chat_id={c.chat_id}\nrole={c.role.value}", action="whoami"
            )
        return await self._reply(
            c, "Perintah tidak dikenal. Ketik /help.", action="unknown_cmd"
        )

    async def _on_message(self, c: Ctx) -> dict[str, Any]:  # replaced in W3, W5
        return await self._reply(
            c,
            f"[{c.role.value}] pesan diterima. Ketik /help.",
            action=f"{c.role.value}_echo",
        )

    async def _on_callback(self, c: Ctx) -> dict[str, Any]:  # replaced in W3
        await self.tg.answer_callback(c.callback.id)  # type: ignore[union-attr]
        return {"action": "callback_noop", "ok": True}


@lru_cache
def get_bot_service() -> BotService:
    return BotService()
