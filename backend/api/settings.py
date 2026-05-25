from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import AppSetting
from schemas.settings import AppSettingRead, AppSettingUpdate, BrandProfileUpdate, ScoringWeights

router = APIRouter()


@router.get("/settings", response_model=list[AppSettingRead])
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AppSetting).where(AppSetting.is_secret == False).order_by(AppSetting.category, AppSetting.key)
    )
    return list(result.scalars().all())


@router.patch("/settings/{key}")
async def update_setting(key: str, update: AppSettingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    setting.value = update.value
    await db.commit()
    return {"key": key, "value": update.value}


@router.get("/settings/scoring-weights", response_model=ScoringWeights)
async def get_scoring_weights(db: AsyncSession = Depends(get_db)):
    keys = ["trend_velocity", "cross_source", "competition_density", "novelty", "brand_fit", "review_signal"]
    result = await db.execute(
        select(AppSetting).where(AppSetting.key.in_([f"weight_{k}" for k in keys]))
    )
    settings_map = {s.key: float(s.value or 0) for s in result.scalars().all()}
    return ScoringWeights(
        trend_velocity=settings_map.get("weight_trend_velocity", 0.25),
        cross_source=settings_map.get("weight_cross_source", 0.20),
        competition_density=settings_map.get("weight_competition_density", 0.15),
        novelty=settings_map.get("weight_novelty", 0.15),
        brand_fit=settings_map.get("weight_brand_fit", 0.15),
        review_signal=settings_map.get("weight_review_signal", 0.10),
    )


@router.patch("/settings/scoring-weights")
async def update_scoring_weights(weights: ScoringWeights, db: AsyncSession = Depends(get_db)):
    updates = {
        "weight_trend_velocity": weights.trend_velocity,
        "weight_cross_source": weights.cross_source,
        "weight_competition_density": weights.competition_density,
        "weight_novelty": weights.novelty,
        "weight_brand_fit": weights.brand_fit,
        "weight_review_signal": weights.review_signal,
    }
    for key, value in updates.items():
        result = await db.execute(select(AppSetting).where(AppSetting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(value)
        else:
            db.add(AppSetting(key=key, value=str(value), value_type="float", category="scoring"))
    await db.commit()
    return {"status": "updated", "weights": updates}
