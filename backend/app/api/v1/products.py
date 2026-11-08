from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError

from app.core.security import require_admin
from app.repositories import products as repo
from app.schemas.catalog import ProductIn, ProductOut, ProductPatch, SendListIn
from app.services.whatsapp_service import WhatsAppService, get_whatsapp_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(limit: int = Query(10, ge=1, le=10)):
    return await repo.list_products(limit=limit)


@router.post(
    "",
    response_model=ProductOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(body: ProductIn):
    try:
        return await repo.create(body.model_dump(mode="json"))
    except APIError as e:
        if "23505" in str(e):
            # Tampilkan pesan asli dari Postgres biar kelihatan kolom mana yang duplicate
            raise HTTPException(409, f"Conflict: {e.message} ({e.details})") from e
        raise


@router.patch(
    "/{pid}", response_model=ProductOut, dependencies=[Depends(require_admin)]
)
async def patch(pid: UUID, body: ProductPatch):
    d = body.model_dump(mode="json", exclude_unset=True)
    if not d:
        raise HTTPException(400, "empty")
    row = await repo.update(str(pid), d)
    if not row:
        raise HTTPException(404, "not found")
    return row


@router.delete("/{pid}", dependencies=[Depends(require_admin)])
async def deactivate(pid: UUID):
    if not await repo.update(str(pid), {"is_active": False}):
        raise HTTPException(404, "not found")
    return {"status": "deactivated"}


@router.post("/send-list", dependencies=[Depends(require_admin)])
async def send_list(
    body: SendListIn, wa: WhatsAppService = Depends(get_whatsapp_service)
):
    r = await wa.send_catalog(body.to)
    if not r.get("ok"):
        raise HTTPException(502, r.get("error", "send failed"))
    return r


@router.get(
    "/all", response_model=list[ProductOut], dependencies=[Depends(require_admin)]
)
async def list_all(limit: int = Query(200, ge=1, le=500)):
    return await repo.list_products(active_only=False, limit=limit)
