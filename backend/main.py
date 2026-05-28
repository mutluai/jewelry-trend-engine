import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from api import products, trends, opportunities, reports, connectors, settings as settings_router, auth_etsy, assistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_settings = get_settings()


CONNECTOR_DEFAULTS = {
    "mock_demo":     {"display_name": "Mock / Demo",              "legal_status": "mock",           "is_enabled": True},
    "google_trends": {"display_name": "Google Trends",            "legal_status": "public_allowed", "is_enabled": True},
    "etsy":          {"display_name": "Etsy Open API v3",         "legal_status": "official_api",   "is_enabled": True},
    "ebay":          {"display_name": "eBay Browse API",          "legal_status": "official_api",   "is_enabled": True},
    "reddit_trends": {"display_name": "Reddit Sosyal Trendler",   "legal_status": "public_allowed", "is_enabled": True},
    "pinterest":     {"display_name": "Pinterest API v5 (STUB)",  "legal_status": "stub",           "is_enabled": True},
    "manual_upload": {"display_name": "Manual Upload",            "legal_status": "public_allowed", "is_enabled": True},
    "web_compliant": {"display_name": "Compliant Web Scraper",    "legal_status": "public_allowed", "is_enabled": False},
    "tiktok_trends": {"display_name": "TikTok Trendler",          "legal_status": "public_allowed", "is_enabled": True},
}


async def _ensure_connector_configs():
    from database import get_db_context
    from models import ConnectorConfig
    from sqlalchemy import select
    async with get_db_context() as db:
        for name, defaults in CONNECTOR_DEFAULTS.items():
            exists = (await db.execute(
                select(ConnectorConfig).where(ConnectorConfig.name == name)
            )).scalar_one_or_none()
            if not exists:
                db.add(ConnectorConfig(name=name, **defaults))
                logger.info(f"Created connector config: {name}")
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Jewelry Trend Engine — {app_settings.app_env}")
    logger.info(f"Demo mode: {app_settings.demo_mode}")
    logger.info(f"AI enabled: {app_settings.has_ai}")
    await _ensure_connector_configs()
    yield
    logger.info("Shutting down Jewelry Trend Engine")


app = FastAPI(
    title="Jewelry Trend Engine API",
    description="AI-powered jewelry product research and trend analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not app_settings.is_production else None,
    redoc_url="/redoc" if not app_settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api/v1", tags=["products"])
app.include_router(trends.router, prefix="/api/v1", tags=["trends"])
app.include_router(opportunities.router, prefix="/api/v1", tags=["opportunities"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(connectors.router, prefix="/api/v1", tags=["connectors"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["settings"])
app.include_router(auth_etsy.router, tags=["auth"])
app.include_router(assistant.router, prefix="/api/v1", tags=["assistant"])


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "env": app_settings.app_env,
        "demo_mode": app_settings.demo_mode,
        "ai_enabled": app_settings.has_ai,
        "db_configured": app_settings.has_database,
    }


@app.get("/")
async def root():
    return {"message": "Jewelry Trend Engine API", "docs": "/docs"}
