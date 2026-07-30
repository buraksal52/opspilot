"""Local filesystem storage for uploaded raw files (SECURITY.md §21-22).

Uploaded files are stored outside any publicly-served directory, keyed only
by application-generated identifiers (workspace_id/data_source_id) — never by
the user-provided filename, which is retained solely as display metadata on
the DataSource record.

Behind a narrow protocol so a future object-storage (e.g. S3) implementation
can replace `LocalFileStorage` without touching application/domain code, the
same pattern already used for JWTProvider/PasswordHasher (ARCHITECTURE.md §6).
"""
import uuid
from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    def save(self, *, workspace_id: uuid.UUID, data_source_id: uuid.UUID, extension: str, content: bytes) -> str:
        """Persist `content` and return an opaque storage key for later read/delete."""
        ...

    def read(self, storage_key: str) -> bytes: ...

    def delete(self, storage_key: str) -> None: ...


class LocalFileStorage:
    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir).resolve()

    def save(self, *, workspace_id: uuid.UUID, data_source_id: uuid.UUID, extension: str, content: bytes) -> str:
        relative_path = Path(str(workspace_id)) / str(data_source_id) / f"source{extension}"
        full_path = self._base_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return str(relative_path)

    def read(self, storage_key: str) -> bytes:
        return self._resolve(storage_key).read_bytes()

    def delete(self, storage_key: str) -> None:
        self._resolve(storage_key).unlink(missing_ok=True)

    def _resolve(self, storage_key: str) -> Path:
        # storage_key is always an application-generated value from `save`
        # (built from UUIDs, never from user input) — this check is a
        # defense-in-depth guard against a future caller misusing it, not a
        # response to an exploitable path today.
        full_path = (self._base_dir / storage_key).resolve()
        if not full_path.is_relative_to(self._base_dir):
            raise ValueError("storage_key resolves outside the storage root")
        return full_path
