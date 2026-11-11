from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
        case_sensitive=False,
    )
    app_env: str = "development"
    admin_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    public_base_url: str = ""
    brand: str = "ConversaFin"
    business_profile: str = "Toko online produk kopi dan makanan, dijual via Telegram"

    supabase_url: str = ""
    supabase_key: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_max_output_tokens: int = 2048
    gemini_timeout: int = 45
    finance_min_confidence: float = 0.6
    media_max_mb: int = 10

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_owner_ids: str = ""
    telegram_dry_run: bool = True

    midtrans_server_key: str = ""
    midtrans_client_key: str = ""
    midtrans_is_production: bool = False
    midtrans_qris_expiry_minutes: int = 15
    midtrans_verify_status: bool = True
    receipt_bucket: str = "receipts"
    receipt_url_ttl: int = 86400

    @property
    def owner_ids(self) -> set[int]:
        return {
            int(x) for x in self.telegram_owner_ids.split(",") if x.strip().isdigit()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
