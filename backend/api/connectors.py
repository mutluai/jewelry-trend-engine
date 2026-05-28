import time
import importlib
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, get_db_context
from models import ConnectorConfig
from schemas.connector import ConnectorStatusRead, ConnectorRunResponse

router = APIRouter()
logger = logging.getLogger(__name__)

CONNECTOR_REGISTRY = {
    "mock_demo": "connectors.mock_demo.MockDemoConnector",
    "google_trends": "connectors.google_trends.GoogleTrendsConnector",
    "reddit_trends": "connectors.reddit_trends.RedditTrendsConnector",
    "etsy": "connectors.etsy.EtsyConnector",
    "ebay": "connectors.ebay.EbayConnector",
    "pinterest": "connectors.pinterest.PinterestConnector",
    "manual_upload": "connectors.manual_upload.ManualUploadConnector",
    "web_compliant": "connectors.web_compliant.WebCompliantConnector",
    "tiktok_trends": "connectors.tiktok_trends.TiktokTrendsConnector",
}

BACKGROUND_CONNECTORS = {"google_trends", "reddit_trends", "tiktok_trends"}


def _load_connector(connector_name: str):
    module_path, class_name = CONNECTOR_REGISTRY[connector_name].rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


async def _update_connector_status(connector_name: str, status: str, error: str | None = None):
    async with get_db_context() as db:
        cfg_result = await db.execute(
            select(ConnectorConfig).where(ConnectorConfig.name == connector_name)
        )
        cfg = cfg_result.scalar_one_or_none()
        if cfg:
            cfg.last_run_at = datetime.now(timezone.utc).isoformat()
            cfg.last_run_status = status
            cfg.last_error = error
            await db.commit()


async def _run_connector_background(connector_name: str):
    try:
        connector = _load_connector(connector_name)
        result = await connector.run()
        await _update_connector_status(connector_name, result.status, result.error_message)
        logger.info(f"{connector_name}: {result.status}, saved={result.records_saved}")
    except Exception as e:
        logger.error(f"{connector_name} background run failed: {e}", exc_info=True)
        await _update_connector_status(connector_name, "failed", str(e))


@router.get("/connectors", response_model=list[ConnectorStatusRead])
async def list_connectors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConnectorConfig).order_by(ConnectorConfig.name))
    return list(result.scalars().all())


@router.post("/connectors/{connector_name}/run", response_model=ConnectorRunResponse)
async def run_connector(
    connector_name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if connector_name not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {connector_name}")

    connector = _load_connector(connector_name)

    if connector_name in BACKGROUND_CONNECTORS:
        background_tasks.add_task(_run_connector_background, connector_name)
        await _update_connector_status(connector_name, "running")
        return ConnectorRunResponse(
            connector_name=connector_name,
            status="running",
            records_fetched=0,
            records_saved=0,
            error=None,
            duration_seconds=0.0,
        )

    start = time.time()
    try:
        result = await connector.run()
        duration = time.time() - start
        await _update_connector_status(connector_name, result.status, result.error_message)
        return ConnectorRunResponse(
            connector_name=connector_name,
            status=result.status,
            records_fetched=result.records_fetched,
            records_saved=result.records_saved,
            error=result.error_message,
            duration_seconds=duration,
        )
    except Exception as e:
        duration = time.time() - start
        await _update_connector_status(connector_name, "failed", str(e))
        return ConnectorRunResponse(
            connector_name=connector_name,
            status="failed",
            records_fetched=0,
            records_saved=0,
            error=str(e),
            duration_seconds=duration,
        )


@router.patch("/connectors/{connector_name}/toggle")
async def toggle_connector(connector_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ConnectorConfig).where(ConnectorConfig.name == connector_name)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Connector not found")
    cfg.is_enabled = not cfg.is_enabled
    await db.commit()
    return {"name": connector_name, "is_enabled": cfg.is_enabled}
