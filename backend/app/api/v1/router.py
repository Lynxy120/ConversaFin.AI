from fastapi import APIRouter

from app.api.v1 import ai, orders, payments, products

api_router = APIRouter(prefix="/api/v1")
for r in (products.router, orders.router, payments.router, ai.router):
    api_router.include_router(r)