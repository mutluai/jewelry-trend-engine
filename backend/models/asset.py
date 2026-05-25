import uuid
from sqlalchemy import String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID
from sqlalchemy import JSON as JSONB
from .base import Base, UUIDMixin, TimestampMixin


class ImageAsset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "image_assets"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(String(1000))
    storage_path: Mapped[str | None] = mapped_column(String(500))
    storage_url: Mapped[str | None] = mapped_column(String(1000))
    width: Mapped[int | None] = mapped_column()
    height: Mapped[int | None] = mapped_column()
    file_size_bytes: Mapped[int | None] = mapped_column()
    content_type: Mapped[str | None] = mapped_column(String(100))
    is_primary: Mapped[bool] = mapped_column(default=False)

    ai_visual_tags: Mapped[list | None] = mapped_column(JSONB)
    ai_style_description: Mapped[str | None] = mapped_column(Text)
    ai_material_guess: Mapped[str | None] = mapped_column(String(255))
    ai_analyzed_at: Mapped[str | None] = mapped_column(String(50))

    product: Mapped["Product"] = relationship(back_populates="image_assets")
