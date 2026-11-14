from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase

WIB = timezone(timedelta(hours=7))
PAGE, CAP = 1000, 20000  # PostgREST caps responses at 1000 rows: paginate


def _ts(d: date) -> str:
    return datetime(d.year, d.month, d.day, tzinfo=WIB).isoformat()


async def _all(build: Callable[[], Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for off in range(0, CAP, PAGE):
        r = await build().range(off, off + PAGE - 1).execute()
        out += r.data
        if len(r.data) < PAGE:
            break
    return out


async def paid_orders(frm: date, to: date) -> list[dict[str, Any]]:
    c = await get_supabase()
    return await _all(
        lambda: c.table("orders")
        .select(
            "id,chat_id,customer_name,total_price,paid_at,order_items(sku,product_name,quantity,subtotal)"
        )
        .eq("status", "paid")
        .gte("paid_at", _ts(frm))
        .lt("paid_at", _ts(to + timedelta(days=1)))
        .order("id")
    )


async def order_statuses(frm: date, to: date) -> list[dict[str, Any]]:
    c = await get_supabase()
    return await _all(
        lambda: c.table("orders")
        .select("id,status,total_price")
        .gte("created_at", _ts(frm))
        .lt("created_at", _ts(to + timedelta(days=1)))
        .order("id")
    )


async def finance_records(frm: date, to: date) -> list[dict[str, Any]]:
    c = await get_supabase()
    return await _all(
        lambda: c.table("financial_records")
        .select("type,domain,amount,category")
        .gte("transaction_date", frm.isoformat())
        .lte("transaction_date", to.isoformat())
        .order("id")
    )


async def active_products() -> list[dict[str, Any]]:
    c = await get_supabase()
    return await _all(
        lambda: c.table("products")
        .select("sku,name,price")
        .eq("is_active", True)
        .order("id")
    )
