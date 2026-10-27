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
    print("\n" + "="*70)
    print("🔍 META WEBHOOK REQUEST DEBUG")
    print(f"Full URL: {request.url}")
    print(f"Query Params: {dict(request.query_params)}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Expected Token from Env (wa_verify_token): '{settings.wa_verify_token}'")
    print("="*70 + "\n")
    
    query_params = request.query_params
    hub_mode = query_params.get("hub.mode")
    hub_challenge = query_params.get("hub.challenge")
    
    # Coba ambil dari 'hub.token' ATAU 'hub.verify_token' (Meta kadang inkonsisten)
    hub_token = query_params.get("hub.token") or query_params.get("hub.verify_token")
    
    expected_token = str(settings.wa_verify_token) if settings.wa_verify_token else ""

    if hub_mode == "subscribe" and hub_challenge and hub_token:
        if hmac.compare_digest(hub_token, expected_token):
            print(f"✅ VERIFIKASI BERHASIL! Returning challenge: {hub_challenge}")
            return PlainTextResponse(content=hub_challenge, status_code=200)
        else:
            print(f"❌ TOKEN MISMATCH!")
            print(f"   Received : '{hub_token}'")
            print(f"   Expected : '{expected_token}'")
    else:
        print(f"❌ PARAMETER TIDAK LENGKAP!")
        print(f"   mode: '{hub_mode}'")
        print(f"   challenge: '{hub_challenge}'")
        print(f"   token: '{hub_token}'")
        
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook", status_code=200)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict[str, str]:
    started = time.perf_counter()

    raw_body = await request.body()
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