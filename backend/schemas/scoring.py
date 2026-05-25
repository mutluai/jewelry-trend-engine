import uuid
from datetime import datetime
from pydantic import BaseModel


class OpportunityScoreRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    total_score: float
    trend_velocity_score: float | None
    cross_source_score: float | None
    competition_density_score: float | None
    novelty_score: float | None
    brand_fit_score: float | None
    review_signal_score: float | None
    score_version: str
    ai_opportunity_narrative: str | None
    ai_recommendation: str | None
    ai_risk_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class OpportunityWithProduct(BaseModel):
    score: OpportunityScoreRead
    product_title: str
    product_url: str | None
    product_image: str | None
    category: str | None
    is_mock: bool


class OpportunityList(BaseModel):
    items: list[OpportunityWithProduct]
    total: int
