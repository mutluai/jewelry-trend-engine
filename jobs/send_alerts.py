#!/usr/bin/env python3
"""
Job: Check alert thresholds and send notifications.
Schedule: every 6 hours via Railway Cron (after connector runs).
Run manually: python jobs/send_alerts.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("job.send_alerts")


async def check_high_opportunity_alerts() -> list[dict]:
    """Find products with score >= threshold that haven't been alerted yet."""
    from database import get_db_context
    from models import OpportunityScore, Product, AppSetting
    from sqlalchemy import select

    alerts = []
    async with get_db_context() as db:
        threshold_setting = (await db.execute(
            select(AppSetting).where(AppSetting.key == "alert_score_threshold")
        )).scalar_one_or_none()

        threshold = float(threshold_setting.value) if threshold_setting else 75.0

        result = await db.execute(
            select(OpportunityScore, Product)
            .join(Product, OpportunityScore.product_id == Product.id)
            .where(OpportunityScore.total_score >= threshold)
            .order_by(OpportunityScore.total_score.desc())
            .limit(5)
        )
        for score, product in result.all():
            alerts.append({
                "title": f"Yüksek Fırsat: {product.title}",
                "message": f"Skor: {score.total_score:.1f}/100 — {product.title}",
                "score": score.total_score,
                "product_title": product.title,
            })

    return alerts


async def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    logger.info("=== Alert Job Started ===")

    alerts = await check_high_opportunity_alerts()
    logger.info(f"Found {len(alerts)} high-opportunity alerts")

    if alerts:
        from services.alerts import AlertService
        alert_service = AlertService()

        top = alerts[0]
        message = f"🏆 *En Yüksek Fırsat*\n{top['message']}"
        if len(alerts) > 1:
            message += f"\n+{len(alerts)-1} daha"

        await alert_service.send_slack(message)
        logger.info(f"Sent alert for {len(alerts)} high-opportunity products")

    logger.info("=== Alert Job Complete ===")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
