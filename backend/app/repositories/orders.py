from typing import Any

from postgrest.exceptions import APIError

from app.core.supabase import get_supabase


class OrderRejected(Exception):
    """Cart contains unknown/inactive products or invalid quantities."""


async def create_order(
    *,
    phone: str,
    name: str | None,
    wa_message_id: str,
    catalog_id: str | None,
    note: str | None,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    client = await get_supabase()
    try:
        res = await client.rpc(
            "create_order",
            {
                "p_customer_phone": phone,
                "p_customer_name": name,
                "p_wa_message_id": wa_message_id,
                "p_catalog_id": catalog_id,
                "p_note": note,
                "p_items": items,
            },
        ).execute()
    except APIError as exc:
        msg = str(exc)
        if "UNKNOWN_PRODUCTS" in msg or "INVALID_ITEMS" in msg:
            raise OrderRejected(msg) from exc
        raise
    order = res.data[0] if isinstance(res.data, list) else res.data
    rows = await client.table("order_items").select("*").eq("order_id", order["id"]).execute()
    return {**order, "order_items": rows.data}


async def list_orders(*, limit: int = 20, status: str | None = None) -> list[dict[str, Any]]:
    client = await get_supabase()
    q = client.table("orders").select("*, order_items(*)").order("created_at", desc=True).limit(limit)
    if status:
        q = q.eq("status", status)
    return (await q.execute()).data


async def get_order(order_id: str) -> dict[str, Any] | None:
    client = await get_supabase()
    res = await client.table("orders").select("*, order_items(*)").eq("id", order_id).limit(1).execute()
    return res.data[0] if res.data else None