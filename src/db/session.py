"""Async SQLAlchemy session and engine setup."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings


def _create_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url_async, echo=False, future=True)


engine: AsyncEngine = _create_engine()

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""
    async with async_session_factory() as session:  # type: ignore[call-arg]
        try:
            yield session
            await session.commit()
        except Exception:  # pragma: no cover - session rollback guard
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize database schema if necessary."""
    from .models import Base

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
