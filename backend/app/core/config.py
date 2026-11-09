from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore", case_sensitive=False
    )
    app_env: str = "development"
    admin_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    brand: str = "ConversaFin"
    supabase_url: str = ""
    supabase_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    business_profile: str = "Toko online produk kopi dan makanan, dijual via WhatsApp"
    gemini_max_output_tokens: int = 2048
    gemini_timeout: int = 45
    finance_min_confidence: float = 0.6
    media_max_mb: int = 10
    wa_phone_number_id: str = "1471407319378387"
    wa_waba_id: str = "2668517793563623"
    wa_access_token: str = ""
    wa_verify_token: str = "token_rahasia_webhook_123"
    wa_app_secret: str = ""
    wa_owner_number: str = ""
    wa_graph_version: str = "v26.0"
    wa_dry_run: bool = True
    midtrans_server_key: str = ""
    midtrans_client_key: str = ""
    midtrans_is_production: bool = False
    midtrans_qris_expiry_minutes: int = 15
    midtrans_verify_status: bool = True
    receipt_bucket: str = "receipts"
    receipt_url_ttl: int = 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()