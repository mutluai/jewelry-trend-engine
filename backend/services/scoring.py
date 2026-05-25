"""
Scoring Engine — composite 0-100 opportunity score.
Weights are configurable via app_settings table (or use defaults).
Stores full breakdown per product.
"""
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ScoreWeights:
    trend_velocity: float = 0.25
    cross_source: float = 0.20
    competition_density: float = 0.15
    novelty: float = 0.15
    brand_fit: float = 0.15
    review_signal: float = 0.10

    def normalize(self) -> "ScoreWeights":
        total = (
            self.trend_velocity + self.cross_source + self.competition_density
            + self.novelty + self.brand_fit + self.review_signal
        )
        if total == 0:
            return ScoreWeights()
        factor = 1.0 / total
        return ScoreWeights(
            trend_velocity=self.trend_velocity * factor,
            cross_source=self.cross_source * factor,
            competition_density=self.competition_density * factor,
            novelty=self.novelty * factor,
            brand_fit=self.brand_fit * factor,
            review_signal=self.review_signal * factor,
        )


@dataclass
class ScoreComponents:
    trend_velocity: float = 0.0    # 0-100: how fast is related trend growing
    cross_source: float = 0.0      # 0-100: how many sources show this
    competition_density: float = 0.0  # 0-100: inverted — less competition = higher
    novelty: float = 0.0           # 0-100: how new/unseen in our catalog
    brand_fit: float = 0.0         # 0-100: how well it matches brand profile
    review_signal: float = 0.0     # 0-100: review count + rating signal


class ScoringEngine:

    def __init__(self, weights: ScoreWeights | None = None):
        self.weights = (weights or ScoreWeights()).normalize()

    def compute_total(self, components: ScoreComponents) -> float:
        w = self.weights
        total = (
            components.trend_velocity * w.trend_velocity
            + components.cross_source * w.cross_source
            + components.competition_density * w.competition_density
            + components.novelty * w.novelty
            + components.brand_fit * w.brand_fit
            + components.review_signal * w.review_signal
        )
        return round(min(max(total, 0), 100), 2)

    def score_product(self, product: dict, context: dict | None = None) -> tuple[float, ScoreComponents]:
        context = context or {}
        components = ScoreComponents()

        # trend_velocity: based on keyword trend data
        trend_velocity = context.get("trend_velocity", 0)
        components.trend_velocity = min(float(trend_velocity or 0) * 2, 100)

        # cross_source: number of distinct sources that show similar products
        source_count = context.get("source_count", 1)
        components.cross_source = min(source_count * 25.0, 100)

        # competition_density: inverted — fewer similar products = higher score
        similar_count = context.get("similar_product_count", 5)
        components.competition_density = max(100 - similar_count * 5.0, 0)

        # novelty: how new is this product type in our tracking
        days_since_first_seen = context.get("days_since_first_seen", 1)
        if days_since_first_seen <= 7:
            components.novelty = 100.0
        elif days_since_first_seen <= 30:
            components.novelty = 70.0
        elif days_since_first_seen <= 90:
            components.novelty = 40.0
        else:
            components.novelty = 10.0

        # brand_fit: based on category + style match to brand profile
        brand_categories = context.get("brand_categories", [])
        brand_styles = context.get("brand_styles", [])
        product_category = product.get("category", "")
        product_style = product.get("style", "")

        fit_score = 50.0
        if product_category and any(c in product_category.lower() for c in brand_categories):
            fit_score += 25.0
        if product_style and any(s in product_style.lower() for s in brand_styles):
            fit_score += 25.0
        components.brand_fit = min(fit_score, 100)

        # review_signal: review count and rating combined
        review_count = product.get("review_count", 0) or 0
        review_rating = product.get("review_rating") or 3.0
        if review_count > 1000:
            review_score = 100.0
        elif review_count > 100:
            review_score = 70.0
        elif review_count > 10:
            review_score = 40.0
        else:
            review_score = 10.0
        rating_boost = (float(review_rating) - 3.0) * 15  # -30 to +30
        components.review_signal = min(max(review_score + rating_boost, 0), 100)

        total = self.compute_total(components)
        return total, components

    @classmethod
    async def score_new_products(cls, limit: int = 100) -> int:
        """Score all products with status='raw' or status='analyzed'. Returns count scored."""
        from database import get_db_context
        from models import Product, OpportunityScore
        from sqlalchemy import select
        from config import get_settings

        settings = get_settings()
        engine = cls()

        brand_context = {
            "brand_categories": [c.strip() for c in settings.brand_categories.split(",")],
            "brand_styles": [s.strip() for s in settings.brand_style_focus.split(",")],
        }

        scored_count = 0
        async with get_db_context() as db:
            result = await db.execute(
                select(Product)
                .where(Product.status.in_(["raw", "analyzed"]))
                .limit(limit)
            )
            products = result.scalars().all()

            for product in products:
                product_dict = {
                    "title": product.title,
                    "category": None,
                    "style": None,
                    "material": None,
                    "review_count": product.review_count,
                    "review_rating": product.review_rating,
                    "price_usd": product.price_usd,
                }

                if product.ai_attributes:
                    product_dict.update(product.ai_attributes)

                context = {
                    **brand_context,
                    "source_count": 1,
                    "similar_product_count": 5,
                    "days_since_first_seen": 3,
                    "trend_velocity": 30,
                }

                total, components = engine.score_product(product_dict, context)

                # Check if score already exists
                existing = await db.execute(
                    select(OpportunityScore).where(OpportunityScore.product_id == product.id)
                )
                existing_score = existing.scalar_one_or_none()

                if existing_score:
                    existing_score.total_score = total
                    existing_score.trend_velocity_score = components.trend_velocity
                    existing_score.cross_source_score = components.cross_source
                    existing_score.competition_density_score = components.competition_density
                    existing_score.novelty_score = components.novelty
                    existing_score.brand_fit_score = components.brand_fit
                    existing_score.review_signal_score = components.review_signal
                else:
                    db.add(OpportunityScore(
                        product_id=product.id,
                        total_score=total,
                        trend_velocity_score=components.trend_velocity,
                        cross_source_score=components.cross_source,
                        competition_density_score=components.competition_density,
                        novelty_score=components.novelty,
                        brand_fit_score=components.brand_fit,
                        review_signal_score=components.review_signal,
                        score_version="1.0",
                        score_breakdown=asdict(components),
                    ))

                product.status = "scored"
                scored_count += 1

            await db.commit()

        logger.info(f"Scored {scored_count} products")
        return scored_count
