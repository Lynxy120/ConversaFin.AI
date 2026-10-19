from datetime import datetime, timezone
from typing import Any

from app.core.supabase import get_supabase


async def list_products(*, active_only: bool = True, limit: int = 100) -> list[dict[str, Any]]:
    client = await get_supabase()
    q = client.table("products").select("*").order("created_at").limit(limit)
    if active_only:
        q = q.eq("is_active", True)
    return (await q.execute()).data


async def create_product(data: dict[str, Any]) -> dict[str, Any]:
    client = await get_supabase()
    return (await client.table("products").insert(data).execute()).data[0]


async def update_product(product_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    client = await get_supabase()
    res = await client.table("products").update({**data, "meta_synced_at": None}).eq("id", product_id).execute()
    return res.data[0] if res.data else None


async def deactivate_product(product_id: str) -> bool:
    client = await get_supabase()
    res = await client.table("products").update({"is_active": False, "meta_synced_at": None}).eq("id", product_id).execute()
    return bool(res.data)


async def mark_synced(ids: list[str]) -> None:
    if not ids:
        return
    client = await get_supabase()
    await client.table("products").update(
        {"meta_synced_at": datetime.now(timezone.utc).isoformat()}
    ).in_("id", ids).execute()