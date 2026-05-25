"""
COMPLIANT WEB CONNECTOR
Fetches public product pages that allow scraping per their robots.txt.
Mandatory robots.txt check before every domain.
Rate limit: minimum 3 seconds between requests per domain.
Never bypasses CAPTCHAs or authentication walls.
"""
import asyncio
import logging
import time
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime, timezone
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

USER_AGENT = "JewelryTrendEngine/1.0 (+https://github.com/mutluai/jewelry-trend-engine; research-bot)"
MIN_DELAY_SECONDS = 3.0


class WebCompliantConnector(BaseConnector):
    name = "web_compliant"
    display_name = "Compliant Web Scraper"
    legal_status = "public_allowed"
    rate_limit_seconds = 3.0
    enabled = True

    def __init__(self, urls: list[str] | None = None):
        super().__init__()
        self._robots_cache: dict[str, tuple[RobotFileParser, float]] = {}
        self._last_request: dict[str, float] = {}
        self.target_urls = urls or []

    async def _get_robots(self, domain: str) -> RobotFileParser | None:
        """Fetch and cache robots.txt for a domain. Cache TTL: 24 hours."""
        cached = self._robots_cache.get(domain)
        if cached:
            parser, fetched_at = cached
            if time.time() - fetched_at < 86400:
                return parser

        import httpx
        robots_url = f"https://{domain}/robots.txt"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(robots_url, headers={"User-Agent": USER_AGENT})
                parser = RobotFileParser()
                parser.set_url(robots_url)
                parser.parse(resp.text.splitlines())
                self._robots_cache[domain] = (parser, time.time())
                return parser
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt for {domain}: {e}")
            return None

    async def _can_fetch(self, url: str) -> bool:
        """Returns True only if robots.txt allows our user-agent to fetch this URL."""
        parsed = urlparse(url)
        domain = parsed.netloc
        robots = await self._get_robots(domain)

        if robots is None:
            # If robots.txt is unreachable, be conservative and skip
            logger.warning(f"Cannot verify robots.txt for {domain} — skipping {url}")
            return False

        allowed = robots.can_fetch(USER_AGENT, url)
        if not allowed:
            logger.info(f"robots.txt disallows: {url}")
        return allowed

    async def _rate_limit(self, domain: str):
        """Enforce minimum delay between requests to same domain."""
        last = self._last_request.get(domain, 0)
        elapsed = time.time() - last
        if elapsed < MIN_DELAY_SECONDS:
            await asyncio.sleep(MIN_DELAY_SECONDS - elapsed)
        self._last_request[domain] = time.time()

    async def _fetch_url(self, url: str) -> RawData | None:
        """Fetch a single URL, respecting robots.txt and rate limits."""
        if not await self._can_fetch(url):
            return None

        parsed = urlparse(url)
        domain = parsed.netloc
        await self._rate_limit(domain)

        import httpx
        from bs4 import BeautifulSoup

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": USER_AGENT})
                if resp.status_code != 200:
                    logger.warning(f"HTTP {resp.status_code} for {url}")
                    return None
                # Never bypass auth — if we land on a login page, skip
                if "login" in resp.url.path.lower() or "signin" in resp.url.path.lower():
                    logger.warning(f"Redirected to login page — skipping {url}")
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")
                return self._extract_product(url, soup)
        except Exception as e:
            logger.warning(f"Fetch failed for {url}: {e}")
            return None

    def _extract_product(self, url: str, soup) -> RawData | None:
        """Extract product data from HTML using common patterns."""
        title = None
        for selector in ["h1.product-title", "h1[itemprop='name']", "h1", ".product-name"]:
            el = soup.select_one(selector)
            if el:
                title = el.get_text(strip=True)
                break

        if not title:
            return None

        description = None
        for selector in [".product-description", "[itemprop='description']", ".description"]:
            el = soup.select_one(selector)
            if el:
                description = el.get_text(strip=True)[:2000]
                break

        price = None
        for selector in ["[itemprop='price']", ".price", ".product-price"]:
            el = soup.select_one(selector)
            if el:
                price_text = el.get("content") or el.get_text(strip=True)
                try:
                    price = float("".join(c for c in price_text if c.isdigit() or c == "."))
                except ValueError:
                    pass
                break

        image_url = None
        for selector in ["[itemprop='image']", ".product-image img", ".main-image img"]:
            el = soup.select_one(selector)
            if el:
                image_url = el.get("src") or el.get("content")
                if image_url and not image_url.startswith("http"):
                    image_url = urljoin(url, image_url)
                break

        return RawData(
            external_id=None,
            title=title,
            description=description,
            source_url=url,
            image_url=image_url,
            price=price,
            currency="USD",
            price_usd=price,
            raw_payload={"source": "web_compliant", "domain": urlparse(url).netloc},
        )

    async def fetch(self) -> list[RawData]:
        if not self.target_urls:
            logger.info("No target URLs configured for web_compliant connector")
            return []

        items = []
        for url in self.target_urls:
            raw = await self._fetch_url(url)
            if raw:
                items.append(raw)

        return items

    async def normalize(self, raw: RawData) -> ProductData:
        return ProductData(
            title=raw.title,
            description=raw.description,
            source_url=raw.source_url,
            image_url=raw.image_url,
            price=raw.price,
            currency=raw.currency,
            price_usd=raw.price_usd,
            review_count=raw.review_count,
            external_id=raw.external_id,
            price_tier=self.infer_price_tier(raw.price_usd),
            is_mock=False,
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )
