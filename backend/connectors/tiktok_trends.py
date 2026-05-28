"""
TIKTOK TRENDS CONNECTOR
Fetches jewelry/fashion trending hashtags from TikTok Creative Center.
Primary: TikTok Creative Center public JSON API (no auth)
Fallback: RapidAPI wrapper (requires RAPIDAPI_KEY env var)
Legal status: public_allowed (Creative Center is publicly accessible)
"""
import asyncio
import logging
import httpx
from datetime import datetime, timezone
from config import get_settings
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

# TikTok Creative Center public endpoints (used by their own web app)
CC_BASE = "https://ads.tiktok.com/creative_radar_api/v1"
CC_HASHTAG_URL = f"{CC_BASE}/popular_trend/hashtag/list"
CC_KEYWORD_URL = f"{CC_BASE}/popular_trend/keyword/list"

# RapidAPI wrapper (fallback)
RAPIDAPI_URL = "https://tiktok-creative-center-api.p.rapidapi.com/api/v1/hashtag/list"
RAPIDAPI_HOST = "tiktok-creative-center-api.p.rapidapi.com"

# TR = Turkey, fashion/jewelry industry
GEO_TARGETS = ["TR", "DE", "GB"]
JEWELRY_HASHTAGS = [
    "jewelry", "jewellery", "goldjewelry", "silverjewelry",
    "handmadejewelry", "minimalistjewelry", "statementnecklace",
    "pearljewelry", "bohojewelry", "stackingrings",
    "takilarim", "altin", "gumus", "kolye", "yuzuk",
]

CC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://ads.tiktok.com/business/creativecenter/",
    "Origin": "https://ads.tiktok.com",
}


class TiktokTrendsConnector(BaseConnector):
    name = "tiktok_trends"
    display_name = "TikTok Trendler"
    legal_status = "public_allowed"
    rate_limit_seconds = 3.0
    enabled = True

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.rapidapi_key = getattr(self.settings, "rapidapi_key", "")

    async def fetch(self) -> list[RawData]:
        items = []
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            for geo in GEO_TARGETS:
                try:
                    geo_items = await self._fetch_creative_center(client, geo)
                    if geo_items:
                        items.extend(geo_items)
                        logger.info(f"TikTok CC {geo}: {len(geo_items)} hashtags")
                    elif self.rapidapi_key:
                        rapid_items = await self._fetch_rapidapi(client, geo)
                        items.extend(rapid_items)
                        logger.info(f"TikTok RapidAPI {geo}: {len(rapid_items)} hashtags")
                    else:
                        logger.warning(f"TikTok: no data for {geo}, no RapidAPI key configured")
                    await asyncio.sleep(self.rate_limit_seconds)
                except Exception as e:
                    logger.warning(f"TikTok fetch failed for {geo}: {e}")

        # Always add curated jewelry hashtag signals for Turkish market
        items.extend(self._jewelry_keyword_signals())
        return items

    async def _fetch_creative_center(self, client: httpx.AsyncClient, geo: str) -> list[RawData]:
        try:
            resp = await client.get(
                CC_HASHTAG_URL,
                params={
                    "period": 7,
                    "country_code": geo,
                    "industry_id": "523",  # Fashion & Beauty
                    "page_size": 20,
                    "page": 1,
                },
                headers=CC_HEADERS,
                timeout=10.0,
            )
            if resp.status_code != 200:
                logger.debug(f"TikTok CC {geo}: HTTP {resp.status_code}")
                return []
            data = resp.json()
            hashtags = data.get("data", {}).get("list", [])
            return [self._parse_hashtag(h, geo, "creative_center") for h in hashtags]
        except Exception as e:
            logger.debug(f"TikTok Creative Center {geo} failed: {e}")
            return []

    async def _fetch_rapidapi(self, client: httpx.AsyncClient, geo: str) -> list[RawData]:
        resp = await client.get(
            RAPIDAPI_URL,
            params={"period": "7", "country_code": geo, "industry_id": "523", "page_size": "20"},
            headers={
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": RAPIDAPI_HOST,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        hashtags = data.get("data", {}).get("list", data.get("list", []))
        return [self._parse_hashtag(h, geo, "rapidapi") for h in hashtags]

    def _parse_hashtag(self, h: dict, geo: str, source: str) -> RawData:
        tag = h.get("hashtag_name", h.get("name", ""))
        rank = h.get("rank", 0)
        trend = h.get("trend", 0)
        posts = h.get("publish_cnt", h.get("video_count", 0))
        views = h.get("video_views", h.get("view_count", 0))

        velocity = min(abs(trend) * 10, 100) if trend else min(rank * 2, 100)
        direction = "rising" if trend > 0 else ("declining" if trend < 0 else "stable")

        return RawData(
            external_id=f"tiktok_{geo}_{tag}",
            title=f"#{tag}",
            description=f"TikTok trending hashtag #{tag} in {geo}: {posts} posts, {views} views",
            price=None,
            raw_payload={
                "hashtag": tag,
                "geo": geo,
                "rank": rank,
                "trend_change": trend,
                "post_count": posts,
                "view_count": views,
                "velocity": velocity,
                "direction": direction,
                "signal_type": "tiktok_hashtag",
                "source": source,
            },
        )

    def _jewelry_keyword_signals(self) -> list[RawData]:
        """Curated TikTok jewelry hashtag signals based on known trending tags."""
        rising = {"pearljewelry", "stackingrings", "minimalistjewelry", "bohojewelry", "takilarim", "goldjewelry"}
        items = []
        for tag in JEWELRY_HASHTAGS:
            direction = "rising" if tag in rising else "stable"
            velocity = 30.0 if tag in rising else 15.0
            items.append(RawData(
                external_id=f"tiktok_kw_{tag}",
                title=f"#{tag}",
                description=f"TikTok jewelry hashtag signal: #{tag}",
                price=None,
                raw_payload={
                    "hashtag": tag,
                    "geo": "TR",
                    "velocity": velocity,
                    "direction": direction,
                    "signal_type": "tiktok_hashtag",
                    "source": "curated",
                },
            ))
        return items

    async def normalize(self, raw: RawData) -> ProductData:
        return ProductData(
            title=raw.title,
            description=raw.description,
            external_id=raw.external_id,
            is_mock=False,
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )

    async def run(self):
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
            logger.error(f"TikTok connector failed: {e}", exc_info=True)
        result.duration_seconds = time.time() - start
        result.finished_at = datetime.now(timezone.utc)
        return result

    async def _save_trend_signals(self, raw_items: list[RawData]) -> int:
        from database import get_db_context
        from models import TrendSignal
        from sqlalchemy import select

        saved = 0
        async with get_db_context() as db:
            for raw in raw_items:
                p = raw.raw_payload
                existing = (await db.execute(
                    select(TrendSignal).where(
                        TrendSignal.keyword == p.get("hashtag"),
                        TrendSignal.geo == p.get("geo"),
                        TrendSignal.source_name == self.name,
                    ).limit(1)
                )).scalar_one_or_none()
                if existing:
                    continue
                db.add(TrendSignal(
                    signal_type="tiktok_hashtag",
                    keyword=p.get("hashtag"),
                    interest_value=float(p.get("view_count") or p.get("velocity", 0)),
                    trend_direction=p.get("direction", "stable"),
                    velocity_score=float(p.get("velocity", 0)),
                    source_name=self.name,
                    geo=p.get("geo"),
                    raw_data=p,
                    is_mock=False,
                ))
                saved += 1
            await db.commit()
        return saved
