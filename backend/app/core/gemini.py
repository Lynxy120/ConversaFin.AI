from functools import lru_cache

from google import genai

from app.core.config import get_settings


@lru_cache
def get_gemini_client() -> genai.Client:
    key = get_settings().gemini_api_key
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=key)