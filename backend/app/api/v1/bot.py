from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_admin
from app.integrations.telegram import TelegramClient, get_telegram_client

router = APIRouter(prefix="/bot", tags=["bot"], dependencies=[Depends(require_admin)])


@router.get("/status")
async def status(tg: TelegramClient = Depends(get_telegram_client)):
    me, wh = await tg.get_me(), await tg.get_webhook_info()
    if not me["ok"]:
        raise HTTPException(502, str(me.get("error")))
    w = wh.get("result", {})
    return {
        "bot": {
            "id": me["result"]["id"],
            "username": me["result"]["username"],
            "name": me["result"]["first_name"],
        },
        "webhook": {
            "url": w.get("url") or None,
            "pending": w.get("pending_update_count", 0),
            "last_error": w.get("last_error_message"),
            "last_error_at": w.get("last_error_date"),
        },
    }
