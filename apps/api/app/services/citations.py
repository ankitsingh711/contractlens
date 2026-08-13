import re
from dataclasses import dataclass

from app.retrieval.types import RetrievedChunk

_CITATION_MARKER_RE = re.compile(r"\[(\d+)\]")


@dataclass
class Citation:
    document_id: str
    filename: str
    page: int | None
    section: str | None
    heading: str | None
    chunk_id: str
    quote: str


def build_evidence_block(chunks: list[RetrievedChunk]) -> str:
    """Formats retrieved chunks as numbered evidence for the prompt. The
    numbers here are the only valid citation markers a generated answer
    may use — validate_citations() checks the model didn't invent others."""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        location = ", ".join(
            part
            for part in [
                f"Section {chunk.section}" if chunk.section else None,
                f"Page {chunk.page}" if chunk.page else None,
            ]
            if part
        )
        label = f"[{i}] ({location})" if location else f"[{i}]"
        blocks.append(f"{label}: {chunk.text}")
    return "\n\n".join(blocks)


def validate_citations(
    answer_text: str, chunks: list[RetrievedChunk]
) -> tuple[str, list[Citation]]:
    """Strips any citation marker that doesn't correspond to a retrieved
    chunk (a citation "that was not retrieved from the database" is never
    allowed to reach the user) and returns the citations that survived.
    """
    markers = sorted({int(m) for m in _CITATION_MARKER_RE.findall(answer_text)})
    citations: list[Citation] = []
    cleaned = answer_text

    for marker in markers:
        index = marker - 1
        if index < 0 or index >= len(chunks):
            # The model cited an index that was never in the evidence we
            # gave it — drop the marker rather than show a broken citation.
            cleaned = cleaned.replace(f"[{marker}]", "")
            continue
        chunk = chunks[index]
        citations.append(
            Citation(
                document_id=str(chunk.document_id),
                filename=chunk.filename,
                page=chunk.page,
                section=chunk.section,
                heading=chunk.heading,
                chunk_id=str(chunk.chunk_id),
                quote=chunk.text[:400],
            )
        )

    return cleaned.strip(), citations
