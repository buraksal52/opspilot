from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(get_settings().redis_url)


async def check_redis_connection() -> bool:
    client = get_redis_client()
    return bool(await client.ping())
