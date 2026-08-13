from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.retrieval import hybrid_search
from app.schemas.search import EvidenceChunkResponse, SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_documents(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await hybrid_search(
        db,
        payload.query,
        current_user.organization_id,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )
    return SearchResponse(
        query=result.query,
        evidence_score=result.evidence_score,
        chunks=[
            EvidenceChunkResponse(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                filename=c.filename,
                page=c.page,
                section=c.section,
                heading=c.heading,
                chunk_type=c.chunk_type,
                text=c.text,
                vector_score=c.vector_score,
                keyword_score=c.keyword_score,
                fused_score=c.fused_score,
                rerank_score=c.rerank_score,
            )
            for c in result.chunks
        ],
    )
