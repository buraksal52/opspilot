"""Background job enqueueing (ADR-024, activated for embeddings per ADR-026).

`ArqJobQueue` lazily creates one pooled Redis connection per process (mirrors
`infrastructure/redis/client.py`'s pattern), not one per request.
"""
import asyncio
import uuid
from typing import Protocol

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings


class JobQueue(Protocol):
    async def enqueue_generate_embeddings(self, document_id: uuid.UUID) -> None: ...


class ArqJobQueue:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._pool: ArqRedis | None = None
        self._lock = asyncio.Lock()

    async def _get_pool(self) -> ArqRedis:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = await create_pool(RedisSettings.from_dsn(self._redis_url))
        return self._pool

    async def enqueue_generate_embeddings(self, document_id: uuid.UUID) -> None:
        pool = await self._get_pool()
        await pool.enqueue_job("generate_embeddings", str(document_id))
