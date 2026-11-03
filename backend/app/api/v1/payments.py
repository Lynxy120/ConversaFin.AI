import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import ValidationError

from app.core.security import require_admin
from app.repositories import orders as orders_repo
from app.schemas.payments import MidtransNotification
from app.services import receipt_service as rs
from app.services.midtrans_service import MidtransService, get_midtrans_service
from app.services.payment_service import PaymentError, PaymentService, get_payment_service

log = logging.getLogger("conversafin.payments")
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/midtrans/notification")
async def notification(req: Request, bg: BackgroundTasks, mt: MidtransService = Depends(get_midtrans_service),
                       pay: PaymentService = Depends(get_payment_service)):
    raw = await req.body()
    log.info("midtrans notif: %s", raw[:400].decode("utf-8", "replace"))
    try:
        n = MidtransNotification.model_validate_json(raw)
    except ValidationError:
        raise HTTPException(400, "invalid payload")
    if not mt.verify_signature(n.order_id, n.status_code, n.gross_amount, n.signature_key):
        raise HTTPException(403, "invalid signature")
    try:
        return {"status": "ok", **await pay.handle_notification(n, bg)}
    except PaymentError as e:  # non-2xx => Midtrans retries
        raise HTTPException(502, str(e)) from e


@router.post("/orders/{oid}/charge", dependencies=[Depends(require_admin)])
async def charge(oid: UUID, pay: PaymentService = Depends(get_payment_service)):
    o = await orders_repo.get_order(str(oid))
    if not o:
        raise HTTPException(404, "not found")
    try:
        return await pay.create_qris(o)
    except PaymentError as e:
        raise HTTPException(502, str(e)) from e


@router.post("/orders/{oid}/receipt", dependencies=[Depends(require_admin)])
async def receipt(oid: UUID):
    o = await orders_repo.get_order(str(oid))
    if not o:
        raise HTTPException(404, "not found")
    if o["status"] != "paid":
        raise HTTPException(409, f"order is {o['status']}")
    path = await rs.store_receipt(o["id"], rs.build_receipt_pdf(o))
    await orders_repo.set_receipt(o["id"], path)
    return {"path": path, "url": await rs.signed_url(path)}