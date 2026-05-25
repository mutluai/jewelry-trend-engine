"""
ETSY CONNECTOR
Uses Etsy Open API v3 (official API).
Requires ETSY_API_KEY environment variable.
Falls back to stub mode if key is not configured.
Legal status: official_api
"""
import asyncio
import logging
from datetime import datetime, timezone
from config import get_settings
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"
JEWELRY_TAXONOMY_IDS = [
    68887144,  # Jewelry > Rings
    68887145,  # Jewelry > Necklaces
    68887146,  # Jewelry > Bracelets
    68887147,  # Jewelry > Earrings
    68887148,  # Jewelry > Body Jewelry
]


class EtsyConnector(BaseConnector):
    name = "etsy"
    display_name = "Etsy Open API v3"
    legal_status = "official_api"
    rate_limit_seconds = 1.0
    enabled = True

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.api_key = self.settings.etsy_api_key
        self.is_stub = not bool(self.api_key)
        if self.is_stub:
            logger.warning("Etsy API key not configured — running in STUB mode")

    async def fetch(self) -> list[RawData]:
        if self.is_stub:
            return self._stub_data()

        import httpx
        items = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for taxonomy_id in JEWELRY_TAXONOMY_IDS[:3]:
                try:
                    response = await client.get(
                        f"{ETSY_API_BASE}/application/listings/active",
                        params={
                            "taxonomy_id": taxonomy_id,
                            "limit": 50,
                            "sort_on": "score",
                            "sort_order": "desc",
                        },
                        headers={"x-api-key": self.api_key},
                    )
                    response.raise_for_status()
                    data = response.json()

                    for listing in data.get("results", []):
                        items.append(self._parse_listing(listing))

                    await asyncio.sleep(self.rate_limit_seconds)

                except Exception as e:
                    logger.warning(f"Etsy fetch failed for taxonomy {taxonomy_id}: {e}")

        return items

    def _parse_listing(self, listing: dict) -> RawData:
        images = listing.get("images", [])
        image_url = images[0].get("url_570xN") if images else None
        price = listing.get("price", {})
        price_amount = float(price.get("amount", 0)) / float(price.get("divisor", 100))

        return RawData(
            external_id=str(listing.get("listing_id")),
            title=listing.get("title", ""),
            description=listing.get("description", "")[:2000] if listing.get("description") else None,
            source_url=listing.get("url"),
            image_url=image_url,
            price=price_amount,
            currency=price.get("currency_code", "USD"),
            price_usd=price_amount if price.get("currency_code") == "USD" else None,
            review_count=listing.get("num_favorers", 0),
            review_rating=None,
            sales_count=listing.get("quantity_sold", 0),
            favorites_count=listing.get("num_favorers", 0),
            raw_payload={"source": "etsy", "taxonomy_id": listing.get("taxonomy_id")},
        )

    def _stub_data(self) -> list[RawData]:
        # STUB: Returns mock Etsy-style data when API key is not available
        return [
            RawData(
                external_id=f"etsy-stub-{i}",
                title=f"[STUB] Etsy Jewelry Item {i}",
                description="Stub data — configure ETSY_API_KEY for real data",
                price=round(25 + i * 15, 2),
                currency="USD",
                price_usd=round(25 + i * 15, 2),
                review_count=i * 10,
                favorites_count=i * 25,
                raw_payload={"source": "etsy_stub", "is_stub": True},
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
            favorites_count=raw.favorites_count,
            external_id=raw.external_id,
            target_gender="women",
            price_tier=self.infer_price_tier(raw.price_usd),
            is_mock=is_stub,
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )
