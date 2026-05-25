"""
Storage Service — Supabase Storage for reports and uploaded files.
Falls back gracefully if Supabase is not configured.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class StorageService:

    def __init__(self):
        from config import get_settings
        self.settings = get_settings()
        self.bucket = self.settings.supabase_storage_bucket

    def _get_client(self):
        from database import get_supabase_client
        return get_supabase_client()

    async def upload_report(self, content: str, filename: str) -> str | None:
        """Upload a report markdown file to Supabase Storage. Returns public URL or None."""
        if not self.settings.supabase_url:
            logger.warning("Supabase not configured — skipping report upload")
            return None

        try:
            client = self._get_client()
            path = f"reports/{filename}"
            data = content.encode("utf-8")

            client.storage.from_(self.bucket).upload(
                path=path,
                file=data,
                file_options={"content-type": "text/markdown; charset=utf-8"},
            )

            # Get public URL
            response = client.storage.from_(self.bucket).get_public_url(path)
            return response

        except Exception as e:
            logger.error(f"Failed to upload report {filename}: {e}")
            return None

    async def upload_file(self, content: bytes, path: str, content_type: str = "application/octet-stream") -> str | None:
        """Upload any file to Supabase Storage. Returns public URL or None."""
        if not self.settings.supabase_url:
            return None

        try:
            client = self._get_client()
            client.storage.from_(self.bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": content_type},
            )
            return client.storage.from_(self.bucket).get_public_url(path)
        except Exception as e:
            logger.error(f"Failed to upload {path}: {e}")
            return None

    async def list_reports(self) -> list[dict]:
        """List all report files in storage."""
        if not self.settings.supabase_url:
            return []
        try:
            client = self._get_client()
            files = client.storage.from_(self.bucket).list("reports/")
            return files or []
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []

    def generate_report_filename(self, report_type: str) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"{report_type}_{ts}.md"
