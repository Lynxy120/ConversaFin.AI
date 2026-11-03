from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProductIn(BaseModel):
    sku: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    image_url: HttpUrl | None = None
    is_active: bool = True


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    image_url: HttpUrl | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    sku: str
    name: str
    description: str | None = None
    price: Decimal
    image_url: str | None = None
    is_active: bool
    created_at: datetime


class SendListIn(BaseModel):
    to: str = Field(pattern=r"^\+?\d{8,15}$")