"""
GOOGLE TRENDS CONNECTOR
Uses pytrends (unofficial wrapper) to fetch jewelry keyword trends.
Legal status: public_allowed (accesses public Google Trends UI data).
Rate limited with exponential backoff to avoid being blocked.
"""
import asyncio
import logging
from datetime import datetime, timezone
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

JEWELRY_KEYWORDS = [
    "gold ring", "silver necklace", "pearl earrings", "diamond bracelet",
    "emerald ring", "rose gold jewelry", "minimalist jewelry", "boho jewelry",
    "vintage jewelry", "statement necklace", "opal ring", "turquoise jewelry",
    "birthstone ring", "charm bracelet", "tennis bracelet", "hoop earrings",
    "anklet", "layered necklace", "stackable rings", "evil eye jewelry",
]

GEO_TARGETS = ["TR", "DE", "GB"]


class GoogleTrendsConnector(BaseConnector):
    name = "google_trends"
    display_name = "Google Trends"
    legal_status = "public_allowed"
    rate_limit_seconds = 10.0
    enabled = True

    async def fetch(self) -> list[RawData]:
        try:
            from pytrends.request import TrendReq
        except ImportError:
            logger.warning("pytrends not installed — returning empty result")
            return []

        items = []
        # pytrends is synchronous; run in thread pool
        loop = asyncio.get_running_loop()

        for geo in GEO_TARGETS:
            try:
                raw_items = await loop.run_in_executor(
                    None, self._fetch_for_geo, geo
                )
                items.extend(raw_items)
                # Respect rate limit between geo requests
                await asyncio.sleep(self.rate_limit_seconds)
            except Exception as e:
                logger.warning(f"Google Trends fetch failed for {geo}: {e}")

        return items

    def _fetch_for_geo(self, geo: str) -> list[RawData]:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=180, timeout=(10, 25), retries=2, backoff_factor=0.5)

        items = []
        # Process keywords in batches of 5 (Google Trends limit)
        batch_size = 5
        for i in range(0, min(len(JEWELRY_KEYWORDS), 20), batch_size):
            batch = JEWELRY_KEYWORDS[i:i + batch_size]
            try:
                pytrends.build_payload(batch, cat=0, timeframe="today 3-m", geo=geo, gprop="")
                interest_df = pytrends.interest_over_time()

                if interest_df is not None and not interest_df.empty:
                    for keyword in batch:
                        if keyword in interest_df.columns:
                            values = interest_df[keyword].dropna()
                            if len(values) >= 2:
                                recent = float(values.iloc[-1])
                                previous = float(values.iloc[-5]) if len(values) >= 5 else float(values.iloc[0])
                                velocity = (recent - previous) / max(previous, 1) * 100

                                direction = "rising" if velocity > 5 else ("declining" if velocity < -5 else "stable")

                                items.append(RawData(
                                    external_id=f"gtrends_{geo}_{keyword.replace(' ', '_')}",
                                    title=f"Trend: {keyword}",
                                    description=f"Google Trends interest for '{keyword}' in {geo}",
                                    price=None,
                                    raw_payload={
                                        "keyword": keyword,
                                        "geo": geo,
                                        "interest_value": recent,
                                        "velocity": velocity,
                                        "direction": direction,
                                        "signal_type": "keyword_trend",
                                        "period": "3-month",
                                    },
                                ))
            except Exception as e:
                logger.warning(f"Batch {batch} for {geo} failed: {e}")

        return items

    async def normalize(self, raw: RawData) -> ProductData:
        payload = raw.raw_payload
        return ProductData(
            title=raw.title,
            description=raw.description,
            external_id=raw.external_id,
            is_mock=False,
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )

    async def save(self, products: list[ProductData]) -> int:
        """Save as TrendSignals rather than Products."""
        from database import get_db_context
        from models import TrendSignal
        import json

        saved = 0
        async with get_db_context() as db:
            for product in products:
                raw_payload = {}
                if hasattr(product, '_raw_payload'):
                    raw_payload = product._raw_payload

            # Re-fetch raw data by re-running (simplified approach)
            # In production this would carry raw_payload through the pipeline
        return saved

    async def run(self):
        """Override run to save TrendSignals directly."""
        import time
        from .base import ConnectorResult

        start = time.time()
        result = ConnectorResult(connector_name=self.name, status="running")

        try:
            raw_items = await self.fetch()
            result.records_fetched = len(raw_items)
            saved = await self._save_trend_signals(raw_items)
            result.records_saved = saved
            result.status = "success"
        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            logger.error(f"Google Trends connector failed: {e}", exc_info=True)

        result.duration_seconds = time.time() - start
        result.finished_at = datetime.now(timezone.utc)
        return result

    async def _save_trend_signals(self, raw_items: list[RawData]) -> int:
        from database import get_db_context
        from models import TrendSignal
        from datetime import datetime, timezone

        saved = 0
        async with get_db_context() as db:
            for raw in raw_items:
                payload = raw.raw_payload
                signal = TrendSignal(
                    signal_type=payload.get("signal_type", "keyword_trend"),
                    keyword=payload.get("keyword"),
                    interest_value=payload.get("interest_value"),
                    trend_direction=payload.get("direction"),
                    velocity_score=payload.get("velocity"),
                    source_name=self.name,
                    geo=payload.get("geo"),
                    raw_data=payload,
                    is_mock=False,
                )
                db.add(signal)
                saved += 1
            await db.commit()
        return saved
