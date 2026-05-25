import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class RawData:
    external_id: str | None
    title: str
    description: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    price: float | None = None
    currency: str | None = None
    price_usd: float | None = None
    review_count: int = 0
    review_rating: float | None = None
    sales_count: int = 0
    favorites_count: int = 0
    raw_payload: dict = field(default_factory=dict)


@dataclass
class ProductData:
    title: str
    description: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    price: float | None = None
    currency: str | None = None
    price_usd: float | None = None
    review_count: int = 0
    review_rating: float | None = None
    sales_count: int = 0
    favorites_count: int = 0
    external_id: str | None = None
    target_gender: str | None = None
    price_tier: str | None = None
    theme: str | None = None
    is_mock: bool = False
    source_name: str = ""
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConnectorResult:
    connector_name: str
    status: str
    records_fetched: int = 0
    records_saved: int = 0
    records_failed: int = 0
    error_message: str | None = None
    duration_seconds: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None


class BaseConnector(ABC):
    name: str = "base"
    display_name: str = "Base Connector"
    legal_status: Literal["official_api", "public_allowed", "stub", "mock"] = "stub"
    rate_limit_seconds: float = 3.0
    enabled: bool = True

    def __init__(self):
        self.logger = logging.getLogger(f"connector.{self.name}")

    @abstractmethod
    async def fetch(self) -> list[RawData]:
        """Fetch raw data from source. Must respect rate limits."""
        ...

    @abstractmethod
    async def normalize(self, raw: RawData) -> ProductData:
        """Convert raw data to normalized ProductData."""
        ...

    def validate(self, product: ProductData) -> bool:
        """Check product data completeness. Override for stricter validation."""
        return bool(product.title and len(product.title.strip()) > 2)

    def infer_price_tier(self, price_usd: float | None) -> str | None:
        if price_usd is None:
            return None
        if price_usd < 30:
            return "budget"
        if price_usd < 80:
            return "mid"
        if price_usd < 150:
            return "premium"
        return "luxury"

    async def save(self, products: list[ProductData]) -> int:
        """Save normalized products to database. Returns count saved."""
        from database import get_db_context
        from models import Product, Source
        from sqlalchemy import select

        saved = 0
        async with get_db_context() as db:
            source_result = await db.execute(select(Source).where(Source.name == self.name))
            source = source_result.scalar_one_or_none()

            for product in products:
                try:
                    db_product = Product(
                        title=product.title,
                        description=product.description,
                        source_url=product.source_url,
                        image_url=product.image_url,
                        price=product.price,
                        currency=product.currency,
                        price_usd=product.price_usd,
                        review_count=product.review_count,
                        review_rating=product.review_rating,
                        sales_count=product.sales_count,
                        favorites_count=product.favorites_count,
                        external_id=product.external_id,
                        target_gender=product.target_gender,
                        price_tier=product.price_tier,
                        theme=product.theme,
                        is_mock=product.is_mock,
                        collected_at=product.collected_at,
                        status="raw",
                        source_id=source.id if source else None,
                    )
                    db.add(db_product)
                    saved += 1
                except Exception as e:
                    self.logger.error(f"Failed to save product '{product.title}': {e}")

            await db.commit()
        return saved

    async def run(self) -> ConnectorResult:
        import time
        start = time.time()
        result = ConnectorResult(connector_name=self.name, status="running")

        try:
            self.logger.info(f"Starting connector: {self.name}")
            raw_items = await self.fetch()
            result.records_fetched = len(raw_items)
            self.logger.info(f"Fetched {len(raw_items)} items from {self.name}")

            valid_products = []
            for raw in raw_items:
                try:
                    product = await self.normalize(raw)
                    if self.validate(product):
                        valid_products.append(product)
                    else:
                        result.records_failed += 1
                except Exception as e:
                    self.logger.warning(f"Normalize error: {e}")
                    result.records_failed += 1

            if valid_products:
                result.records_saved = await self.save(valid_products)

            result.status = "success"
            self.logger.info(f"Connector {self.name} complete: {result.records_saved} saved")

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            self.logger.error(f"Connector {self.name} failed: {e}", exc_info=True)

        result.duration_seconds = time.time() - start
        result.finished_at = datetime.now(timezone.utc)
        return result
