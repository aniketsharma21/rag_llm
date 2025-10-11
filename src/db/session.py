"""Async SQLAlchemy session and engine setup.

This module provides the database connection and session management for the
application using SQLAlchemy's async API. It includes:
- Async database engine configuration
- Session factory for creating new database sessions
- Context manager for session lifecycle management
- Database initialization utilities

Example:
    ```python
    from src.db.session import get_session
    
    async with get_session() as session:
        # Use the session for database operations
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalar_one_or_none()
    ```
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings


def _create_engine() -> AsyncEngine:
    """Create and configure an async SQLAlchemy engine.
    
    Returns:
        AsyncEngine: A configured SQLAlchemy async engine instance.
        
    Note:
        - Uses the database URL from application settings
        - Disables SQL query echoing by default
        - Enables SQLAlchemy 2.0 future features
    """
    return create_async_engine(settings.database_url_async, echo=False, future=True)


engine: AsyncEngine = _create_engine()

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Asynchronous context manager for database sessions.
    
    Yields:
        AsyncSession: A database session for executing queries.
        
    Note:
        - Automatically handles session commit/rollback
        - Ensures the session is properly closed after use
        - Rolls back on any unhandled exceptions
        
    Example:
        ```python
        async with get_session() as session:
            user = User(name='test')
            session.add(user)
            # No need to call commit/close manually
        ```
    """
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
    """Initialize the database schema.
    
    Creates all tables defined in the models if they don't already exist.
    
    Note:
        - Safe to call multiple times (won't recreate existing tables)
        - Should be called during application startup
        - Uses async engine for table creation
    """
    from .models import Base

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
