from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ForbiddenError
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse
from app.services.audit_service import list_audit_logs

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Only organization admins can view the audit log.")

    entries = await list_audit_logs(db, current_user.organization_id)
    return AuditLogListResponse(
        audit_logs=[
            AuditLogResponse(
                id=entry.id,
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                metadata=entry.audit_metadata,
                ip_address=entry.ip_address,
                user_email=user_email,
                created_at=entry.created_at,
            )
            for entry, user_email in entries
        ]
    )
