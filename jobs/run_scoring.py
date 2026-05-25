#!/usr/bin/env python3
"""
Job: Score unprocessed products and optionally run AI attribute extraction.
Schedule: after each connector run, or standalone every 6 hours.
Run manually: python jobs/run_scoring.py [--limit 100] [--ai]
"""
import asyncio
import logging
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("job.run_scoring")


async def run_ai_extraction(limit: int = 50) -> int:
    """Run AI attribute extraction on unanalyzed products."""
    from database import get_db_context
    from models import Product
    from sqlalchemy import select
    from config import get_settings

    settings = get_settings()
    if not settings.has_ai:
        logger.info("AI not configured — skipping attribute extraction")
        return 0

    from ai.tasks import extract_product_attributes
    import asyncio

    extracted = 0
    async with get_db_context() as db:
        result = await db.execute(
            select(Product)
            .where(Product.status == "raw")
            .where(Product.ai_analyzed_at.is_(None))
            .limit(limit)
        )
        products = result.scalars().all()

        for product in products:
            try:
                attrs, usage = await extract_product_attributes(
                    title=product.title,
                    description=product.description,
                )
                product.ai_attributes = attrs.model_dump()
                product.ai_analyzed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                product.ai_model_used = usage.get("model", settings.ai_model)
                product.status = "analyzed"
                extracted += 1
                await asyncio.sleep(0.5)  # Rate limit
            except Exception as e:
                logger.warning(f"AI extraction failed for product {product.id}: {e}")

        await db.commit()

    return extracted


async def main():
    parser = argparse.ArgumentParser(description="Score products and run AI extraction")
    parser.add_argument("--limit", type=int, default=100, help="Max products to process")
    parser.add_argument("--ai", action="store_true", help="Run AI attribute extraction first")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    logger.info("=== Scoring Job Started ===")

    if args.ai:
        logger.info("Running AI attribute extraction...")
        extracted = await run_ai_extraction(limit=args.limit)
        logger.info(f"AI extracted attributes for {extracted} products")

    logger.info("Scoring products...")
    from services.scoring import ScoringEngine
    scored = await ScoringEngine.score_new_products(limit=args.limit)
    logger.info(f"Scored {scored} products")

    logger.info("=== Scoring Job Complete ===")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
