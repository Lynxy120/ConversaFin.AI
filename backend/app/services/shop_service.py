from functools import lru_cache
from typing import Any
from uuid import UUID

from app.core.format import rupiah
from app.integrations.telegram import kb
from app.repositories import carts as carts_repo
from app.repositories import orders as orders_repo
from app.repositories import products as products_repo
from app.repositories.carts import UnknownProduct
from app.repositories.orders import EmptyCart

PAGE = 8
__all__ = [
    "ShopService",
    "get_shop_service",
    "UnknownProduct",
    "EmptyCart",
    "order_text",
]


def order_text(o: dict[str, Any]) -> str:
    lines = [
        f"• {i['product_name']} ×{i['quantity']} = {rupiah(i['subtotal'])}"
        for i in o["order_items"]
    ]
    return (
        f"🧾 Pesanan #{o['id'][:8].upper()}\n"
        + "\n".join(lines)
        + f"\nTotal: {rupiah(o['total_price'])}"
    )


class ShopService:
    async def catalog(self, page: int = 0) -> tuple[str, dict | None]:
        page = max(page, 0)
        prods = await products_repo.list_products(limit=PAGE + 1, offset=page * PAGE)
        more, prods = len(prods) > PAGE, prods[:PAGE]
        if not prods:
            return "Katalog masih kosong.", None
        rows = [
            [(f"➕ {p['name'][:28]} · {rupiah(p['price'])}", f"p:{p['id']}")]
            for p in prods
        ]  # "p:"+uuid = 38 bytes
        nav = ([("⬅️", f"cat:{page - 1}")] if page else []) + (
            [("➡️", f"cat:{page + 1}")] if more else []
        )
        if nav:
            rows.append(nav)
        rows.append([("🛒 Keranjang", "c:view")])
        return "🛍 Katalog Produk\nTap produk untuk menambah ke keranjang.", kb(rows)

    async def add(self, chat_id: int, raw_id: str) -> int:
        try:
            pid = str(UUID(raw_id))
        except ValueError as e:
            raise UnknownProduct from e
        return await carts_repo.add(str(chat_id), pid)

    async def cart(self, chat_id: int) -> tuple[str, dict]:
        items = await carts_repo.items(str(chat_id))
        if not items:
            return "🛒 Keranjang kosong.", kb([[("🛍 Katalog", "cat:0")]])
        total = sum(float(i["products"]["price"]) * i["quantity"] for i in items)
        lines = [
            f"• {i['products']['name']} ×{i['quantity']} = {rupiah(float(i['products']['price']) * i['quantity'])}"
            for i in items
        ]
        return "🛒 Keranjang\n" + "\n".join(lines) + f"\nTotal: {rupiah(total)}", kb(
            [
                [("➕ Tambah", "cat:0"), ("🧹 Kosongkan", "c:clr")],
                [("✅ Checkout", "c:co")],
            ]
        )

    async def clear(self, chat_id: int) -> None:
        await carts_repo.clear(str(chat_id))

    async def checkout(self, chat_id: int, name: str, ref: str) -> dict[str, Any]:
        return await orders_repo.checkout(str(chat_id), name, ref)


@lru_cache
def get_shop_service() -> ShopService:
    return ShopService()
