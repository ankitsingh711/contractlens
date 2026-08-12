from app.models.document_chunk import ChunkType
from app.services.parsing.chunker import chunk_pages
from app.services.parsing.types import ParsedPage

SAMPLE_TEXT = """MASTER SERVICES AGREEMENT

This Master Services Agreement is entered into between Acme Corp and Widget LLC.

8.2 Termination

Either party may terminate this agreement upon 7 days written notice to the \
other party if the other party materially breaches this agreement and fails \
to cure such breach within the applicable cure period specified herein.

9 Limitation of Liability

Neither party's liability under this agreement shall exceed the total fees \
paid in the twelve months preceding the claim, except for breaches of \
confidentiality obligations set forth in Section 5 of this Agreement.
"""


def test_chunker_preserves_section_and_heading():
    pages = [ParsedPage(number=1, text=SAMPLE_TEXT)]
    chunks = chunk_pages(pages)

    sections = {c.section for c in chunks if c.section}
    assert "8.2" in sections
    assert "9" in sections

    termination_chunks = [c for c in chunks if c.section == "8.2"]
    assert any(c.heading == "Termination" for c in termination_chunks)
    assert any("7 days written notice" in c.text for c in termination_chunks)


def test_chunker_assigns_page_numbers():
    pages = [
        ParsedPage(number=1, text="1 Definitions\n\nSome definitional text here for page one."),
        ParsedPage(number=2, text="2 Payment Terms\n\nPayment is due within thirty days of invoice."),
    ]
    chunks = chunk_pages(pages)

    pages_seen = {c.page for c in chunks}
    assert pages_seen == {1, 2}


def test_chunker_marks_clause_type_when_under_a_section():
    pages = [
        ParsedPage(
            number=1,
            text="10 Confidentiality\n\nEach party shall keep the other party's confidential "
            "information strictly confidential and shall not disclose it to any third party "
            "without prior written consent, except as required by law.",
        )
    ]
    chunks = chunk_pages(pages)
    clause_chunks = [c for c in chunks if c.chunk_type == ChunkType.CONTRACT_CLAUSE]
    assert clause_chunks
    assert all(c.section == "10" for c in clause_chunks)


def test_chunker_splits_long_paragraph_on_sentence_boundaries():
    long_sentence_block = " ".join(
        f"This is sentence number {i} describing an obligation of the parties under this agreement."
        for i in range(40)
    )
    pages = [ParsedPage(number=1, text=long_sentence_block)]
    chunks = chunk_pages(pages)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.text.strip().endswith(".")


def test_chunker_handles_empty_pages():
    assert chunk_pages([ParsedPage(number=1, text="   \n\n  ")]) == []
