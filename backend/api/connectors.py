import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import ConnectorConfig, SourceRun
from schemas.connector import ConnectorStatusRead, ConnectorRunResponse

router = APIRouter()

CONNECTOR_REGISTRY = {
    "mock_demo": "connectors.mock_demo.MockDemoConnector",
    "google_trends": "connectors.google_trends.GoogleTrendsConnector",
    "etsy": "connectors.etsy.EtsyConnector",
    "pinterest": "connectors.pinterest.PinterestConnector",
    "manual_upload": "connectors.manual_upload.ManualUploadConnector",
    "web_compliant": "connectors.web_compliant.WebCompliantConnector",
}


@router.get("/connectors", response_model=list[ConnectorStatusRead])
async def list_connectors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConnectorConfig).order_by(ConnectorConfig.name))
    return list(result.scalars().all())


@router.post("/connectors/{connector_name}/run", response_model=ConnectorRunResponse)
async def run_connector(connector_name: str, db: AsyncSession = Depends(get_db)):
    if connector_name not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {connector_name}")

    module_path, class_name = CONNECTOR_REGISTRY[connector_name].rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    connector_class = getattr(module, class_name)
    connector = connector_class()

    start = time.time()
    try:
        result = await connector.run()
        duration = time.time() - start

        cfg_result = await db.execute(
            select(ConnectorConfig).where(ConnectorConfig.name == connector_name)
        )
        cfg = cfg_result.scalar_one_or_none()
        if cfg:
            from datetime import datetime, timezone
            cfg.last_run_at = datetime.now(timezone.utc).isoformat()
            cfg.last_run_status = result.status
            cfg.last_error = result.error_message
            await db.commit()

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
