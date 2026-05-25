import uuid
from sqlalchemy import String, Text, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID
from .base import Base, UUIDMixin, TimestampMixin


class Competitor(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "competitors"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500))
    etsy_shop_id: Mapped[str | None] = mapped_column(String(100))
    market_position: Mapped[str | None] = mapped_column(String(100))
    price_range_min: Mapped[float | None] = mapped_column(Float)
    price_range_max: Mapped[float | None] = mapped_column(Float)
    product_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    brand: Mapped["Brand"] = relationship(back_populates="competitors")
    products: Mapped[list["Product"]] = relationship(back_populates="competitor")
