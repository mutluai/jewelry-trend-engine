import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID
from sqlalchemy import JSON as JSONB
import enum
from .base import Base, UUIDMixin, TimestampMixin


class LegalStatus(str, enum.Enum):
    official_api = "official_api"
    public_allowed = "public_allowed"
    stub = "stub"
    mock = "mock"


class RunStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"
    skipped = "skipped"


class Source(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    connector_class: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_status: Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True)
    rate_limit_seconds: Mapped[float] = mapped_column(Float, default=3.0)
    description: Mapped[str | None] = mapped_column(Text)
    docs_url: Mapped[str | None] = mapped_column(String(500))

    runs: Mapped[list["SourceRun"]] = relationship(back_populates="source")
    products: Mapped[list["Product"]] = relationship(back_populates="source")


class SourceRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "source_runs"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="running")
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_saved: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    meta: Mapped[dict | None] = mapped_column(JSONB)

    source: Mapped["Source"] = relationship(back_populates="runs")
