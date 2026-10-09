import hashlib
import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.webhooks import WebhookPayload
from app.services.whatsapp_service import WhatsAppService, get_whatsapp_service

logger = logging.getLogger("conversafin.webhooks")
router = APIRouter(tags=["webhooks"])


def _valid_signature(secret: str, raw_body: bytes, header: str | None) -> bool:
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    settings: Settings = Depends(get_settings),
) -> PlainTextResponse:
    if (
        hub_mode == "subscribe"
        and hub_challenge is not None
        and hub_verify_token is not None
        and hmac.compare_digest(hub_verify_token, settings.wa_verify_token)
    ):
        return PlainTextResponse(content=hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook", status_code=200)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict[str, str]:
    raw_body = await request.body()

    if settings.wa_app_secret and not _valid_signature(
        settings.wa_app_secret, raw_body, request.headers.get("X-Hub-Signature-256")
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = WebhookPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        logger.warning("Unparseable webhook payload: %s", exc.errors()[:3])
        return {"status": "ignored"}

    background_tasks.add_task(service.process_payload, payload)
    return {"status": "accepted"}


@router.get("/webhook/debug/events")
async def debug_events(
    settings: Settings = Depends(get_settings),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict:
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")
    return {"dry_run": settings.wa_dry_run, "events": list(service.events)}