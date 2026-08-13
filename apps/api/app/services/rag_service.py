import time
import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.prompts import load_prompt
from app.retrieval import RetrievedChunk, hybrid_search
from app.services.citations import Citation, build_evidence_block, validate_citations
from app.services.llm import LLMMessage, get_llm_provider

settings = get_settings()

ABSTENTION_MESSAGE = (
    "I couldn't determine this from the provided documents.\n\n"
    "The available evidence does not contain enough information to answer this "
    "question reliably."
)

PROMPT_TASK = "qa"
PROMPT_VERSION = "v1"


@dataclass
class AnswerResult:
    query: str
    answer: str
    citations: list[Citation]
    confidence: float
    evidence_score: float
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    abstained: bool = False
    model: str = ""
    prompt_version: str = PROMPT_VERSION
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


async def answer_query(
    db: AsyncSession,
    query: str,
    organization_id: uuid.UUID,
    document_ids: list[uuid.UUID] | None = None,
) -> AnswerResult:
    """Retrieve -> evaluate evidence -> generate -> validate citations ->
    return. Every step is real: an insufficient-evidence result abstains
    instead of asking the LLM to answer regardless (see docs/agent.md)."""
    start = time.perf_counter()

    result = await hybrid_search(
        db,
        query,
        organization_id,
        document_ids=document_ids,
        top_k=settings.RETRIEVAL_TOP_K,
        candidate_pool_size=settings.RETRIEVAL_CANDIDATE_POOL_SIZE,
    )

    if not result.chunks or result.evidence_score < settings.EVIDENCE_THRESHOLD:
        return AnswerResult(
            query=query,
            answer=ABSTENTION_MESSAGE,
            citations=[],
            confidence=result.evidence_score,
            evidence_score=result.evidence_score,
            retrieved_chunks=result.chunks,
            abstained=True,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    prompt_template = load_prompt(PROMPT_TASK, PROMPT_VERSION)
    evidence_block = build_evidence_block(result.chunks)
    prompt = prompt_template.format(query=query, evidence=evidence_block)

    llm = get_llm_provider()
    response = await llm.complete([LLMMessage(role="user", content=prompt)])

    cleaned_answer, citations = validate_citations(response.text, result.chunks)
    if not citations:
        # The model produced no valid, evidence-backed citation — treat
        # this the same as insufficient evidence rather than showing an
        # unsupported claim.
        return AnswerResult(
            query=query,
            answer=ABSTENTION_MESSAGE,
            citations=[],
            confidence=result.evidence_score,
            evidence_score=result.evidence_score,
            retrieved_chunks=result.chunks,
            abstained=True,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    return AnswerResult(
        query=query,
        answer=cleaned_answer,
        citations=citations,
        confidence=result.evidence_score,
        evidence_score=result.evidence_score,
        retrieved_chunks=result.chunks,
        abstained=False,
        model=response.model,
        prompt_version=PROMPT_VERSION,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        latency_ms=(time.perf_counter() - start) * 1000,
    )
