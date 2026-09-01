"""SQLAlchemy unit of work."""

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from arendabot.adapters.postgres.repositories import SqlAlchemyTelegramUserRepository
from arendabot.application.ports import TelegramUserRepository, UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Manage one async SQLAlchemy transaction and its repositories."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.users: TelegramUserRepository

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SqlAlchemyTelegramUserRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is not None:
            await self._session.rollback()
            await self._session.close()

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work has not been entered")
        await self._session.commit()
