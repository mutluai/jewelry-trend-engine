"""
MANUAL UPLOAD CONNECTOR
Processes CSV/JSON files uploaded to Supabase Storage by the user.
Users upload competitor product lists or market research data.
The system normalizes and processes it through the standard pipeline.
"""
import csv
import io
import json
import logging
from datetime import datetime, timezone
from config import get_settings
from .base import BaseConnector, RawData, ProductData

logger = logging.getLogger(__name__)

EXPECTED_CSV_COLUMNS = ["title", "description", "price", "currency", "source_url", "image_url", "review_count"]


class ManualUploadConnector(BaseConnector):
    name = "manual_upload"
    display_name = "Manual Upload (CSV/JSON)"
    legal_status = "public_allowed"
    rate_limit_seconds = 0.0
    enabled = True

    def __init__(self, file_path: str | None = None, file_content: str | None = None):
        super().__init__()
        self.settings = get_settings()
        self.file_path = file_path
        self.file_content = file_content

    async def fetch(self) -> list[RawData]:
        """Fetch from Supabase Storage or provided content."""
        if self.file_content:
            return self._parse_content(self.file_content, "json")

        if self.file_path:
            return await self._fetch_from_storage(self.file_path)

        return await self._fetch_pending_uploads()

    async def _fetch_from_storage(self, path: str) -> list[RawData]:
        """Download file from Supabase Storage."""
        from database import get_supabase_client
        try:
            client = get_supabase_client()
            response = client.storage.from_("uploads").download(path)
            content = response.decode("utf-8")
            fmt = "csv" if path.endswith(".csv") else "json"
            return self._parse_content(content, fmt)
        except Exception as e:
            logger.error(f"Failed to download {path} from Supabase Storage: {e}")
            return []

    async def _fetch_pending_uploads(self) -> list[RawData]:
        """Check Supabase Storage for pending upload files."""
        from database import get_supabase_client
        try:
            client = get_supabase_client()
            files = client.storage.from_("uploads").list("pending/")
            all_items = []
            for file_info in files:
                file_path = f"pending/{file_info['name']}"
                items = await self._fetch_from_storage(file_path)
                all_items.extend(items)
                # Move to processed folder
                # client.storage.from_("uploads").move(file_path, f"processed/{file_info['name']}")
            return all_items
        except Exception as e:
            logger.warning(f"No pending uploads found: {e}")
            return []

    def _parse_content(self, content: str, fmt: str) -> list[RawData]:
        items = []
        try:
            if fmt == "json":
                data = json.loads(content)
                rows = data if isinstance(data, list) else data.get("products", [])
                for row in rows:
                    items.append(self._row_to_raw(row))
            elif fmt == "csv":
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    items.append(self._row_to_raw(dict(row)))
        except Exception as e:
            logger.error(f"Parse error: {e}")
        return items

    def _row_to_raw(self, row: dict) -> RawData:
        price = None
        try:
            price = float(row.get("price", 0) or 0) or None
        except (ValueError, TypeError):
            pass

        return RawData(
            external_id=row.get("id") or row.get("external_id"),
            title=str(row.get("title", "")).strip(),
            description=str(row.get("description", "")).strip() or None,
            source_url=row.get("source_url") or row.get("url"),
            image_url=row.get("image_url") or row.get("image"),
            price=price,
            currency=row.get("currency", "USD"),
            price_usd=price if row.get("currency", "USD") == "USD" else None,
            review_count=int(row.get("review_count", 0) or 0),
            review_rating=float(row.get("review_rating", 0) or 0) or None,
            sales_count=int(row.get("sales_count", 0) or 0),
            favorites_count=int(row.get("favorites_count", 0) or 0),
            raw_payload={"source": "manual_upload", "original_row": row},
        )

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
            review_rating=raw.review_rating,
            sales_count=raw.sales_count,
            favorites_count=raw.favorites_count,
            external_id=raw.external_id,
            price_tier=self.infer_price_tier(raw.price_usd),
            is_mock=False,
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )
