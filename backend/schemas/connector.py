import uuid
from datetime import datetime
from pydantic import BaseModel


class ConnectorStatusRead(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    is_enabled: bool
    legal_status: str
    last_run_at: str | None
    last_run_status: str | None
    last_error: str | None

    class Config:
        from_attributes = True


class ConnectorRunResponse(BaseModel):
    connector_name: str
    status: str
    records_fetched: int
    records_saved: int
    error: str | None
    duration_seconds: float
