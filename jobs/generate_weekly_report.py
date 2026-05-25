#!/usr/bin/env python3
"""
Job: Generate weekly trend report in Turkish and send notifications.
Schedule: every Monday at 09:00 UTC+3 (06:00 UTC) via Railway Cron.
Run manually: python jobs/generate_weekly_report.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("job.weekly_report")


async def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    logger.info("=== Weekly Report Job Started ===")

    try:
        from services.reporting import ReportingService
        result = await ReportingService.generate_and_send(
            report_type="weekly",
            send_email=True,
            send_slack=True,
        )
        logger.info(f"Weekly report complete: {result}")
        return 0
    except Exception as e:
        logger.error(f"Weekly report failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
