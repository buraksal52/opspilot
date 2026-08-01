from app.core.config import get_settings
from app.infrastructure.database.models.document_chunk import EMBEDDING_DIMENSION


def test_model_embedding_dimension_matches_settings_default():
    """The pgvector column width (EMBEDDING_DIMENSION, fixed by migration) and
    Settings.embedding_dimension (ADR-025) must never silently drift apart —
    changing one without the other would either truncate/reject vectors or
    misrepresent the actual column width to callers."""
    assert EMBEDDING_DIMENSION == get_settings().embedding_dimension
