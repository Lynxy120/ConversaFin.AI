import re
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import require_admin
from app.core.supabase import get_supabase

router = APIRouter(
    prefix="/finance", tags=["finance"], dependencies=[Depends(require_admin)]
)
WIB = timezone(timedelta(hours=7))
Domain = Literal["business", "personal"]
COLS = "id,type,domain,amount,category,description,merchant,transaction_date,source,input_type,confidence,created_at"


def _span(frm: date | None, to: date | None) -> tuple[date, date]:
    to = to or datetime.now(WIB).date()
    frm = frm or to - timedelta(days=29)
    if frm > to or (to - frm).days > 366:
        raise HTTPException(422, "invalid date range (max 366 days)")
    return frm, to


@router.get("/summary")
async def summary(
    from_: date | None = Query(None, alias="from"),
    to: date | None = None,
    domain: Domain | None = None,
):
    frm, to = _span(from_, to)
    c = await get_supabase()
    args = {"p_from": frm.isoformat(), "p_to": to.isoformat(), "p_domain": domain}
    series = (await c.rpc("finance_timeseries", args).execute()).data
    cats = (await c.rpc("finance_by_category", args).execute()).data
    pend = (
        await c.table("orders")
        .select("id", count="exact")
        .eq("status", "pending")
        .limit(1)
        .execute()
    )
    income = sum(float(r["income"]) for r in series)
    expense = sum(float(r["expense"]) for r in series)
    return {
        "from": frm.isoformat(),
        "to": to.isoformat(),
        "income": income,
        "expense": expense,
        "profit": income - expense,
        "pending_orders": pend.count or 0,
        "series": series,
        "categories": cats,
    }


@router.get("/records")
async def records(
    from_: date | None = Query(None, alias="from"),
    to: date | None = None,
    domain: Domain | None = None,
    type: Literal["income", "expense"] | None = None,
    category: str | None = Query(None, max_length=40),
    q: str | None = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    frm, to = _span(from_, to)
    qy = (
        (await get_supabase())
        .table("financial_records")
        .select(COLS, count="exact")
        .gte("transaction_date", frm.isoformat())
        .lte("transaction_date", to.isoformat())
        .order("transaction_date", desc=True)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if domain:
        qy = qy.eq("domain", domain)
    if type:
        qy = qy.eq("type", type)
    if category:
        qy = qy.eq("category", category)
    if q:
        qy = qy.ilike("description", f"%{re.sub(r'[%,()*\\\\]', ' ', q).strip()}%")
    r = await qy.execute()
    return {"items": r.data, "total": r.count or 0}
