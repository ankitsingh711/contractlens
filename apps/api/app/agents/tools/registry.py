import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import ToolCallRecord, run_tool
from app.agents.tools.calculate import CalculateInput, calculate
from app.agents.tools.compare_clauses import CompareClausesInput, compare_clauses
from app.agents.tools.get_clause import GetClauseInput, get_clause
from app.agents.tools.get_document_metadata import GetDocumentMetadataInput, get_document_metadata
from app.agents.tools.retrieve_source import RetrieveSourceInput, retrieve_source
from app.agents.tools.search_documents import SearchDocumentsInput, search_documents


@dataclass
class ToolSpec:
    name: str
    input_model: type[BaseModel]
    fn: Callable[[BaseModel], Awaitable[BaseModel]]


def build_tool_registry(db: AsyncSession, organization_id: uuid.UUID) -> dict[str, ToolSpec]:
    """Binds each tool to this request's db session/organization scope.
    Every tool is org-scoped at the query level (see each tool's SQL), so
    the agent can never read another organization's documents through a
    tool call regardless of what the model asks for."""
    return {
        "search_documents": ToolSpec(
            name="search_documents",
            input_model=SearchDocumentsInput,
            fn=lambda i: search_documents(db, organization_id, i),
        ),
        "get_clause": ToolSpec(
            name="get_clause",
            input_model=GetClauseInput,
            fn=lambda i: get_clause(db, organization_id, i),
        ),
        "get_document_metadata": ToolSpec(
            name="get_document_metadata",
            input_model=GetDocumentMetadataInput,
            fn=lambda i: get_document_metadata(db, organization_id, i),
        ),
        "calculate": ToolSpec(
            name="calculate",
            input_model=CalculateInput,
            fn=lambda i: calculate(db, organization_id, i),
        ),
        "retrieve_source": ToolSpec(
            name="retrieve_source",
            input_model=RetrieveSourceInput,
            fn=lambda i: retrieve_source(db, organization_id, i),
        ),
        "compare_clauses": ToolSpec(
            name="compare_clauses",
            input_model=CompareClausesInput,
            fn=lambda i: compare_clauses(db, organization_id, i),
        ),
    }


async def call_tool(
    registry: dict[str, ToolSpec], name: str, raw_input: dict[str, Any]
) -> ToolCallRecord:
    spec = registry.get(name)
    if spec is None:
        return ToolCallRecord(name=name, input=raw_input, output=None, latency_ms=0.0, error=f"Unknown tool '{name}'.")
    try:
        validated = spec.input_model.model_validate(raw_input)
    except Exception as exc:
        return ToolCallRecord(name=name, input=raw_input, output=None, latency_ms=0.0, error=f"Invalid input: {exc}")
    return await run_tool(name, validated, spec.fn)
