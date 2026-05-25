from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env in project root (two levels up from this file: backend/config.py → backend/ → project root)
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""
    supabase_storage_bucket: str = "reports"

    # Upstash Redis
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # AI
    gemini_api_key: str = ""
    ai_model: str = "gemini-3.1-flash-lite"
    ai_max_tokens: int = 4096

    # Notifications
    resend_api_key: str = ""
    alert_email_from: str = "noreply@example.com"
    alert_email_to: str = ""
    slack_webhook_url: str = ""

    # Connectors
    etsy_api_key: str = ""
    pinterest_access_token: str = ""

    # Brand
    brand_name: str = "Jewelry Brand"
    brand_market: str = "Turkey,Europe"
    brand_style_focus: str = "minimalist,gold-plated,silver,gemstone"
    brand_target_customer: str = "women 20-40, gift buyers, bridal"
    brand_price_min: float = 25.0
    brand_price_max: float = 250.0
    brand_categories: str = "rings,necklaces,bracelets,earrings,anklets"

    # App
    report_language: str = "tr"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    demo_mode: bool = False
    log_level: str = "INFO"
    sentry_dsn: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def has_database(self) -> bool:
        return bool(self.database_url)

    @property
    def has_ai(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_etsy(self) -> bool:
        return bool(self.etsy_api_key)

    @property
    def has_pinterest(self) -> bool:
        return bool(self.pinterest_access_token)

    @property
    def has_email(self) -> bool:
        return bool(self.resend_api_key and self.alert_email_to)

    @property
    def has_slack(self) -> bool:
        return bool(self.slack_webhook_url)

    @property
    def has_redis(self) -> bool:
        return bool(self.upstash_redis_rest_url and self.upstash_redis_rest_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
