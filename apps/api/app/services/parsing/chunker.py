import re
from dataclasses import dataclass

import tiktoken

from app.models.document_chunk import ChunkType
from app.services.parsing.types import ParsedPage

# Matches contract-style section headers such as:
#   "8.2 Termination", "8.2. Termination for Cause"
_NUMBERED_SECTION_RE = re.compile(r"^(?P<section>\d+(?:\.\d+){0,3})\.?\s+(?P<heading>[A-Z][A-Za-z0-9 ,&/'\-]{2,100})$")

# Matches "ARTICLE VIII - TERMINATION" / "SECTION 8: TERMINATION"
_LABELED_SECTION_RE = re.compile(
    r"^(?:ARTICLE|SECTION)\s+(?P<section>[IVXLCDM\d]+)[:.\-–]?\s*(?P<heading>[A-Z][A-Za-z0-9 ,&/'\-]{2,100})$"
)

MAX_CHUNK_TOKENS = 220
MIN_CHUNK_TOKENS = 20

_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


@dataclass
class Chunk:
    chunk_index: int
    page: int | None
    section: str | None
    heading: str | None
    chunk_type: ChunkType
    text: str
    token_count: int


def _match_heading(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return None
    for pattern in (_NUMBERED_SECTION_RE, _LABELED_SECTION_RE):
        match = pattern.match(stripped)
        if match:
            return match.group("section"), match.group("heading").strip()
    return None


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _split_long_paragraph(paragraph: str) -> list[str]:
    """Split an over-long paragraph on sentence boundaries, keeping each
    piece under MAX_CHUNK_TOKENS instead of cutting mid-sentence."""
    if count_tokens(paragraph) <= MAX_CHUNK_TOKENS:
        return [paragraph]

    sentences = re.split(r"(?<=[.;])\s+", paragraph)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and count_tokens(candidate) > MAX_CHUNK_TOKENS:
            pieces.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces or [paragraph]


def chunk_pages(pages: list[ParsedPage]) -> list[Chunk]:
    """Splits parsed pages into document-aware chunks, preserving page,
    section number, and heading — never a fixed-character-count split."""
    chunks: list[Chunk] = []
    current_section: str | None = None
    current_heading: str | None = None
    index = 0

    for page in pages:
        for paragraph in _split_paragraphs(page.text):
            heading_match = _match_heading(paragraph)
            if heading_match:
                current_section, current_heading = heading_match
                chunks.append(
                    Chunk(
                        chunk_index=index,
                        page=page.number,
                        section=current_section,
                        heading=current_heading,
                        chunk_type=ChunkType.HEADING,
                        text=paragraph,
                        token_count=count_tokens(paragraph),
                    )
                )
                index += 1
                continue

            for piece in _split_long_paragraph(paragraph):
                token_count = count_tokens(piece)
                if token_count < MIN_CHUNK_TOKENS and chunks and chunks[-1].page == page.number:
                    # Merge tiny fragments (e.g. a trailing signature line, or a
                    # short clause immediately under its heading) into the
                    # previous chunk instead of creating a near-empty chunk.
                    previous = chunks[-1]
                    previous.text = f"{previous.text}\n\n{piece}"
                    previous.token_count = count_tokens(previous.text)
                    if previous.chunk_type == ChunkType.HEADING and current_section:
                        previous.chunk_type = ChunkType.CONTRACT_CLAUSE
                    continue

                chunk_type = (
                    ChunkType.CONTRACT_CLAUSE if current_section else ChunkType.PARAGRAPH
                )
                chunks.append(
                    Chunk(
                        chunk_index=index,
                        page=page.number,
                        section=current_section,
                        heading=current_heading,
                        chunk_type=chunk_type,
                        text=piece,
                        token_count=token_count,
                    )
                )
                index += 1

    return chunks
