#!/usr/bin/env python3
"""
Job: Run all enabled data connectors.
Schedule: every 6 hours via Railway Cron.
Run manually: python jobs/run_connectors.py [--connector mock_demo]
"""
import asyncio
import logging
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("job.run_connectors")

CONNECTOR_MAP = {
    "mock_demo": ("connectors.mock_demo", "MockDemoConnector"),
    "google_trends": ("connectors.google_trends", "GoogleTrendsConnector"),
    "etsy": ("connectors.etsy", "EtsyConnector"),
    "pinterest": ("connectors.pinterest", "PinterestConnector"),
    "manual_upload": ("connectors.manual_upload", "ManualUploadConnector"),
    "web_compliant": ("connectors.web_compliant", "WebCompliantConnector"),
}


async def get_enabled_connectors(only: str | None = None) -> list[str]:
    """Return enabled connector names from DB config, or all if DB not available."""
    if only:
        return [only]

    try:
        from database import get_db_context
        from models import ConnectorConfig
        from sqlalchemy import select
        async with get_db_context() as db:
            result = await db.execute(
                select(ConnectorConfig).where(ConnectorConfig.is_enabled == True)
            )
            return [cfg.name for cfg in result.scalars().all()]
    except Exception as e:
        logger.warning(f"Could not query DB for enabled connectors: {e}. Using env-based config.")
        from config import get_settings
        settings = get_settings()
        if settings.demo_mode:
            return ["mock_demo"]
        connectors = ["mock_demo", "google_trends", "etsy", "pinterest"]
        if settings.has_etsy:
            pass  # etsy already in list
        return connectors


async def log_run(connector_name: str, result) -> None:
    """Log connector run result to database."""
    try:
        from database import get_db_context
        from models import Source, SourceRun
        from sqlalchemy import select
        async with get_db_context() as db:
            src_result = await db.execute(select(Source).where(Source.name == connector_name))
            source = src_result.scalar_one_or_none()
            if source:
                run = SourceRun(
                    source_id=source.id,
                    status=result.status,
                    records_fetched=result.records_fetched,
                    records_saved=result.records_saved,
                    records_failed=result.records_failed,
                    error_message=result.error_message,
                    started_at=result.started_at,
                    finished_at=result.finished_at,
                    duration_seconds=result.duration_seconds,
                )
                db.add(run)
                await db.commit()
    except Exception as e:
        logger.warning(f"Could not log run for {connector_name}: {e}")


async def run_connector(name: str) -> bool:
    if name not in CONNECTOR_MAP:
        logger.error(f"Unknown connector: {name}")
        return False

    module_path, class_name = CONNECTOR_MAP[name]
    try:
        import importlib
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        connector = cls()
        logger.info(f"Running connector: {name}")
        result = await connector.run()
        await log_run(name, result)
        logger.info(
            f"[{name}] {result.status}: {result.records_saved}/{result.records_fetched} saved "
            f"in {result.duration_seconds:.1f}s"
        )
        return result.status == "success"
    except Exception as e:
        logger.error(f"Connector {name} crashed: {e}", exc_info=True)
        return False


async def main():
    parser = argparse.ArgumentParser(description="Run data connectors")
    parser.add_argument("--connector", help="Run specific connector only")
    parser.add_argument("--demo", action="store_true", help="Force demo mode (mock only)")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    if args.demo:
        os.environ["DEMO_MODE"] = "true"

    start = datetime.now(timezone.utc)
    logger.info(f"=== Connector Job Started at {start.isoformat()} ===")

    enabled = await get_enabled_connectors(only=args.connector)
    logger.info(f"Connectors to run: {enabled}")

    results = {}
    for name in enabled:
        results[name] = await run_connector(name)

    success_count = sum(1 for v in results.values() if v)
    logger.info(f"=== Connector Job Complete: {success_count}/{len(results)} succeeded ===")

    # Trigger scoring after ingestion
    if success_count > 0:
        logger.info("Triggering scoring job...")
        try:
            from services.scoring import ScoringEngine
            scored = await ScoringEngine.score_new_products(limit=200)
            logger.info(f"Scored {scored} products")
        except Exception as e:
            logger.error(f"Scoring failed: {e}")

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
