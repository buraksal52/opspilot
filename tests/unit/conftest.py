"""Overrides tests/conftest.py's DB-migrating fixture for this subtree.

TESTING.md §4: unit tests cover isolated deterministic components and should
not require infrastructure. The root conftest's `_migrated_database` fixture
is session-scoped/autouse for the whole `tests/` tree (needed by tests/api and
tests/integration), which would otherwise force every `tests/unit` test to
also stand up a Postgres connection it never uses. Overriding the fixture name
here (pytest resolves fixtures from the nearest conftest first) makes it a
no-op for tests/unit only, without touching the root conftest's behavior for
tests/api and tests/integration.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def _migrated_database():
    yield
