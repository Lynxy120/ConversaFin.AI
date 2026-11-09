import hashlib
import hmac
import logging
import time

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
    request: Request,
    settings: Settings = Depends(get_settings),
) -> PlainTextResponse:
    # 1. Ambil query parameter dari Meta
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # 2. Cek apakah ada mode dan token
    if mode and token:
        # 3. Validasi mode dan token
        if mode == "subscribe" and token == settings.wa_verify_token:
            print("WEBHOOK_VERIFIED")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            # Token tidak cocok
            raise HTTPException(status_code=403, detail="Verification token mismatch")

    # Parameter tidak lengkap
    raise HTTPException(status_code=400, detail="Missing parameters")


@router.post("/webhook", status_code=200)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict[str, str]:
    started = time.perf_counter()

    raw_body = await request.body()
    logger.info(
        "WA inbound %d bytes: %s",
        len(raw_body),
        raw_body[:600].decode("utf-8", "replace"),
    )
    after_body = time.perf_counter()

    if settings.wa_app_secret and not _valid_signature(
        settings.wa_app_secret,
        raw_body,
        request.headers.get("X-Hub-Signature-256"),
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = WebhookPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        logger.warning("Unparseable webhook payload: %s", exc.errors()[:3])
        logger.info(
            "Webhook timing: body=%.4fs total=%.4fs",
            after_body - started,
            time.perf_counter() - started,
        )
        return {"status": "ignored"}

    background_tasks.add_task(service.process_payload, payload)

    logger.info(
        "Webhook timing: body=%.4fs total=%.4fs",
        after_body - started,
        time.perf_counter() - started,
    )
    return {"status": "accepted"}


@router.get("/webhook/debug/events")
async def debug_events(
    settings: Settings = Depends(get_settings),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict:
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")
    return {"dry_run": settings.wa_dry_run, "events": list(service.events)}
