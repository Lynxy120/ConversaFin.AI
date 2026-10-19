import asyncio

from supabase import AsyncClient, acreate_client

from app.core.config import get_settings

_client: AsyncClient | None = None
_lock = asyncio.Lock()


async def get_supabase() -> AsyncClient:
    global _client
    if _client is None:
        async with _lock:
            if _client is None:
                s = get_settings()
                _client = await acreate_client(s.supabase_url, s.supabase_key)
    return _client