from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from database import get_db
from models import Product, OpportunityScore
from schemas.product import ProductRead, ProductList

router = APIRouter()


@router.get("/products", response_model=ProductList)
async def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    material: str | None = None,
    source: str | None = None,
    status: str | None = None,
    is_mock: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Product)

    if status:
        query = query.where(Product.status == status)
    if is_mock is not None:
        query = query.where(Product.is_mock == is_mock)
    if search:
        query = query.where(
            or_(
                Product.title.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Product.created_at.desc())
    result = await db.execute(query)
    products = result.scalars().all()

    return ProductList(items=list(products), total=total, page=page, page_size=page_size)


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/stats/overview")
async def get_overview_stats(db: AsyncSession = Depends(get_db)):
    total_products = (await db.execute(select(func.count(Product.id)))).scalar_one()
    mock_products = (await db.execute(
        select(func.count(Product.id)).where(Product.is_mock == True)
    )).scalar_one()
    scored_products = (await db.execute(
        select(func.count(Product.id)).where(Product.status == "scored")
    )).scalar_one()
    top_scores = (await db.execute(
        select(OpportunityScore).order_by(OpportunityScore.total_score.desc()).limit(5)
    )).scalars().all()

    return {
        "total_products": total_products,
        "real_products": total_products - mock_products,
        "mock_products": mock_products,
        "scored_products": scored_products,
        "top_opportunities": [
            {"product_id": str(s.product_id), "score": s.total_score}
            for s in top_scores
        ],
    }
