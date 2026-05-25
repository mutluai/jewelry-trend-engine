"""
Reporting Service — generates daily/weekly reports using AI and sends notifications.
"""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class ReportingService:

    @classmethod
    async def generate_and_send(
        cls,
        report_type: str = "daily",
        send_email: bool = True,
        send_slack: bool = True,
    ) -> dict:
        logger.info(f"Generating {report_type} report...")

        # 1. Gather data summary
        stats = await cls._gather_stats(report_type)

        # 2. Generate report text via AI
        from ai.tasks import generate_report
        from config import get_settings
        settings = get_settings()

        content, usage = await generate_report(
            report_type=report_type,
            data_summary=stats,
            language=settings.report_language,
        )

        # 3. Store report in database
        from database import get_db_context
        from models import Report
        from services.storage import StorageService

        storage = StorageService()
        filename = storage.generate_report_filename(report_type)
        storage_url = await storage.upload_report(content, filename)

        email_sent = False
        slack_sent = False

        async with get_db_context() as db:
            report = Report(
                report_type=report_type,
                title=cls._report_title(report_type),
                language=settings.report_language,
                content_markdown=content,
                storage_path=f"reports/{filename}",
                storage_url=storage_url,
                period_start=stats.get("period_start"),
                period_end=stats.get("period_end"),
                product_count=stats.get("total_products", 0),
                signal_count=stats.get("new_signals", 0),
                ai_model_used=usage.get("model", settings.ai_model),
                ai_tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            )

            # 4. Send notifications
            if send_email or send_slack:
                from services.alerts import AlertService
                alert_service = AlertService()
                email_sent, slack_sent = await alert_service.send_report_notification(
                    report_type=report_type,
                    report_content=content,
                    report_url=storage_url,
                    stats=stats,
                )

            report.email_sent = email_sent
            report.slack_sent = slack_sent
            db.add(report)
            await db.commit()

            logger.info(f"Report saved. Email: {email_sent}, Slack: {slack_sent}")
            return {
                "status": "success",
                "report_type": report_type,
                "storage_url": storage_url,
                "email_sent": email_sent,
                "slack_sent": slack_sent,
                "tokens_used": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            }

    @classmethod
    async def _gather_stats(cls, report_type: str) -> dict:
        from database import get_db_context
        from models import Product, OpportunityScore, TrendSignal
        from sqlalchemy import select, func

        now = datetime.now(timezone.utc)
        if report_type == "daily":
            period_start = (now - timedelta(days=1)).isoformat()
        else:
            period_start = (now - timedelta(days=7)).isoformat()

        async with get_db_context() as db:
            total_products = (await db.execute(select(func.count(Product.id)))).scalar_one()
            new_signals = (await db.execute(select(func.count(TrendSignal.id)))).scalar_one()

            top_score_row = (await db.execute(
                select(OpportunityScore).order_by(OpportunityScore.total_score.desc()).limit(1)
            )).scalar_one_or_none()

            top_score = f"{top_score_row.total_score:.1f}/100" if top_score_row else "N/A"

        return {
            "period": "Son 24 saat" if report_type == "daily" else "Son 7 gün",
            "period_start": period_start,
            "period_end": now.isoformat(),
            "total_products": total_products,
            "new_signals": new_signals,
            "top_opportunity": top_score,
            "top_score": top_score,
            "rising_materials": ["altın kaplama", "gümüş", "rose gold"],
            "rising_styles": ["minimalist", "vintage", "celestial"],
        }

    @classmethod
    def _report_title(cls, report_type: str) -> str:
        titles = {
            "daily": "Günlük Trend Özeti",
            "weekly": "Haftalık Trend Raporu",
            "opportunity": "Fırsat Listesi",
            "competitor": "Rakip Hareket Raporu",
        }
        from datetime import date
        return f"{titles.get(report_type, 'Rapor')} — {date.today().strftime('%d.%m.%Y')}"
