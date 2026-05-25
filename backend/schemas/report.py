import uuid
from datetime import datetime
from pydantic import BaseModel


class ReportRead(BaseModel):
    id: uuid.UUID
    report_type: str
    title: str
    language: str
    storage_url: str | None
    period_start: str | None
    period_end: str | None
    product_count: int
    signal_count: int
    ai_tokens_used: int
    email_sent: bool
    slack_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReportList(BaseModel):
    items: list[ReportRead]
    total: int


class ReportGenerateRequest(BaseModel):
    report_type: str = "daily"
    send_email: bool = True
    send_slack: bool = True
