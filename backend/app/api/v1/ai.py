from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.security import require_admin
from app.services.finance_service import FinanceError, FinanceService, RunResult, get_finance_service
from app.services.gemini_service import AIError
from app.services.media_service import MediaError, clean_mime

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(require_admin)])


class ParseIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    save: bool = False
    ref: str | None = Field(default=None, max_length=100)


def _out(r: RunResult) -> dict:
    return {"extraction": r.extraction.model_dump(), "candidates": r.candidates, "saved": r.saved, "rejected": r.rejected}


async def _run(svc: FinanceService, **kw) -> dict:
    try:
        return _out(await svc.run(actor="api", source="ai", **kw))
    except (FinanceError, MediaError) as e:
        raise HTTPException(422, str(e)) from e
    except AIError as e:
        raise HTTPException(502, str(e)) from e


@router.post("/parse")
async def parse_text(body: ParseIn, svc: FinanceService = Depends(get_finance_service)):
    return await _run(svc, kind="text", text=body.text, save=body.save, ref=f"api:{body.ref or uuid4().hex}")


@router.post("/parse-media")
async def parse_media(
    file: UploadFile = File(...), save: bool = Form(False), ref: str | None = Form(None),
    svc: FinanceService = Depends(get_finance_service),
):
    mime = clean_mime(file.content_type)
    kind = "audio" if mime.startswith("audio/") else "image" if mime.startswith("image/") else None
    if not kind:
        raise HTTPException(415, "Only audio/* or image/* accepted")
    data = await file.read(get_settings().media_max_mb * 1024 * 1024 + 1)
    return await _run(svc, kind=kind, data=data, mime=mime, save=save, ref=f"api:{ref or uuid4().hex}")