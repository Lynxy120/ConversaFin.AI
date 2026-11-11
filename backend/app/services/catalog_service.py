import logging
from decimal import Decimal
from functools import lru_cache
from typing import Any

from app.core.config import Settings, get_settings
from app.repositories import products as products_repo

logger = logging.getLogger("conversafin.catalog")


class CatalogError(Exception):
    pass


class CatalogService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()

    def _to_item(self, p: dict[str, Any]) -> dict[str, Any]:
        price = Decimal(str(p["price"]))
        return {
            "id": p["retailer_id"],
            "title": p["name"][:150],
            "description": (p.get("description") or p["name"])[:5000],
            "availability": "in stock" if p.get("is_active") else "out of stock",
            "condition": "new",
            "price": f"{price:.2f} {p.get('currency') or 'IDR'}",
            "link": f"{self._s.catalog_link_base_url.rstrip('/')}/{p['retailer_id']}",
            "image_link": p["image_url"],
            "brand": self._s.catalog_brand,
        }

    async def get_telegram_catalog(self) -> list[dict[str, Any]]:
        """
        Retrieves active products formatted for Telegram Inline Keyboards.
        """
        products = await products_repo.list_products(active_only=True, limit=50)
        return [self._to_item(p) for p in products]


@lru_cache
def get_catalog_service() -> CatalogService:
    return CatalogService()
