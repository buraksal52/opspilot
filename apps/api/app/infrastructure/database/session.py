from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

engine: AsyncEngine = create_async_engine(_settings.database_url, pool_pre_ping=True)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Commits the request's transaction on clean exit, rolls back on any
    # exception (including domain errors raised after partial writes), so a
    # route handler never needs to call commit()/rollback() itself. Phase 1's
    # endpoints were all read-only so this had no observable effect yet;
    # Phase 3 introduces the first writes (BACKLOG.md 3.2).
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
