from pydantic import BaseModel, Field


class AppSettingRead(BaseModel):
    key: str
    value: str | None
    value_type: str
    description: str | None
    category: str | None

    class Config:
        from_attributes = True


class AppSettingUpdate(BaseModel):
    value: str


class ScoringWeights(BaseModel):
    trend_velocity: float = Field(default=0.25, ge=0, le=1)
    cross_source: float = Field(default=0.20, ge=0, le=1)
    competition_density: float = Field(default=0.15, ge=0, le=1)
    novelty: float = Field(default=0.15, ge=0, le=1)
    brand_fit: float = Field(default=0.15, ge=0, le=1)
    review_signal: float = Field(default=0.10, ge=0, le=1)


class BrandProfileUpdate(BaseModel):
    brand_name: str | None = None
    brand_market: str | None = None
    brand_style_focus: str | None = None
    brand_target_customer: str | None = None
    brand_price_min: float | None = None
    brand_price_max: float | None = None
    brand_categories: str | None = None
    report_language: str | None = None
