from sqlalchemy import String, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON as JSONB
from .base import Base, UUIDMixin, TimestampMixin


class ConnectorConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "connector_configs"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_seconds: Mapped[float] = mapped_column(Float, default=3.0)
    max_records_per_run: Mapped[int | None] = mapped_column()
    legal_status: Mapped[str] = mapped_column(String(50), nullable=False)
    legal_notes: Mapped[str | None] = mapped_column(Text)
    config_json: Mapped[dict | None] = mapped_column(JSONB)
    last_run_at: Mapped[str | None] = mapped_column(String(50))
    last_run_status: Mapped[str | None] = mapped_column(String(20))
    last_error: Mapped[str | None] = mapped_column(Text)


class AppSetting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(String(20), default="string")
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50))
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
