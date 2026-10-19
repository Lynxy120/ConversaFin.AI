from fastapi import APIRouter

from app.api.v1 import orders, products

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(orders.router)
api_router.include_router(products.router)