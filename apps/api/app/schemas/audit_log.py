import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, Any]
    ip_address: str | None
    user_email: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    audit_logs: list[AuditLogResponse]
