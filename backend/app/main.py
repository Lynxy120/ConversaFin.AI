import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

from app.api.v1 import telegram
from app.integrations.telegram import get_telegram_client
from app.services.bot_service import get_bot_service
from app.api.v1.router import api_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("httpx").setLevel(
    logging.WARNING
)  # httpx logs full URLs; Telegram URLs contain the bot token
S = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    tg = get_telegram_client()
    if (
        S.public_base_url and S.app_env == "production"
    ):  # self-heal webhook on every Render boot
        r = await tg.set_webhook(
            f"{S.public_base_url.rstrip('/')}/telegram/webhook",
            S.telegram_webhook_secret,
        )
        logging.getLogger("conversafin").info("setWebhook -> %s", r)
    yield
    await tg.aclose()


app = FastAPI(title="ConversaFin.AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in S.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(telegram.router)
app.include_router(api_router)


@app.get("/")
async def health():
    return {"status": "ok", "service": "conversafin-ai", "env": S.app_env}
