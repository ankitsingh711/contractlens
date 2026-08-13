import uuid

from app.models.document import Document, DocumentType
from app.models.document_chunk import ChunkType, DocumentChunk
from app.retrieval.fusion import reciprocal_rank_fusion


def _chunk_and_doc(text: str) -> tuple[DocumentChunk, Document]:
    doc = Document(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        filename="msa.pdf",
        document_type=DocumentType.PDF,
        content_type="application/pdf",
        size_bytes=100,
        storage_key="key",
    )
    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        chunk_type=ChunkType.CONTRACT_CLAUSE,
        text=text,
        token_count=5,
    )
    return chunk, doc


def test_rrf_ranks_chunk_found_in_both_lists_highest():
    shared_chunk, shared_doc = _chunk_and_doc("shared")
    vector_only_chunk, vector_only_doc = _chunk_and_doc("vector only")
    keyword_only_chunk, keyword_only_doc = _chunk_and_doc("keyword only")

    vector_results = [(shared_chunk, shared_doc, 0.9), (vector_only_chunk, vector_only_doc, 0.5)]
    keyword_results = [(shared_chunk, shared_doc, 0.8), (keyword_only_chunk, keyword_only_doc, 0.4)]

    fused = reciprocal_rank_fusion(vector_results, keyword_results)

    assert fused[0][0].id == shared_chunk.id
    fused_ids = [chunk.id for chunk, *_ in fused]
    assert vector_only_chunk.id in fused_ids
    assert keyword_only_chunk.id in fused_ids


def test_rrf_preserves_original_scores_alongside_fused_score():
    chunk, doc = _chunk_and_doc("text")
    vector_results = [(chunk, doc, 0.75)]
    keyword_results = [(chunk, doc, 0.33)]

    [(_, _, fused_score, vector_score, keyword_score)] = reciprocal_rank_fusion(
        vector_results, keyword_results
    )

    assert vector_score == 0.75
    assert keyword_score == 0.33
    assert fused_score > 0


def test_rrf_handles_empty_lists():
    assert reciprocal_rank_fusion([], []) == []
