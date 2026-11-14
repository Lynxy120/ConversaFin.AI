import re
import secrets
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from postgrest.exceptions import APIError

from app.core.security import require_admin
from app.repositories import products as repo
from app.schemas.catalog import ProductOut
from app.services import image_service as images

router = APIRouter(prefix="/products", tags=["products"])


def _sku(name: str) -> str:
    stem = re.sub(r"[^A-Z0-9]", "", name.upper())[:3].ljust(3, "X")
    return f"{stem}-{secrets.token_hex(3).upper()}"


@router.get("", response_model=list[ProductOut])
async def list_products(limit: int = Query(10, ge=1, le=10)):
    return await repo.list_products(limit=limit)


@router.get(
    "/all", response_model=list[ProductOut], dependencies=[Depends(require_admin)]
)
async def list_all(limit: int = Query(200, ge=1, le=500)):
    return await repo.list_products(active_only=False, limit=limit)


@router.post(
    "",
    response_model=ProductOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(
    name: str = Form(..., min_length=1, max_length=150),
    price: Decimal = Form(..., ge=0, max_digits=14, decimal_places=2),
    description: str | None = Form(None, max_length=500),
    is_active: bool = Form(True),
    image: UploadFile | None = File(None),
):
    webp = (
        await images.prepare(image) if image else None
    )  # validation/conversion before any write
    path = url = None
    if webp:
        path = f"{uuid4().hex}.webp"
        url = await images.upload(path, webp)  # storage first, then DB
    try:
        for _ in range(5):
            try:
                return await repo.create(
                    {
                        "sku": _sku(name),
                        "name": name.strip(),
                        "price": float(price),
                        "description": (description or "").strip() or None,
                        "is_active": is_active,
                        "image_url": url,
                        "image_path": path,
                    }
                )
            except APIError as e:
                if "23505" not in str(e):
                    raise
        raise HTTPException(503, "Could not allocate a unique SKU, retry")
    except BaseException:
        await images.remove(path)  # no orphan files if the insert fails
        raise


@router.patch(
    "/{pid}", response_model=ProductOut, dependencies=[Depends(require_admin)]
)
async def patch(
    pid: UUID,
    name: str | None = Form(None, min_length=1, max_length=150),
    price: Decimal | None = Form(None, ge=0, max_digits=14, decimal_places=2),
    description: str | None = Form(None, max_length=500),
    is_active: bool | None = Form(None),
    remove_image: bool = Form(False),
    image: UploadFile | None = File(None),
):
    cur = await repo.get(str(pid))
    if not cur:
        raise HTTPException(404, "Product not found")
    data: dict = {}
    if name is not None:
        data["name"] = name.strip()
    if price is not None:
        data["price"] = float(price)
    if description is not None:
        data["description"] = description.strip() or None
    if is_active is not None:
        data["is_active"] = is_active

    new_path = None
    if image:
        webp = await images.prepare(image)
        new_path = f"{uuid4().hex}.webp"
        data["image_url"], data["image_path"] = (
            await images.upload(new_path, webp),
            new_path,
        )
    elif remove_image:
        data["image_url"] = data["image_path"] = None
    if not data:
        raise HTTPException(400, "No fields to update")

    try:
        row = await repo.update(str(pid), data)
    except BaseException:
        await images.remove(new_path)
        raise
    if not row:
        await images.remove(new_path)
        raise HTTPException(404, "Product not found")
    if (image or remove_image) and cur.get("image_path"):
        await images.remove(cur["image_path"])  # drop the replaced file
    return row


@router.delete("/{pid}", dependencies=[Depends(require_admin)])
async def deactivate(pid: UUID):
    if not await repo.update(str(pid), {"is_active": False}):
        raise HTTPException(404, "Product not found")
    return {"status": "deactivated"}
