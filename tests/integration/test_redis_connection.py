from app.infrastructure.redis.client import check_redis_connection


async def test_redis_connection_works():
    assert await check_redis_connection() is True
