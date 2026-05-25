import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON as JSONB
from .base import Base, UUIDMixin, TimestampMixin


trend_signal_products = Table(
    "trend_signal_products",
    Base.metadata,
    Column("trend_signal_id", UUID(as_uuid=True), ForeignKey("trend_signals.id"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
)


class TrendSignal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "trend_signals"

    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    keyword: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))
    material: Mapped[str | None] = mapped_column(String(100))
    style: Mapped[str | None] = mapped_column(String(100))

    interest_value: Mapped[float | None] = mapped_column(Float)
    trend_direction: Mapped[str | None] = mapped_column(String(20))
    velocity_score: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)

    source_name: Mapped[str | None] = mapped_column(String(100))
    geo: Mapped[str | None] = mapped_column(String(10))
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ai_analysis: Mapped[dict | None] = mapped_column(JSONB)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    is_mock: Mapped[bool] = mapped_column(default=False)

    products: Mapped[list["Product"]] = relationship(
        secondary=trend_signal_products
    )
