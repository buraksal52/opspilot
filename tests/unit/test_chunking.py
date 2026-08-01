import uuid
from datetime import UTC, datetime

from app.application.retrieval.chunking_service import ChunkingService, estimate_token_count
from app.domain.document import Document, DocumentType


def _make_document(text_content: str, metadata: dict | None = None) -> Document:
    now = datetime.now(UTC)
    return Document(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        data_source_id=uuid.uuid4(),
        title="Test Document",
        document_type=DocumentType.MARKDOWN,
        text_content=text_content,
        page_count=None,
        language=None,
        metadata=metadata or {},
        created_at=now,
        updated_at=now,
    )


def test_short_document_produces_a_single_chunk():
    service = ChunkingService(target_tokens=550, overlap_tokens=75)
    document = _make_document("Just one short paragraph.")

    chunks = service.chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0]["content"] == "Just one short paragraph."
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["page_number"] is None


def test_no_content_loss_across_chunks():
    paragraphs = [f"Paragraph number {i} with some representative filler words to add length." for i in range(40)]
    document = _make_document("\n\n".join(paragraphs))
    service = ChunkingService(target_tokens=100, overlap_tokens=20)

    chunks = service.chunk_document(document)

    assert len(chunks) > 1
    combined = "\n\n".join(chunk["content"] for chunk in chunks)
    for paragraph in paragraphs:
        assert paragraph in combined


def test_chunking_is_deterministic():
    paragraphs = [f"Paragraph {i}. " * 5 for i in range(30)]
    document = _make_document("\n\n".join(paragraphs))
    service = ChunkingService(target_tokens=120, overlap_tokens=30)

    first = service.chunk_document(document)
    second = service.chunk_document(document)

    assert first == second


def test_adjacent_chunks_overlap():
    paragraphs = [f"Paragraph {i} has distinct filler content padded out for length." for i in range(20)]
    document = _make_document("\n\n".join(paragraphs))
    service = ChunkingService(target_tokens=80, overlap_tokens=25)

    chunks = service.chunk_document(document)

    assert len(chunks) > 1
    # The tail of chunk N should reappear at the head of chunk N+1.
    first_para_of_chunk1 = chunks[1]["content"].split("\n\n")[0]
    assert first_para_of_chunk1 in chunks[0]["content"]


def test_page_metadata_is_preserved_when_present():
    document = _make_document(
        text_content="ignored when pages metadata is present",
        metadata={"pages": ["Page one content.", "Page two content."]},
    )
    service = ChunkingService(target_tokens=550, overlap_tokens=75)

    chunks = service.chunk_document(document)

    assert {c["page_number"] for c in chunks} == {1, 2}


def test_markdown_heading_becomes_section_title():
    text = "# Refund Policy\n\nRefunds are processed within 5 business days.\n\n" "Late deliveries may qualify for a full refund."
    document = _make_document(text)
    service = ChunkingService(target_tokens=550, overlap_tokens=75)

    chunks = service.chunk_document(document)

    assert chunks[0]["section_title"] == "Refund Policy"


def test_oversized_paragraph_is_split_without_losing_words():
    huge_paragraph = " ".join(f"word{i}" for i in range(500))
    document = _make_document(huge_paragraph)
    service = ChunkingService(target_tokens=50, overlap_tokens=10)

    chunks = service.chunk_document(document)

    assert len(chunks) > 1
    combined_words = " ".join(c["content"] for c in chunks).split()
    for i in range(500):
        assert f"word{i}" in combined_words


def test_estimate_token_count_is_positive_for_nonempty_text():
    assert estimate_token_count("hello world") > 0
    assert estimate_token_count("x") == 1
