"""Shared parser types and text normalization (RAG_SYSTEM.md §6-7)."""
import re
from dataclasses import dataclass


class ParserError(Exception):
    """Raised when uploaded content cannot be parsed (malformed/corrupt input, SECURITY.md §23)."""


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    text: str
    page_count: int | None
    # Per-page text, preserved so a future chunker (Phase 4) doesn't need to
    # re-parse the source file to recover page boundaries (RAG_SYSTEM.md §6:
    # "do not discard source location metadata during parsing").
    pages: list[str] | None
    language: str | None
    metadata: dict


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_TRAILING_WHITESPACE_RE = re.compile(r"[ \t]+\n")
_EXCESSIVE_BLANK_LINES_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """Whitespace/control-character cleanup only — never rewrites content
    (RAG_SYSTEM.md §7: "evidence should remain faithful to the original
    document")."""
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _TRAILING_WHITESPACE_RE.sub("\n", text)
    text = _EXCESSIVE_BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def parse_plain_text(content: bytes) -> ParsedDocument:
    """Shared implementation for Markdown and plain-text sources — both are
    "decode as UTF-8, then normalize", differing only in the ParserError
    message a caller might want. Callers pass their own error context."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ParserError(f"File is not valid UTF-8: {exc}") from exc

    text = normalize_text(text)
    if not text:
        raise ParserError("File has no extractable text content")

    return ParsedDocument(text=text, page_count=None, pages=None, language=None, metadata={})
