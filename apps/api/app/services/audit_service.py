import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.audit_log import AuditLog
from app.models.user import User

logger = get_logger("audit")


async def log_action(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    action: str,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """Records a compliance-relevant action. Never raises: audit logging
    must not be able to break the feature it's observing, so any failure
    here (e.g. a transient DB issue) is logged and swallowed rather than
    propagated — the same fail-safe philosophy as the observability
    client (app/observability/), just for security events instead of LLM
    traces.
    """
    try:
        db.add(
            AuditLog(
                organization_id=organization_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                audit_metadata=metadata or {},
                ip_address=ip_address,
            )
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error("audit_log.failed", action=action, error=str(exc))


async def list_audit_logs(
    db: AsyncSession, organization_id: uuid.UUID, limit: int = 50
) -> list[tuple[AuditLog, str | None]]:
    """Returns (entry, user_email) pairs — a left join so entries with no
    resolved user (e.g. a failed login for an email that isn't a real
    account) still appear, with user_email=None."""
    stmt = (
        select(AuditLog, User.email)
        .outerjoin(User, User.id == AuditLog.user_id)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]
