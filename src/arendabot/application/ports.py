"""Outbound application ports."""

from types import TracebackType
from typing import Protocol, Self

from arendabot.domain.telegram_user import TelegramUser


class TelegramUserRepository(Protocol):
    """Persistence contract for Telegram users."""

    async def get_by_telegram_id(self, telegram_id: int) -> TelegramUser | None:
        """Return the matching user, if one exists."""
        ...

    async def save(self, user: TelegramUser) -> None:
        """Insert or update a user."""
        ...


class UnitOfWork(Protocol):
    """Atomic persistence boundary."""

    users: TelegramUserRepository

    async def __aenter__(self) -> Self:
        """Open the unit of work."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the unit of work and roll back unfinished work."""
        ...

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...
