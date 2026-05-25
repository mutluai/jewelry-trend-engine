from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import TrendSignal
from schemas.trend import TrendSignalRead, TrendSignalList

router = APIRouter()


@router.get("/trends", response_model=TrendSignalList)
async def list_trends(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    signal_type: str | None = None,
    category: str | None = None,
    direction: str | None = None,
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(TrendSignal)

    if signal_type:
        query = query.where(TrendSignal.signal_type == signal_type)
    if category:
        query = query.where(TrendSignal.category == category)
    if direction:
        query = query.where(TrendSignal.trend_direction == direction)
    if source:
        query = query.where(TrendSignal.source_name == source)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(TrendSignal.created_at.desc())
    )
    result = await db.execute(query)
    signals = result.scalars().all()

    return TrendSignalList(items=list(signals), total=total)


@router.get("/trends/summary")
async def get_trend_summary(db: AsyncSession = Depends(get_db)):
    rising = (await db.execute(
        select(func.count(TrendSignal.id)).where(TrendSignal.trend_direction == "rising")
    )).scalar_one()
    declining = (await db.execute(
        select(func.count(TrendSignal.id)).where(TrendSignal.trend_direction == "declining")
    )).scalar_one()
    stable = (await db.execute(
        select(func.count(TrendSignal.id)).where(TrendSignal.trend_direction == "stable")
    )).scalar_one()

    top_keywords = (await db.execute(
        select(TrendSignal.keyword, func.avg(TrendSignal.velocity_score).label("avg_velocity"))
        .where(TrendSignal.keyword.isnot(None))
        .group_by(TrendSignal.keyword)
        .order_by(func.avg(TrendSignal.velocity_score).desc())
        .limit(10)
    )).all()

    return {
        "rising": rising,
        "declining": declining,
        "stable": stable,
        "top_keywords": [{"keyword": r.keyword, "velocity": r.avg_velocity} for r in top_keywords],
    }
