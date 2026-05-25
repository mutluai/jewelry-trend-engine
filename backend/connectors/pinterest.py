"""
PINTEREST CONNECTOR — STUB
Pinterest API v5 requires Business account approval.
This is a stub connector that returns mock data until API access is granted.
Legal status: stub
Replace _stub_data() with real API calls once PINTEREST_ACCESS_TOKEN is set.
"""
import logging
from datetime import datetime, timezone
from config import get_settings
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

PINTEREST_API_BASE = "https://api.pinterest.com/v5"

PINTEREST_JEWELRY_BOARDS = [
    "jewelry", "gold jewelry", "silver jewelry", "minimalist jewelry",
    "boho jewelry", "bridal jewelry", "statement jewelry",
]


class PinterestConnector(BaseConnector):
    name = "pinterest"
    display_name = "Pinterest API v5"
    legal_status = "stub"  # STUB until API access approved
    rate_limit_seconds = 1.0
    enabled = True

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.access_token = self.settings.pinterest_access_token
        self.is_stub = not bool(self.access_token)
        if self.is_stub:
            logger.warning("Pinterest access token not configured — running in STUB mode")

    async def fetch(self) -> list[RawData]:
        if self.is_stub:
            return self._stub_data()

        # STUB: Replace with real API calls when access token is available
        # Real implementation would call:
        # GET /v5/search/pins?query={keyword}&ad_account_id=...
        logger.warning("Pinterest real API not yet implemented — using stub")
        return self._stub_data()

    def _stub_data(self) -> list[RawData]:
        """STUB: Mock Pinterest-style trend data."""
        stub_items = [
            ("Minimalist Gold Ring Stack", 45.0, 850, 2300),
            ("Pearl Drop Earrings Vintage", 38.0, 1200, 4100),
            ("Evil Eye Necklace Gold", 32.0, 980, 3200),
            ("Layered Chain Necklace Set", 55.0, 670, 1890),
            ("Boho Crystal Bracelet", 28.0, 445, 1200),
            ("Diamond Tennis Bracelet", 189.0, 320, 890),
            ("Moonstone Ring Silver", 42.0, 760, 2100),
            ("Rose Gold Hoop Earrings", 35.0, 1100, 3600),
        ]
        return [
            RawData(
                external_id=f"pinterest-stub-{i}",
                title=f"[STUB] {title}",
                description=f"Pinterest trend stub data for '{title}'",
                price=price,
                currency="USD",
                price_usd=price,
                review_count=saves,
                favorites_count=saves,
                raw_payload={
                    "source": "pinterest_stub",
                    "is_stub": True,
                    "saves": saves,
                    "clicks": clicks,
                    "board_keywords": PINTEREST_JEWELRY_BOARDS[:3],
                },
            )
            for i, (title, price, saves, clicks) in enumerate(stub_items)
        ]

    async def normalize(self, raw: RawData) -> ProductData:
        return ProductData(
            title=raw.title,
            description=raw.description,
            price=raw.price,
            currency=raw.currency,
            price_usd=raw.price_usd,
            favorites_count=raw.favorites_count,
            external_id=raw.external_id,
            target_gender="women",
            price_tier=self.infer_price_tier(raw.price_usd),
            is_mock=raw.raw_payload.get("is_stub", False),
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )
