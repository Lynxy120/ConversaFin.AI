import hmac

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings


async def require_admin(x_api_key: str | None = Header(default=None), s: Settings = Depends(get_settings)) -> None:
    if not s.admin_api_key or not x_api_key or not hmac.compare_digest(x_api_key.encode(), s.admin_api_key.encode()):
        raise HTTPException(401, "Invalid or missing API key")