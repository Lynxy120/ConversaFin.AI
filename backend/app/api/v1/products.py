from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError

from app.core.security import require_admin
from app.repositories import products as repo
from app.schemas.catalog import ProductCreate, ProductOut, ProductUpdate, SendCatalogRequest
from app.services.catalog_service import CatalogError, get_catalog_service
from app.services.whatsapp_service import WhatsAppService, get_whatsapp_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(limit: int = Query(100, ge=1, le=200)):
    return await repo.list_products(active_only=True, limit=limit)


@router.post("", response_model=ProductOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_product(body: ProductCreate):
    try:
        return await repo.create_product(body.model_dump(mode="json"))
    except APIError as exc:
        if "23505" in str(exc):
            raise HTTPException(409, "retailer_id already exists") from exc
        raise


@router.patch("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
async def update_product(product_id: UUID, body: ProductUpdate):
    data = body.model_dump(mode="json", exclude_unset=True)
    if not data:
        raise HTTPException(400, "No fields to update")
    row = await repo.update_product(str(product_id), data)
    if not row:
        raise HTTPException(404, "Product not found")
    return row


@router.delete("/{product_id}", dependencies=[Depends(require_admin)])
async def deactivate_product(product_id: UUID):
    if not await repo.deactivate_product(str(product_id)):
        raise HTTPException(404, "Product not found")
    return {"status": "deactivated"}


@router.post("/sync", dependencies=[Depends(require_admin)])
async def sync_catalog():
    try:
        return await get_catalog_service().sync_all()
    except CatalogError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/send-catalog", dependencies=[Depends(require_admin)])
async def send_catalog(body: SendCatalogRequest, service: WhatsAppService = Depends(get_whatsapp_service)):
    result = await service.send_catalog(body.to)
    if not result.get("ok"):
        raise HTTPException(502, result.get("error", "send failed"))
    return result