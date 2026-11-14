from collections import Counter
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import require_admin
from app.repositories import orders as repo
from app.services.midtrans_service import MidtransError, get_midtrans_service
from app.services.order_notify import notify_customer

router = APIRouter(
    prefix="/orders", tags=["orders"], dependencies=[Depends(require_admin)]
)
TRANSITIONS = {
    "new": {"preparing", "cancelled"},
    "preparing": {"ready", "cancelled"},
    "ready": {"completed", "cancelled"},
}


class FulfillmentIn(BaseModel):
    status: Literal["preparing", "ready", "completed", "cancelled"]
    note: str | None = Field(default=None, max_length=300)
    notify: bool = True


def _bucket(o: dict) -> str:
    return "unpaid" if o["status"] == "pending" else o["fulfillment_status"]


@router.get("")
async def list_orders(limit: int = Query(20, ge=1, le=100), status: str | None = None):
    return await repo.list_orders(limit, status)


@router.get("/tasks")  # must stay above /{oid}
async def tasks():
    items = await repo.list_tasks()
    c = Counter(_bucket(o) for o in items)
    return {
        "counts": {k: c.get(k, 0) for k in ("unpaid", "new", "preparing", "ready")},
        "items": items,
    }


@router.get("/{oid}")
async def get_order(oid: UUID):
    o = await repo.get_order(str(oid))
    if not o:
        raise HTTPException(404, "Order not found")
    return o


@router.patch("/{oid}/fulfillment")
async def update_fulfillment(oid: UUID, body: FulfillmentIn, bg: BackgroundTasks):
    o = await repo.get_order(str(oid))
    if not o:
        raise HTTPException(404, "Order not found")

    if o["status"] == "pending":
        if body.status != "cancelled":
            raise HTTPException(409, "Order is not paid yet")
        if o.get(
            "midtrans_order_id"
        ):  # void the QR so a late payment cannot land on a cancelled order
            try:
                await get_midtrans_service().cancel(o["midtrans_order_id"])
            except MidtransError as e:
                raise HTTPException(
                    409,
                    f"Could not cancel the QRIS payment (it may have just been paid): {e}",
                ) from e
        row = await repo.cancel_unpaid(o["id"], body.note)
    elif o["status"] == "paid":
        cur = o["fulfillment_status"]
        if body.status not in TRANSITIONS.get(cur, set()):
            raise HTTPException(
                409, f"Cannot move an order from {cur} to {body.status}"
            )
        row = await repo.advance(o["id"], expect=cur, to=body.status, note=body.note)
    else:
        raise HTTPException(409, f"Order is {o['status']}")

    if not row:
        raise HTTPException(409, "Order changed meanwhile, refresh and retry")
    if body.notify:
        bg.add_task(notify_customer, o, body.status)
    return row
