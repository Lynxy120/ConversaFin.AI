from fastapi import APIRouter

from app.api.v1 import orders, products, payments, ai, bot, finance

api_router = APIRouter(prefix="/api/v1")
for r in (
    products.router,
    orders.router,
    payments.router,
    ai.router,
    finance.router,
    bot.router,
):
    api_router.include_router(r)
