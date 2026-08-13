import uuid

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.get_clause import GetClauseInput, get_clause


class CompareClausesInput(BaseModel):
    document_id_a: str
    document_id_b: str
    section: str = Field(min_length=1, max_length=64)


class CompareClausesOutput(BaseModel):
    section: str
    document_a_text: str | None
    document_b_text: str | None
    both_found: bool


async def compare_clauses(
    db: AsyncSession, organization_id: uuid.UUID, input: CompareClausesInput
) -> CompareClausesOutput:
    """Fetches the same section from two documents side by side. A basic
    building block for document comparison — the dedicated comparison
    workflow/UI (multi-clause, risk-aware) is Phase 5; this tool is what
    it will call per clause."""
    result_a = await get_clause(
        db, organization_id, GetClauseInput(document_id=input.document_id_a, section=input.section)
    )
    result_b = await get_clause(
        db, organization_id, GetClauseInput(document_id=input.document_id_b, section=input.section)
    )
    return CompareClausesOutput(
        section=input.section,
        document_a_text=result_a.text,
        document_b_text=result_b.text,
        both_found=result_a.found and result_b.found,
    )
