"""Async SQLAlchemy engine, sessions, and readiness checks."""

import logging
from typing import Protocol

from sqlalchemy import URL, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class ReadinessProbe(Protocol):
    """Report whether an application's required dependencies are available."""

    async def is_ready(self) -> bool:
        """Return true when dependencies are ready."""
        ...


class SqlAlchemyReadinessProbe:
    """Check PostgreSQL availability through an async engine."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def is_ready(self) -> bool:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("Database readiness check failed")
            return False
        return True


def create_engine(database_url: str | URL, *, echo: bool = False) -> AsyncEngine:
    """Create the application's async database engine."""
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessions that retain loaded state after commits."""
    return async_sessionmaker(engine, expire_on_commit=False)
