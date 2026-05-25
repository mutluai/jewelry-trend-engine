import uuid
from datetime import datetime
from pydantic import BaseModel


class TrendSignalRead(BaseModel):
    id: uuid.UUID
    signal_type: str
    keyword: str | None
    category: str | None
    material: str | None
    style: str | None
    interest_value: float | None
    trend_direction: str | None
    velocity_score: float | None
    confidence: float | None
    source_name: str | None
    geo: str | None
    period_start: datetime | None
    period_end: datetime | None
    is_mock: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TrendSignalList(BaseModel):
    items: list[TrendSignalRead]
    total: int
