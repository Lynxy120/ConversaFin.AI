from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import require_admin
from app.repositories import orders as repo

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(require_admin)])


@router.get("")
async def list_orders(limit: int = Query(20, ge=1, le=100), status: str | None = None):
    return await repo.list_orders(limit=limit, status=status)


@router.get("/{order_id}")
async def get_order(order_id: UUID):
    order = await repo.get_order(str(order_id))
    if not order:
        raise HTTPException(404, "Order not found")
    return order