from typing import Any
from datetime import datetime, timezone

from postgrest.exceptions import APIError

from app.core.supabase import get_supabase


class EmptyCart(Exception): ...


async def checkout(chat_id: str, name: str | None, ref: str) -> dict[str, Any]:
    c = await get_supabase()
    try:
        r = await c.rpc(
            "checkout_cart", {"p_chat": chat_id, "p_name": name, "p_ref": ref}
        ).execute()
    except APIError as e:
        if "EMPTY_CART" in str(e):
            raise EmptyCart from e
        raise
    o = r.data[0] if isinstance(r.data, list) else r.data
    return await get_order(o["id"])  # type: ignore[return-value]


async def get_order(order_id: str) -> dict[str, Any] | None:
    r = (
        await (await get_supabase())
        .table("orders")
        .select("*, order_items(*)")
        .eq("id", order_id)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None


async def list_orders(
    limit: int = 20, status: str | None = None
) -> list[dict[str, Any]]:
    q = (
        (await get_supabase())
        .table("orders")
        .select("*, order_items(*)")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if status:
        q = q.eq("status", status)
    return (await q.execute()).data


async def get_by_mid(mid: str) -> dict[str, Any] | None:
    r = (
        await (await get_supabase())
        .table("orders")
        .select("*, order_items(*)")
        .eq("midtrans_order_id", mid)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None


async def set_payment(
    order_id: str, *, mid: str, tx_id: str | None, url: str, expires: datetime | None
) -> None:
    await (await get_supabase()).table("orders").update(
        {
            "midtrans_order_id": mid,
            "midtrans_transaction_id": tx_id,
            "payment_url": url,
            "payment_type": "qris",
            "payment_expires_at": expires.isoformat() if expires else None,
        }
    ).eq("id", order_id).execute()


async def mark_paid(mid: str, payment_type: str | None) -> dict[str, Any] | None:
    """Only the call that flips pending->paid receives a row (idempotent)."""
    d: dict[str, Any] = {
        "status": "paid",
        "paid_at": datetime.now(timezone.utc).isoformat(),
    }
    if payment_type:
        d["payment_type"] = payment_type
    r = (
        await (await get_supabase())
        .table("orders")
        .update(d)
        .eq("midtrans_order_id", mid)
        .eq("status", "pending")
        .execute()
    )
    return r.data[0] if r.data else None


async def set_status_if_pending(mid: str, status: str) -> bool:
    r = (
        await (await get_supabase())
        .table("orders")
        .update({"status": status})
        .eq("midtrans_order_id", mid)
        .eq("status", "pending")
        .execute()
    )
    return bool(r.data)


async def set_receipt(order_id: str, path: str) -> None:
    await (await get_supabase()).table("orders").update({"receipt_path": path}).eq(
        "id", order_id
    ).execute()


async def list_tasks(limit: int = 200) -> list[dict[str, Any]]:
    r = (
        await (await get_supabase())
        .table("orders")
        .select("*, order_items(*)")
        .or_(
            "status.eq.pending,and(status.eq.paid,fulfillment_status.in.(new,preparing,ready))"
        )
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return r.data


async def advance(
    order_id: str, *, expect: str, to: str, note: str | None
) -> dict[str, Any] | None:
    """Compare-and-set on fulfillment_status; returns None if the order changed meanwhile."""
    d: dict[str, Any] = {"fulfillment_status": to}
    if note is not None:
        d["fulfillment_note"] = note
    if to in ("completed", "cancelled"):
        d["fulfilled_at"] = datetime.now(timezone.utc).isoformat()
    r = (
        await (await get_supabase())
        .table("orders")
        .update(d)
        .eq("id", order_id)
        .eq("status", "paid")
        .eq("fulfillment_status", expect)
        .execute()
    )
    return r.data[0] if r.data else None


async def cancel_unpaid(order_id: str, note: str | None) -> dict[str, Any] | None:
    r = (
        await (await get_supabase())
        .table("orders")
        .update(
            {
                "status": "cancelled",
                "fulfillment_status": "cancelled",
                "fulfillment_note": note,
            }
        )
        .eq("id", order_id)
        .eq("status", "pending")
        .execute()
    )
    return r.data[0] if r.data else None
