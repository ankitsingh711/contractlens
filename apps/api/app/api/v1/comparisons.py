from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.comparison import CompareRequest, CompareResponse, ComparisonRowResponse, ComparisonSideResponse
from app.services.audit_service import log_action
from app.services.comparison_service import compare_documents

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("", response_model=CompareResponse)
async def compare(
    payload: CompareRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await compare_documents(
        db, current_user.organization_id, payload.document_id_a, payload.document_id_b
    )
    await log_action(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="comparison.create",
        resource_type="comparison",
        metadata={
            "document_id_a": str(payload.document_id_a),
            "document_id_b": str(payload.document_id_b),
        },
        ip_address=get_client_ip(request),
    )
    return CompareResponse(
        document_id_a=payload.document_id_a,
        document_id_b=payload.document_id_b,
        rows=[
            ComparisonRowResponse(
                category=r.category,
                label=r.label,
                document_a=ComparisonSideResponse(**vars(r.document_a)),
                document_b=ComparisonSideResponse(**vars(r.document_b)),
            )
            for r in rows
        ],
    )
