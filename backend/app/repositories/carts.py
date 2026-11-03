from typing import Any

from app.core.supabase import get_supabase


async def add(phone: str, sku: str) -> int:
    r = await (await get_supabase()).rpc("add_to_cart", {"p_phone": phone, "p_sku": sku}).execute()
    return int(r.data)


async def items(phone: str) -> list[dict[str, Any]]:
    r = await (await get_supabase()).table("cart_items").select("quantity, products(sku,name,price)") \
        .eq("customer_phone", phone).execute()
    return r.data


async def clear(phone: str) -> None:
    await (await get_supabase()).table("cart_items").delete().eq("customer_phone", phone).execute()