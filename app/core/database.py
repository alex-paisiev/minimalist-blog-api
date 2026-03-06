from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


# Engine and session factory are initialised lazily at startup (see lifespan in
# main.py). Tests replace get_db via dependency_overrides, so they never touch these.
_async_session: async_sessionmaker[AsyncSession] | None = None


def init_db() -> None:
    """Create the engine and session factory. Called once at application startup."""
    global _async_session
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=(settings.APP_ENV == "development"),
    )
    _async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if _async_session is None:
        raise RuntimeError("Database not initialised. Call init_db() at startup.")
    async with _async_session() as session:
        try:
            yield session
        finally:
            await session.close()
