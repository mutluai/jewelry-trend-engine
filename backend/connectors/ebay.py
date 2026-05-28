"""
EBAY BROWSE API CONNECTOR
Uses eBay Browse API v1 (official API) with OAuth2 Client Credentials.
No user authorization needed — app token is sufficient for public listing search.
Legal status: official_api
"""
import asyncio
import logging
from datetime import datetime, timezone
from config import get_settings
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

JEWELRY_QUERIES = [
    "gold ring women",
    "silver necklace handmade",
    "pearl earrings",
    "minimalist jewelry",
    "boho jewelry",
    "stackable rings",
    "evil eye jewelry",
    "rose gold bracelet",
]


class EbayConnector(BaseConnector):
    name = "ebay"
    display_name = "eBay Browse API"
    legal_status = "official_api"
    rate_limit_seconds = 1.0
    enabled = True

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.app_id = self.settings.ebay_app_id
        self.cert_id = self.settings.ebay_cert_id
        self.is_stub = not (self.app_id and self.cert_id)
        if self.is_stub:
            logger.warning("eBay credentials not configured — running in STUB mode")

    async def _get_token(self) -> str:
        import httpx, base64
        credentials = base64.b64encode(f"{self.app_id}:{self.cert_id}".encode()).decode()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                EBAY_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def fetch(self) -> list[RawData]:
        if self.is_stub:
            return self._stub_data()

        import httpx
        try:
            token = await self._get_token()
        except Exception as e:
            logger.error(f"eBay token fetch failed: {e}")
            return self._stub_data()

        items = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in JEWELRY_QUERIES[:5]:
                try:
                    resp = await client.get(
                        EBAY_BROWSE_URL,
                        params={
                            "q": query,
                            "category_ids": "281",  # Jewelry & Watches
                            "limit": 20,
                            "sort": "bestMatch",
                        },
                        headers={
                            "Authorization": f"Bearer {token}",
                            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    results = data.get("itemSummaries", [])
                    logger.info(f"eBay '{query}': {len(results)} items")
                    for item in results:
                        items.append(self._parse_item(item))
                    await asyncio.sleep(self.rate_limit_seconds)
                except Exception as e:
                    logger.error(f"eBay fetch failed for '{query}': {e}")

        return items

    def _parse_item(self, item: dict) -> RawData:
        price_data = item.get("price", {})
        try:
            price = float(price_data.get("value", 0))
        except (ValueError, TypeError):
            price = None

        image = item.get("image", {})
        return RawData(
            external_id=item.get("itemId", ""),
            title=item.get("title", ""),
            description=item.get("shortDescription"),
            source_url=item.get("itemWebUrl"),
            image_url=image.get("imageUrl") if image else None,
            price=price,
            currency=price_data.get("currency", "USD"),
            price_usd=price if price_data.get("currency") == "USD" else None,
            review_count=item.get("feedbackScore"),
            raw_payload={"source": "ebay", "condition": item.get("condition"), "seller": item.get("seller", {}).get("username")},
        )

    def _stub_data(self) -> list[RawData]:
        return [
            RawData(
                external_id=f"ebay-stub-{i}",
                title=f"[STUB] eBay Jewelry Item {i}",
                description="Stub data — configure EBAY_APP_ID and EBAY_CERT_ID",
                price=round(20 + i * 18, 2),
                currency="USD",
                price_usd=round(20 + i * 18, 2),
                review_count=i * 15,
                raw_payload={"source": "ebay_stub", "is_stub": True},
            )
            for i in range(1, 6)
        ]

    async def normalize(self, raw: RawData) -> ProductData:
        is_stub = raw.raw_payload.get("is_stub", False)
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
            target_gender="women",
            price_tier=self.infer_price_tier(raw.price_usd),
            is_mock=is_stub,
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )
