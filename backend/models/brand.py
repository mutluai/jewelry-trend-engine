from sqlalchemy import String, Text, ARRAY, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDMixin, TimestampMixin


class Brand(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    market: Mapped[str | None] = mapped_column(String(500))
    style_focus: Mapped[str | None] = mapped_column(String(500))
    target_customer: Mapped[str | None] = mapped_column(Text)
    price_min: Mapped[float | None] = mapped_column(Float)
    price_max: Mapped[float | None] = mapped_column(Float)
    categories: Mapped[str | None] = mapped_column(Text)
    report_language: Mapped[str] = mapped_column(String(10), default="tr")
    is_active: Mapped[bool] = mapped_column(default=True)

    products: Mapped[list["Product"]] = relationship(back_populates="brand")
    competitors: Mapped[list["Competitor"]] = relationship(back_populates="brand")
