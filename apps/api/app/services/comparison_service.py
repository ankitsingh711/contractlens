import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.retrieval import hybrid_search
from app.services.document_service import get_document
from app.services.risk_categories import RISK_CATEGORIES

settings = get_settings()


@dataclass
class ComparisonSide:
    found: bool
    text: str | None
    page: int | None
    section: str | None
    chunk_id: str | None


@dataclass
class ComparisonRow:
    category: str
    label: str
    document_a: ComparisonSide
    document_b: ComparisonSide


async def _side_for(
    db: AsyncSession, organization_id: uuid.UUID, document_id: uuid.UUID, query: str
) -> ComparisonSide:
    result = await hybrid_search(
        db, query, organization_id, document_ids=[document_id], top_k=1
    )
    if not result.chunks or result.evidence_score < settings.EVIDENCE_THRESHOLD:
        return ComparisonSide(found=False, text=None, page=None, section=None, chunk_id=None)

    chunk = result.chunks[0]
    return ComparisonSide(
        found=True,
        text=chunk.text,
        page=chunk.page,
        section=chunk.section,
        chunk_id=str(chunk.chunk_id),
    )


async def compare_documents(
    db: AsyncSession,
    organization_id: uuid.UUID,
    document_id_a: uuid.UUID,
    document_id_b: uuid.UUID,
) -> list[ComparisonRow]:
    """Compares two documents clause-by-clause across the same fixed
    category list used for risk analysis. Each side is the top retrieved
    chunk for that category within that document — the comparison is
    literally the retrieved evidence, not an LLM-generated summary, so
    there's no risk of the comparison itself hallucinating a difference
    that isn't in the text. A category where neither document has a
    matching clause is omitted rather than shown as an empty row.
    """
    if document_id_a == document_id_b:
        raise ValidationAppError("Choose two different documents to compare.")

    # Raises NotFoundError/ForbiddenError if either document doesn't
    # belong to this organization, giving a clear error instead of a
    # silently empty comparison.
    await get_document(db, document_id_a, organization_id)
    await get_document(db, document_id_b, organization_id)

    rows: list[ComparisonRow] = []
    for category in RISK_CATEGORIES:
        side_a = await _side_for(db, organization_id, document_id_a, category.search_query)
        side_b = await _side_for(db, organization_id, document_id_b, category.search_query)
        if not side_a.found and not side_b.found:
            continue
        rows.append(
            ComparisonRow(category=category.key, label=category.label, document_a=side_a, document_b=side_b)
        )
    return rows
