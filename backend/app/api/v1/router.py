from fastapi import APIRouter

from app.api.v1 import orders, payments, products

api_router = APIRouter(prefix="/api/v1")
for r in (products.router, orders.router, payments.router):
    api_router.include_router(r)