from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import require_admin
from app.repositories import orders as repo

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(require_admin)])


@router.get("")
async def list_orders(limit: int = Query(20, ge=1, le=100), status: str | None = None):
    return await repo.list_orders(limit, status)


@router.get("/{oid}")
async def get_order(oid: UUID):
    o = await repo.get_order(str(oid))
    if not o:
        raise HTTPException(404, "not found")
    return o