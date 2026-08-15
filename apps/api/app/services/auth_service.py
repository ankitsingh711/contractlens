import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedError, ValidationAppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.audit_service import log_action


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "org"


async def register_user(
    db: AsyncSession, payload: RegisterRequest, ip_address: str | None = None
) -> TokenResponse:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise ValidationAppError("An account with this email already exists.")

    base_slug = _slugify(payload.organization_name)
    slug = base_slug
    suffix = 1
    while await db.scalar(select(Organization).where(Organization.slug == slug)):
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    organization = Organization(name=payload.organization_name, slug=slug)
    db.add(organization)
    await db.flush()

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.ADMIN,
        organization_id=organization.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await log_action(
        db,
        organization_id=organization.id,
        user_id=user.id,
        action="user.register",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip_address,
    )

    token = create_access_token(user.id, organization.id)
    return TokenResponse(access_token=token)


async def authenticate_user(
    db: AsyncSession, payload: LoginRequest, ip_address: str | None = None
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))

    if user is None:
        # Not attributable to any organization, so there is nowhere to
        # record it in an org-scoped audit log — see docs/security.md.
        raise UnauthorizedError("Invalid email or password.")

    if not verify_password(payload.password, user.hashed_password):
        await log_action(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            action="user.login_failed",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
        )
        raise UnauthorizedError("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedError("This account has been deactivated.")

    await log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="user.login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip_address,
    )

    token = create_access_token(user.id, user.organization_id)
    return TokenResponse(access_token=token)
