import uuid

from app.retrieval.types import RetrievedChunk
from app.services.citations import build_evidence_block, validate_citations


def _chunk(text: str, section: str | None = "8.2", page: int | None = 14) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        filename="msa.pdf",
        page=page,
        section=section,
        heading="Termination",
        chunk_type="contract_clause",
        text=text,
    )


def test_build_evidence_block_numbers_chunks_with_location():
    chunks = [_chunk("Either party may terminate upon 7 days notice.")]
    block = build_evidence_block(chunks)
    assert block.startswith("[1] (Section 8.2, Page 14):")
    assert "7 days notice" in block


def test_validate_citations_keeps_valid_markers():
    chunks = [_chunk("Either party may terminate upon 7 days notice.")]
    answer = "The agreement may be terminated with 7 days notice. [1]"

    cleaned, citations = validate_citations(answer, chunks)

    assert cleaned == answer
    assert len(citations) == 1
    assert citations[0].section == "8.2"
    assert citations[0].page == 14
    assert "7 days notice" in citations[0].quote


def test_validate_citations_strips_markers_not_in_retrieved_chunks():
    chunks = [_chunk("Either party may terminate upon 7 days notice.")]
    # The model hallucinated a second source that was never retrieved.
    answer = "The agreement may be terminated with 7 days notice. [1] It also caps liability. [2]"

    cleaned, citations = validate_citations(answer, chunks)

    assert "[2]" not in cleaned
    assert len(citations) == 1


def test_validate_citations_returns_no_citations_when_no_markers_present():
    chunks = [_chunk("Either party may terminate upon 7 days notice.")]
    answer = "The agreement may be terminated with 7 days notice."

    cleaned, citations = validate_citations(answer, chunks)

    assert cleaned == answer
    assert citations == []
