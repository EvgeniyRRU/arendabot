"""Synchronize a Telegram profile with the domain store."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from arendabot.application.ports import UnitOfWork
from arendabot.domain.telegram_user import TelegramUser


@dataclass(frozen=True, slots=True)
class SyncTelegramUserCommand:
    """Telegram profile data accepted by the synchronization use case."""

    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    language_code: str | None
    is_bot: bool


class SyncTelegramUser:
    """Create a Telegram user or refresh its profile."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock
        self._id_factory = id_factory

    async def execute(self, command: SyncTelegramUserCommand) -> TelegramUser:
        """Synchronize one Telegram user in a single transaction."""
        now = self._clock()
        async with self._unit_of_work_factory() as unit_of_work:
            user = await unit_of_work.users.get_by_telegram_id(command.telegram_id)
            if user is None:
                user = TelegramUser(
                    id=self._id_factory(),
                    telegram_id=command.telegram_id,
                    username=command.username,
                    first_name=command.first_name,
                    last_name=command.last_name,
                    language_code=command.language_code,
                    is_bot=command.is_bot,
                    created_at=now,
                    updated_at=now,
                )
            else:
                user = user.refresh_profile(
                    username=command.username,
                    first_name=command.first_name,
                    last_name=command.last_name,
                    language_code=command.language_code,
                    is_bot=command.is_bot,
                    updated_at=now,
                )

            await unit_of_work.users.save(user)
            await unit_of_work.commit()
            return user
