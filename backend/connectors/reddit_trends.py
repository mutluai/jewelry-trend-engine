"""
REDDIT TRENDS CONNECTOR
Monitors jewelry subreddits via Reddit's public JSON API.
No authentication required for public subreddits.
Legal status: public_allowed (Reddit API Terms allow read access to public posts)
"""
import asyncio
import logging
import httpx
from datetime import datetime, timezone
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

JEWELRY_SUBREDDITS = [
    "jewelry",
    "jewelrymaking",
    "GEMS",
    "Watches",
    "WeddingRings",
    "Silverbugs",
]

REDDIT_API = "https://www.reddit.com/r/{subreddit}/{sort}.json"
HEADERS = {"User-Agent": "JewelryTrendEngine/1.0 (research-bot; +https://github.com/mutluai/jewelry-trend-engine)"}


class RedditTrendsConnector(BaseConnector):
    name = "reddit_trends"
    display_name = "Reddit Sosyal Trendler"
    legal_status = "public_allowed"
    rate_limit_seconds = 2.0
    enabled = True

    async def fetch(self) -> list[RawData]:
        items = []
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            for subreddit in JEWELRY_SUBREDDITS:
                for sort in ["hot", "top"]:
                    try:
                        resp = await client.get(
                            REDDIT_API.format(subreddit=subreddit, sort=sort),
                            params={"limit": 25, "t": "week"},
                        )
                        if resp.status_code != 200:
                            logger.warning(f"Reddit r/{subreddit}/{sort}: HTTP {resp.status_code}")
                            continue
                        data = resp.json()
                        posts = data.get("data", {}).get("children", [])
                        logger.info(f"Reddit r/{subreddit}/{sort}: {len(posts)} posts")

                        for post in posts:
                            p = post.get("data", {})
                            score = p.get("score", 0)
                            if score < 5:
                                continue
                            items.append(RawData(
                                external_id=f"reddit_{p.get('id', '')}",
                                title=p.get("title", ""),
                                description=p.get("selftext", "")[:500] or None,
                                source_url=f"https://reddit.com{p.get('permalink', '')}",
                                image_url=p.get("url") if p.get("url", "").endswith((".jpg", ".jpeg", ".png", ".webp")) else None,
                                price=None,
                                raw_payload={
                                    "subreddit": subreddit,
                                    "score": score,
                                    "num_comments": p.get("num_comments", 0),
                                    "upvote_ratio": p.get("upvote_ratio", 0),
                                    "flair": p.get("link_flair_text"),
                                    "signal_type": "social_trend",
                                    "sort": sort,
                                },
                            ))
                        await asyncio.sleep(self.rate_limit_seconds)
                    except Exception as e:
                        logger.warning(f"Reddit r/{subreddit}/{sort} failed: {e}")
        return items

    async def normalize(self, raw: RawData) -> ProductData:
        return ProductData(
            title=raw.title,
            description=raw.description,
            source_url=raw.source_url,
            image_url=raw.image_url,
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
            logger.error(f"Reddit connector failed: {e}", exc_info=True)

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
                payload = raw.raw_payload
                existing = (await db.execute(
                    select(TrendSignal).where(
                        TrendSignal.keyword == raw.external_id,
                        TrendSignal.source_name == self.name,
                    ).limit(1)
                )).scalar_one_or_none()
                if existing:
                    continue

                score = payload.get("score", 0)
                velocity = min(score / 10, 100)
                direction = "rising" if payload.get("upvote_ratio", 0) > 0.85 else "stable"

                db.add(TrendSignal(
                    signal_type="social_trend",
                    keyword=raw.title[:255],
                    interest_value=float(score),
                    trend_direction=direction,
                    velocity_score=velocity,
                    source_name=self.name,
                    geo=None,
                    raw_data=payload,
                    is_mock=False,
                ))
                saved += 1
            await db.commit()
        return saved
