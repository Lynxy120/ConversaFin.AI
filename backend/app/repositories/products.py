from typing import Any

from app.core.supabase import get_supabase


async def list_products(
    *, active_only: bool = True, limit: int = 10, offset: int = 0
) -> list[dict[str, Any]]:
    q = (
        (await get_supabase())
        .table("products")
        .select("*")
        .order("created_at")
        .order("id")
        .range(offset, offset + limit - 1)
    )
    if active_only:
        q = q.eq("is_active", True)
    return (await q.execute()).data


async def get(pid: str) -> dict[str, Any] | None:
    r = (
        await (await get_supabase())
        .table("products")
        .select("*")
        .eq("id", pid)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None


async def create(data: dict[str, Any]) -> dict[str, Any]:
    return (await (await get_supabase()).table("products").insert(data).execute()).data[
        0
    ]


async def update(pid: str, data: dict[str, Any]) -> dict[str, Any] | None:
    r = (
        await (await get_supabase())
        .table("products")
        .update(data)
        .eq("id", pid)
        .execute()
    )
    return r.data[0] if r.data else None
