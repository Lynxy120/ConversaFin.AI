from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"

    supabase_url: str = ""
    supabase_key: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"

    wa_phone_number_id: str = "1369280939600113"
    wa_access_token: str = ""
    wa_verify_token: str = "token_rahasia_webhook_123"
    wa_app_secret: str = ""
    wa_owner_number: str = ""  # comma-separated, e.g. 6281234567890,6285111222333
    wa_graph_version: str = "v23.0"
    wa_dry_run: bool = False

    midtrans_server_key: str = ""
    midtrans_client_key: str = ""
    midtrans_is_production: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()