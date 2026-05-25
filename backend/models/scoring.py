import uuid
from sqlalchemy import String, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID
from sqlalchemy import JSON as JSONB
from .base import Base, UUIDMixin, TimestampMixin


class OpportunityScore(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "opportunity_scores"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )

    total_score: Mapped[float] = mapped_column(Float, nullable=False)

    trend_velocity_score: Mapped[float | None] = mapped_column(Float)
    cross_source_score: Mapped[float | None] = mapped_column(Float)
    competition_density_score: Mapped[float | None] = mapped_column(Float)
    novelty_score: Mapped[float | None] = mapped_column(Float)
    brand_fit_score: Mapped[float | None] = mapped_column(Float)
    review_signal_score: Mapped[float | None] = mapped_column(Float)

    score_version: Mapped[str] = mapped_column(String(20), default="1.0")
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    ai_opportunity_narrative: Mapped[str | None] = mapped_column(Text)
    ai_recommendation: Mapped[str | None] = mapped_column(Text)
    ai_risk_notes: Mapped[str | None] = mapped_column(Text)

    product: Mapped["Product"] = relationship(back_populates="opportunity_scores")
