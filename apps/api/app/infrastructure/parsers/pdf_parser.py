"""PDF text extraction (RAG_SYSTEM.md §6, SECURITY.md §23).

Uses pypdf, a maintained pure-Python PDF library. Malformed files and
excessive page counts are rejected explicitly rather than left to fail in
some unpredictable downstream way (SECURITY.md §23: "handle parser failure,
malformed files, excessive page counts").
"""
import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.infrastructure.parsers.base import ParsedDocument, ParserError, normalize_text

# A generous but bounded ceiling — this is a demo/portfolio system, not a
# document-management platform (SECURITY.md §32: resource exhaustion controls).
MAX_PDF_PAGES = 500


def parse_pdf(content: bytes) -> ParsedDocument:
    try:
        reader = PdfReader(io.BytesIO(content))
    except (PdfReadError, ValueError) as exc:
        raise ParserError(f"Could not read PDF: {exc}") from exc

    try:
        page_count = len(reader.pages)
    except (PdfReadError, ValueError) as exc:
        raise ParserError(f"Could not read PDF page structure: {exc}") from exc

    if page_count == 0:
        raise ParserError("PDF has no pages")
    if page_count > MAX_PDF_PAGES:
        raise ParserError(f"PDF exceeds the maximum supported page count ({MAX_PDF_PAGES})")

    pages: list[str] = []
    for index, page in enumerate(reader.pages):
        try:
            raw_text = page.extract_text() or ""
        except Exception as exc:  # pypdf can raise a variety of parsing errors per-page
            raise ParserError(f"Failed to extract text from PDF page {index + 1}: {exc}") from exc
        pages.append(normalize_text(raw_text))

    text = "\n\n".join(pages)
    if not text.strip():
        raise ParserError("PDF contains no extractable text (it may be a scanned image without OCR)")

    return ParsedDocument(text=text, page_count=page_count, pages=pages, language=None, metadata={})
