import logging
from decimal import Decimal
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.repositories import products as products_repo

logger = logging.getLogger("conversafin.catalog")
BATCH_SIZE = 500


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

    async def sync_all(self) -> dict[str, Any]:
        if not self._s.wa_catalog_id:
            raise CatalogError("WA_CATALOG_ID is not set")

        products = await products_repo.list_products(active_only=False, limit=1000)
        syncable = [p for p in products if p.get("image_url")]
        skipped = [p["retailer_id"] for p in products if not p.get("image_url")]
        if not syncable:
            raise CatalogError("No products with image_url to sync")

        handles: list[str] = []
        async with httpx.AsyncClient(
            base_url=f"https://graph.facebook.com/{self._s.wa_graph_version}",
            timeout=httpx.Timeout(30.0, connect=5.0),
            headers={"Authorization": f"Bearer {self._s.wa_access_token}"},
        ) as client:
            for i in range(0, len(syncable), BATCH_SIZE):
                chunk = syncable[i : i + BATCH_SIZE]
                resp = await client.post(
                    f"/{self._s.wa_catalog_id}/items_batch",
                    json={
                        "item_type": "PRODUCT_ITEM",
                        "allow_upsert": True,
                        "requests": [{"method": "UPDATE", "data": self._to_item(p)} for p in chunk],
                    },
                )
                if resp.status_code >= 400:
                    raise CatalogError(f"Meta {resp.status_code}: {resp.text[:300]}")
                handles.extend(resp.json().get("handles", []))

        await products_repo.mark_synced([p["id"] for p in syncable])
        logger.info("Catalog sync submitted: %d items, handles=%s", len(syncable), handles)
        return {"synced": len(syncable), "skipped_no_image": skipped, "handles": handles}


@lru_cache
def get_catalog_service() -> CatalogService:
    return CatalogService()