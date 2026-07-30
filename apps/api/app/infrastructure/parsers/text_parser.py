from app.infrastructure.parsers.base import ParsedDocument, parse_plain_text


def parse_text(content: bytes) -> ParsedDocument:
    return parse_plain_text(content)
