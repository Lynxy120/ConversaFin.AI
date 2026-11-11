from typing import Any

from postgrest.exceptions import APIError

from app.core.supabase import get_supabase


class UnknownProduct(Exception): ...


async def add(chat_id: str, product_id: str) -> int:
    try:
        r = (
            await (await get_supabase())
            .rpc("add_to_cart", {"p_chat": chat_id, "p_product": product_id})
            .execute()
        )
    except APIError as e:
        if "UNKNOWN_PRODUCT" in str(e):
            raise UnknownProduct from e
        raise
    return int(r.data)


async def items(chat_id: str) -> list[dict[str, Any]]:
    r = (
        await (await get_supabase())
        .table("cart_items")
        .select("quantity, products(id,name,price)")
        .eq("chat_id", chat_id)
        .order("updated_at")
        .execute()
    )
    return r.data


async def clear(chat_id: str) -> None:
    await (await get_supabase()).table("cart_items").delete().eq(
        "chat_id", chat_id
    ).execute()
