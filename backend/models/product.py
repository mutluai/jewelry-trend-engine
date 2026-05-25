import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID
from sqlalchemy import JSON as JSONB
import enum
from .base import Base, UUIDMixin, TimestampMixin
from .taxonomy import product_materials, product_stones, product_colors, product_style_tags


class ProductStatus(str, enum.Enum):
    raw = "raw"
    analyzed = "analyzed"
    scored = "scored"
    archived = "archived"


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "products"

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id")
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id")
    )
    competitor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitors.id")
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id")
    )

    external_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    image_url: Mapped[str | None] = mapped_column(String(1000))

    price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(10))
    price_usd: Mapped[float | None] = mapped_column(Float)

    review_count: Mapped[int] = mapped_column(Integer, default=0)
    review_rating: Mapped[float | None] = mapped_column(Float)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    favorites_count: Mapped[int] = mapped_column(Integer, default=0)

    target_gender: Mapped[str | None] = mapped_column(String(50))
    price_tier: Mapped[str | None] = mapped_column(String(50))
    theme: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(20), default="raw")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ai_attributes: Mapped[dict | None] = mapped_column(JSONB)
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_model_used: Mapped[str | None] = mapped_column(String(100))

    source: Mapped["Source"] = relationship(back_populates="products")
    brand: Mapped["Brand | None"] = relationship(back_populates="products")
    competitor: Mapped["Competitor | None"] = relationship(back_populates="products")
    category: Mapped["Category | None"] = relationship(back_populates="products")

    materials: Mapped[list["Material"]] = relationship(
        secondary=product_materials, back_populates="products"
    )
    stones: Mapped[list["Stone"]] = relationship(
        secondary=product_stones, back_populates="products"
    )
    colors: Mapped[list["Color"]] = relationship(
        secondary=product_colors, back_populates="products"
    )
    style_tags: Mapped[list["StyleTag"]] = relationship(
        secondary=product_style_tags, back_populates="products"
    )

    snapshots: Mapped[list["ProductSnapshot"]] = relationship(back_populates="product")
    opportunity_scores: Mapped[list["OpportunityScore"]] = relationship(back_populates="product")
    image_assets: Mapped[list["ImageAsset"]] = relationship(back_populates="product")


class ProductSnapshot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_snapshots"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    price: Mapped[float | None] = mapped_column(Float)
    price_usd: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    review_rating: Mapped[float | None] = mapped_column(Float)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    favorites_count: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    snapshot_data: Mapped[dict | None] = mapped_column(JSONB)

    product: Mapped["Product"] = relationship(back_populates="snapshots")
