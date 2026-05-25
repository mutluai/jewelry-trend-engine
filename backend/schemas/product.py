import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, HttpUrl


class ProductCreate(BaseModel):
    title: str
    description: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    price: float | None = None
    currency: str | None = None
    price_usd: float | None = None
    review_count: int = 0
    review_rating: float | None = None
    sales_count: int = 0
    favorites_count: int = 0
    target_gender: str | None = None
    price_tier: str | None = None
    theme: str | None = None
    external_id: str | None = None
    is_mock: bool = False


class ProductRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    source_url: str | None
    image_url: str | None
    price: float | None
    currency: str | None
    price_usd: float | None
    review_count: int
    review_rating: float | None
    sales_count: int
    favorites_count: int
    target_gender: str | None
    price_tier: str | None
    theme: str | None
    status: str
    is_mock: bool
    collected_at: datetime | None
    ai_attributes: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int
