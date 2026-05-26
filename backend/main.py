import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from api import products, trends, opportunities, reports, connectors, settings as settings_router, auth_etsy, assistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Jewelry Trend Engine — {app_settings.app_env}")
    logger.info(f"Demo mode: {app_settings.demo_mode}")
    logger.info(f"AI enabled: {app_settings.has_ai}")
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
