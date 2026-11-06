import asyncio
import logging
from datetime import date
from functools import lru_cache
from typing import Literal

from google.genai import errors, types
from pydantic import ValidationError

from app.ai.prompts import build_system_prompt, user_prompt
from app.core.config import get_settings
from app.core.gemini import get_gemini_client
from app.schemas.finance import ExtractionResult

log = logging.getLogger("conversafin.gemini")
RETRYABLE = {429, 500, 502, 503, 504}


class AIError(Exception): ...


class GeminiService:
    def __init__(self) -> None:
        self._s = get_settings()
        self._client = get_gemini_client()
        # temperature intentionally left at model default (Gemini 3 guidance)
        self._cfg = types.GenerateContentConfig(
            system_instruction=build_system_prompt(self._s.business_profile),
            response_mime_type="application/json",
            response_schema=ExtractionResult,
            max_output_tokens=self._s.gemini_max_output_tokens,
        )

    async def extract(
        self, *, kind: Literal["text", "audio", "image"], today: date,
        text: str | None = None, data: bytes | None = None, mime: str | None = None,
    ) -> ExtractionResult:
        prompt = user_prompt(kind, today, text)
        contents = [types.Part.from_bytes(data=data, mime_type=mime), prompt] if data else prompt

        for attempt in range(3):
            try:
                resp = await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=self._s.gemini_model, contents=contents, config=self._cfg),
                    timeout=self._s.gemini_timeout,
                )
                break
            except (errors.APIError, asyncio.TimeoutError) as e:
                code = getattr(e, "code", None)
                if attempt < 2 and (code in RETRYABLE or isinstance(e, asyncio.TimeoutError)):
                    await asyncio.sleep(1.5 * 2**attempt)
                    continue
                log.error("Gemini failed (%s): %s", code or "timeout", e)
                raise AIError(f"Layanan AI gagal ({code or 'timeout'}). Coba lagi.") from e

        if not resp.text:
            raise AIError("AI tidak mengembalikan hasil (kemungkinan diblokir).")
        usage = resp.usage_metadata.total_token_count if resp.usage_metadata else "?"
        log.info("gemini kind=%s tokens=%s", kind, usage)
        try:
            return ExtractionResult.model_validate_json(resp.text)
        except ValidationError as e:
            log.error("Invalid AI JSON: %s | %s", e.errors()[:2], resp.text[:300])
            raise AIError("Format respons AI tidak valid.") from e


@lru_cache
def get_gemini_service() -> GeminiService:
    return GeminiService()