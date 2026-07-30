"""Parser unit tests use small, self-built fixtures (TESTING.md §29: "do not
make every test depend on the full synthetic dataset") rather than requiring
`make generate-northstar` to have already run. One test at the bottom
additionally exercises the real Northstar PDFs when they happen to be
present, as a bonus real-world check, but is skipped otherwise.
"""
from pathlib import Path

import pytest
from fpdf import FPDF

from app.infrastructure.parsers.base import ParserError
from app.infrastructure.parsers.markdown_parser import parse_markdown
from app.infrastructure.parsers.pdf_parser import parse_pdf
from app.infrastructure.parsers.text_parser import parse_text

REPO_ROOT = Path(__file__).resolve().parents[2]
NORTHSTAR_DOCS_DIR = REPO_ROOT / "data" / "northstar" / "documents"


def _build_pdf_bytes(pages: list[str]) -> bytes:
    pdf = FPDF()
    for page_text in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, page_text)
    return bytes(pdf.output())


def test_parse_pdf_extracts_text_and_page_count():
    content = _build_pdf_bytes(["Hello from page one.", "Second page content."])
    result = parse_pdf(content)
    assert result.page_count == 2
    assert result.pages is not None and len(result.pages) == 2
    assert "Hello from page one" in result.text
    assert "Second page content" in result.text


def test_parse_pdf_rejects_non_pdf_bytes():
    with pytest.raises(ParserError, match="Could not read PDF"):
        parse_pdf(b"this is not a pdf file at all")


def test_parse_pdf_rejects_empty_extracted_text():
    pdf = FPDF()
    pdf.add_page()  # a page with no text content at all
    content = bytes(pdf.output())
    with pytest.raises(ParserError, match="no extractable text"):
        parse_pdf(content)


def test_parse_markdown_normalizes_whitespace():
    content = "# Title\r\n\r\n\r\n\r\nSome   text with trailing spaces   \nMore text.\n".encode("utf-8")
    result = parse_markdown(content)
    assert "# Title" in result.text
    assert "\n\n\n" not in result.text  # excessive blank lines collapsed
    assert result.page_count is None


def test_parse_markdown_rejects_empty_content():
    with pytest.raises(ParserError, match="no extractable text"):
        parse_markdown(b"   \n\n  \n")


def test_parse_markdown_rejects_invalid_utf8():
    with pytest.raises(ParserError, match="UTF-8"):
        parse_markdown(b"\xff\xfe not valid utf-8")


def test_parse_text_behaves_like_markdown_for_plain_content():
    content = b"Plain text content.\nSecond line.\n"
    result = parse_text(content)
    assert result.text == "Plain text content.\nSecond line."
    assert result.page_count is None


@pytest.mark.skipif(
    not NORTHSTAR_DOCS_DIR.exists(), reason="Northstar dataset not generated (run: make generate-northstar)"
)
def test_parses_real_northstar_shipping_policy_pdf():
    content = (NORTHSTAR_DOCS_DIR / "Shipping Policy.pdf").read_bytes()
    result = parse_pdf(content)
    assert result.page_count == 1
    assert "delivery window" in result.text.lower()
