import io

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.errors import DocumentProcessingError
from app.services.parsing.types import ParsedPage


def parse_pdf(data: bytes) -> list[ParsedPage]:
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise DocumentProcessingError("The PDF file could not be read.") from exc

    pages = [ParsedPage(number=i + 1, text=page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if not any(page.text.strip() for page in pages):
        raise DocumentProcessingError(
            "No extractable text found in this PDF (it may be a scanned image)."
        )
    return pages


def parse_docx(data: bytes) -> list[ParsedPage]:
    try:
        doc = DocxDocument(io.BytesIO(data))
    except Exception as exc:
        raise DocumentProcessingError("The DOCX file could not be read.") from exc

    text = "\n".join(p.text for p in doc.paragraphs)
    if not text.strip():
        raise DocumentProcessingError("No extractable text found in this document.")
    # DOCX has no reliable page boundaries without rendering; treat as one page.
    return [ParsedPage(number=None, text=text)]


def parse_txt(data: bytes) -> list[ParsedPage]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentProcessingError("The text file is not valid UTF-8.") from exc

    if not text.strip():
        raise DocumentProcessingError("The text file is empty.")
    return [ParsedPage(number=None, text=text)]


PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "txt": parse_txt,
}


def parse_document(data: bytes, document_type: str) -> list[ParsedPage]:
    parser = PARSERS.get(document_type)
    if parser is None:
        raise DocumentProcessingError(f"Unsupported document type: {document_type}")
    return parser(data)
