from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import OpportunityScore, Product
from schemas.scoring import OpportunityScoreRead, OpportunityWithProduct, OpportunityList

router = APIRouter()


@router.get("/opportunities", response_model=OpportunityList)
async def list_opportunities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    min_score: float = Query(default=0.0, ge=0, le=100),
    max_score: float = Query(default=100.0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(OpportunityScore, Product)
        .join(Product, OpportunityScore.product_id == Product.id)
        .where(OpportunityScore.total_score >= min_score)
        .where(OpportunityScore.total_score <= max_score)
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(OpportunityScore.total_score.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    items = []
    for score, product in rows:
        items.append(
            OpportunityWithProduct(
                score=OpportunityScoreRead.model_validate(score),
                product_title=product.title,
                product_url=product.source_url,
                product_image=product.image_url,
                category=None,
                is_mock=product.is_mock,
            )
        )

    return OpportunityList(items=items, total=total)


@router.get("/opportunities/top")
async def get_top_opportunities(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OpportunityScore, Product)
        .join(Product, OpportunityScore.product_id == Product.id)
        .order_by(OpportunityScore.total_score.desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "product_id": str(score.product_id),
            "product_title": product.title,
            "total_score": score.total_score,
            "recommendation": score.ai_recommendation,
            "is_mock": product.is_mock,
        }
        for score, product in rows
    ]
