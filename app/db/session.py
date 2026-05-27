from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.ENVIRONMENT == "development",
    # Pool sizing: enough for concurrent requests without overwhelming Postgres.
    # Tune via env for different deployment sizes.
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # detect stale connections after DB restarts
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
