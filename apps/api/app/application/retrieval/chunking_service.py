"""Document chunking (RAG_SYSTEM.md §8-11, BACKLOG.md 4.2).

Structure-aware where structure is available (PDF page boundaries preserved
via `Document.metadata["pages"]`, RAG_SYSTEM.md §6's "do not discard source
location metadata"), paragraph-based otherwise (Markdown/plain text).
Deterministic: the same Document always produces the same chunks.
"""
import re
from dataclasses import dataclass

from app.domain.document import Document

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$")


def estimate_token_count(text: str) -> int:
    """Approximate token count (~4 chars/token), used only to size chunks
    against CHUNK_TARGET_TOKENS/CHUNK_OVERLAP_TOKENS — not an exact count for
    any particular embedding model's tokenizer (ADR-025)."""
    return max(1, len(text) // 4)


@dataclass(frozen=True, slots=True)
class _Unit:
    page_number: int | None
    text: str


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text) if p.strip()]


def _heading_title(paragraph: str) -> str | None:
    match = _HEADING_RE.match(paragraph.strip())
    return match.group(1).strip() if match else None


def _split_oversized(text: str, target_tokens: int, overlap_tokens: int) -> list[str]:
    """Word-level packing fallback for a single paragraph too large to fit in
    one chunk on its own (RAG_SYSTEM.md §9: "otherwise token/character-based
    chunking"). Guarantees forward progress each iteration."""
    words = text.split()
    if not words:
        return []
    target_chars = max(target_tokens * 4, 1)
    overlap_chars = max(overlap_tokens * 4, 0)

    pieces: list[str] = []
    start = 0
    while start < len(words):
        i = start
        length = 0
        piece_words: list[str] = []
        while i < len(words) and (length < target_chars or not piece_words):
            length += len(words[i]) + 1
            piece_words.append(words[i])
            i += 1
        pieces.append(" ".join(piece_words))

        if i >= len(words):
            break

        back = i
        back_len = 0
        while back > start and back_len < overlap_chars:
            back -= 1
            back_len += len(words[back]) + 1
        start = back if back > start else i

    return pieces


def _build_units(document: Document) -> list[_Unit]:
    pages = document.metadata.get("pages")
    if pages:
        return [_Unit(page_number=index + 1, text=paragraph) for index, page in enumerate(pages) for paragraph in _split_paragraphs(page)]
    return [_Unit(page_number=None, text=paragraph) for paragraph in _split_paragraphs(document.text_content)]


class ChunkingService:
    def __init__(self, target_tokens: int, overlap_tokens: int) -> None:
        self._target_tokens = target_tokens
        self._overlap_tokens = overlap_tokens

    def chunk_document(self, document: Document) -> list[dict]:
        units = _build_units(document)
        if not units:
            return []

        chunks: list[dict] = []
        buffer: list[_Unit] = []
        buffer_tokens = 0
        current_section: str | None = None

        def flush(*, seed_overlap: bool) -> None:
            nonlocal buffer, buffer_tokens
            if not buffer:
                return
            content = "\n\n".join(unit.text for unit in buffer)
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "content": content,
                    "page_number": buffer[0].page_number,
                    "section_title": current_section,
                    "token_count": estimate_token_count(content),
                    "metadata": {},
                }
            )
            if not seed_overlap:
                buffer = []
                buffer_tokens = 0
                return
            # Seed the next chunk's buffer with a token-bounded trailing
            # overlap from this one (RAG_SYSTEM.md §9). Only used when the
            # next unit shares this one's page, so overlap never mixes pages.
            overlap_units: list[_Unit] = []
            overlap_tok = 0
            for unit in reversed(buffer):
                unit_tok = estimate_token_count(unit.text)
                if overlap_units and overlap_tok + unit_tok > self._overlap_tokens:
                    break
                overlap_units.insert(0, unit)
                overlap_tok += unit_tok
            buffer = overlap_units
            buffer_tokens = overlap_tok

        for unit in units:
            heading = _heading_title(unit.text)
            if heading:
                current_section = heading

            # Page atomicity (RAG_SYSTEM.md §8, §10: citation precision) — a
            # chunk never spans two PDF pages. No-op for Markdown/text, where
            # every unit's page_number is None.
            if buffer and buffer[0].page_number != unit.page_number:
                flush(seed_overlap=False)

            unit_tokens = estimate_token_count(unit.text)

            if unit_tokens > self._target_tokens:
                flush(seed_overlap=False)
                for piece in _split_oversized(unit.text, self._target_tokens, self._overlap_tokens):
                    chunks.append(
                        {
                            "chunk_index": len(chunks),
                            "content": piece,
                            "page_number": unit.page_number,
                            "section_title": current_section,
                            "token_count": estimate_token_count(piece),
                            "metadata": {},
                        }
                    )
                continue

            if buffer and buffer_tokens + unit_tokens > self._target_tokens:
                flush(seed_overlap=True)

            buffer.append(unit)
            buffer_tokens += unit_tokens

        flush(seed_overlap=False)
        return chunks
