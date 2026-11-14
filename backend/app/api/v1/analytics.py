import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.core.security import require_admin
from app.repositories import analytics as repo
from app.services.insights_service import build_insights

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(require_admin)]
)
WIB = timezone(timedelta(hours=7))


@router.get("/insights")
async def insights(days: int = Query(30, ge=7, le=180)):
    to = datetime.now(WIB).date()
    frm = to - timedelta(days=days - 1)
    pfrm, pto = frm - timedelta(days=days), frm - timedelta(days=1)
    paid, prev, statuses, records, products = await asyncio.gather(
        repo.paid_orders(frm, to),
        repo.paid_orders(pfrm, pto),
        repo.order_statuses(frm, to),
        repo.finance_records(frm, to),
        repo.active_products(),
    )
    return build_insights(
        frm=frm,
        to=to,
        paid=paid,
        prev_paid=prev,
        statuses=statuses,
        records=records,
        products=products,
    )
