import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.telegram import Update
from app.services.bot_service import BotService, get_bot_service

log = logging.getLogger("conversafin.tgwebhook")
router = APIRouter(tags=["telegram"])


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    bg: BackgroundTasks,
    s: Settings = Depends(get_settings),
    bot: BotService = Depends(get_bot_service),
) -> dict[str, bool]:
    raw = await request.body()  # 1) log raw body first (PII: trim/remove when stable)
    log.info(
        "TG inbound bytes=%d body=%s", len(raw), raw[:3000].decode("utf-8", "replace")
    )
    secret = (
        s.telegram_webhook_secret
    )  # 2) auth: Telegram echoes the secret set in setWebhook
    got = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret:
        if not hmac.compare_digest(got.encode(), secret.encode()):
            log.error("invalid webhook secret -> 403")
            raise HTTPException(403, "Forbidden")
    elif s.app_env == "production":
        log.error("TELEGRAM_WEBHOOK_SECRET is empty in production")
        raise HTTPException(403, "Forbidden")
    try:  # 3) parse; non-2xx would make Telegram retry forever
        update = Update.model_validate_json(raw)
    except ValidationError as e:
        log.error(
            "update failed validation: %s", str(e.errors(include_url=False))[:800]
        )
        return {"ok": True}
    bg.add_task(bot.handle_update, update)  # 4) 200 immediately
    return {"ok": True}


@router.get("/telegram/debug/events")
async def debug_events(
    s: Settings = Depends(get_settings), bot: BotService = Depends(get_bot_service)
) -> dict:
    if s.app_env != "development":
        raise HTTPException(404, "Not found")
    return {
        "dry_run": s.telegram_dry_run,
        "owners": sorted(s.owner_ids),
        "events": list(bot.events),
    }
