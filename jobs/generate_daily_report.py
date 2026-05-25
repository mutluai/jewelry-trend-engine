#!/usr/bin/env python3
"""
Job: Generate daily summary report in Turkish and send notifications.
Schedule: every day at 08:00 UTC+3 (05:00 UTC) via Railway Cron.
Run manually: python jobs/generate_daily_report.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("job.daily_report")


async def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    logger.info("=== Daily Report Job Started ===")

    try:
        from services.reporting import ReportingService
        result = await ReportingService.generate_and_send(
            report_type="daily",
            send_email=True,
            send_slack=True,
        )
        logger.info(f"Daily report complete: {result}")
        return 0
    except Exception as e:
        logger.error(f"Daily report failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
