from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProductCreate(BaseModel):
    retailer_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_\-]+$")
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    image_url: HttpUrl | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    image_url: HttpUrl | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    retailer_id: str
    name: str
    description: str | None = None
    price: Decimal
    currency: str = "IDR"
    image_url: str | None = None
    is_active: bool = True
    meta_synced_at: datetime | None = None
    created_at: datetime


class SendCatalogRequest(BaseModel):
    to: str = Field(pattern=r"^\+?\d{8,15}$")