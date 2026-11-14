import logging
from typing import Any

from app.integrations.telegram import get_telegram_client

log = logging.getLogger("conversafin.notify")
MSG = {
    "preparing": "👩‍🍳 Pesanan #{no} sedang disiapkan.",
    "ready": "✅ Pesanan #{no} sudah siap! Silakan diambil.",
    "completed": "🙏 Pesanan #{no} selesai. Terima kasih sudah berbelanja!",
    "cancelled": "Pesanan #{no} dibatalkan. Hubungi kami jika ada pertanyaan.",
}


async def notify_customer(order: dict[str, Any], status: str) -> None:
    try:
        await get_telegram_client().send_message(
            int(order["chat_id"]), MSG[status].format(no=order["id"][:8].upper())
        )
    except Exception:
        log.exception("customer notification failed for %s", order["id"])
