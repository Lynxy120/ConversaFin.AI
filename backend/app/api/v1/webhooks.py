import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.webhooks import WebhookPayload
from app.services.whatsapp_service import WhatsAppService, get_whatsapp_service

log = logging.getLogger("conversafin.webhooks")
router = APIRouter(tags=["webhooks"])
MAX_LOG_BYTES = (
    4000  # raw bodies contain phone numbers (PII): lower or remove once stable
)


def _signature_ok(secret: str, raw: bytes, header: str | None) -> bool:
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
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
        and hmac.compare_digest(
            hub_verify_token.encode(), settings.wa_verify_token.encode()
        )
    ):
        return PlainTextResponse(hub_challenge, status_code=200)
    log.warning("webhook verification rejected (mode=%s)", hub_mode)
    raise HTTPException(403, "Verification failed")


@router.post("/webhook", status_code=200)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict[str, str]:
    # 1) Log raw body BEFORE any signature check or parsing.
    raw = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")
    log.info(
        "WA inbound POST bytes=%d sig_header=%s body=%s",
        len(raw),
        bool(sig),
        raw[:MAX_LOG_BYTES].decode("utf-8", "replace"),
    )

    # 2) Signature: enforced only when a secret is configured AND not in development.
    secret = settings.wa_app_secret
    if not secret:
        log.warning("WA_APP_SECRET not set: signature verification skipped")
    elif not _signature_ok(secret, raw, sig):
        if settings.app_env == "development":
            log.warning("invalid/missing X-Hub-Signature-256 (dev mode: continuing)")
        else:
            log.error(
                "invalid X-Hub-Signature-256 -> 403 (check WA_APP_SECRET = App settings > Basic > App secret)"
            )
            raise HTTPException(403, "Invalid signature")

    # 3) Parse. Never return non-2xx for bad shapes (Meta would retry); log loudly instead.
    try:
        payload = WebhookPayload.model_validate(json.loads(raw))
    except (json.JSONDecodeError, UnicodeDecodeError):
        log.error("WA payload is not valid JSON")
        return {"status": "ignored"}
    except ValidationError as e:
        log.error(
            "WA payload failed validation: %s",
            json.dumps(e.errors(include_url=False, include_context=False), default=str)[
                :1500
            ],
        )
        return {"status": "ignored"}

    n_msg = sum(len(c.value.messages) for en in payload.entry for c in en.changes)
    n_sts = sum(len(c.value.statuses) for en in payload.entry for c in en.changes)
    log.info("WA payload parsed: messages=%d statuses=%d -> queued", n_msg, n_sts)

    # 4) Queue and return 200 immediately.
    background_tasks.add_task(service.process_payload, payload)
    return {"status": "accepted"}


@router.get("/webhook/debug/events")
async def debug_events(
    settings: Settings = Depends(get_settings),
    service: WhatsAppService = Depends(get_whatsapp_service),
) -> dict:
    if settings.app_env != "development":
        raise HTTPException(404, "Not found")
    return {"dry_run": settings.wa_dry_run, "events": list(service.events)}
