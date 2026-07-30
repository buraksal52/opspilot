"""Upload validation (SECURITY.md §19-22, API.md §22).

Extension determines the intended source type; where a cheap, reliable
content check exists (PDF magic bytes) it is applied too, since SECURITY.md
§19 explicitly warns against trusting the extension alone. The client-supplied
Content-Type header is recorded for display but is not used to gate
acceptance: it is easily spoofed and inconsistent across browsers/OSes for
plain-text formats (a CSV exported from Excel may arrive as
"application/vnd.ms-excel", "text/csv", or "application/octet-stream"
depending on the client). The real content check for text-based formats is
that they successfully decode/parse (infrastructure/parsers), which runs
right after this validation step.
"""
import pathlib

from app.core.errors import ValidationAppError
from app.domain.data_source import SourceType

EXTENSION_TO_SOURCE_TYPE: dict[str, SourceType] = {
    ".csv": SourceType.CSV,
    ".pdf": SourceType.PDF,
    ".md": SourceType.MARKDOWN,
    ".markdown": SourceType.MARKDOWN,
    ".txt": SourceType.TEXT,
}

_PDF_MAGIC_BYTES = b"%PDF-"


def determine_source_type(filename: str) -> SourceType:
    extension = pathlib.Path(filename).suffix.lower()
    source_type = EXTENSION_TO_SOURCE_TYPE.get(extension)
    if source_type is None:
        supported = ", ".join(sorted(EXTENSION_TO_SOURCE_TYPE))
        raise ValidationAppError(f"Unsupported file extension {extension or '(none)'!r}. Supported: {supported}")
    return source_type


def validate_upload(*, filename: str, size_bytes: int, content: bytes, max_size_bytes: int) -> SourceType:
    if size_bytes == 0:
        raise ValidationAppError("Uploaded file is empty.")
    if size_bytes > max_size_bytes:
        raise ValidationAppError(f"File exceeds the maximum upload size of {max_size_bytes} bytes.")

    source_type = determine_source_type(filename)

    if source_type == SourceType.PDF and not content.startswith(_PDF_MAGIC_BYTES):
        raise ValidationAppError("File has a .pdf extension but is not a valid PDF file.")

    return source_type
