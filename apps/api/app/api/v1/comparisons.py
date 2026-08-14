from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.comparison import CompareRequest, CompareResponse, ComparisonRowResponse, ComparisonSideResponse
from app.services.comparison_service import compare_documents

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("", response_model=CompareResponse)
async def compare(
    payload: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await compare_documents(
        db, current_user.organization_id, payload.document_id_a, payload.document_id_b
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
