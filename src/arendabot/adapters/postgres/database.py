"""Async SQLAlchemy engine and session construction."""

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str | URL, *, echo: bool = False) -> AsyncEngine:
    """Create the application's async database engine."""
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessions that retain loaded state after commits."""
    return async_sessionmaker(engine, expire_on_commit=False)
