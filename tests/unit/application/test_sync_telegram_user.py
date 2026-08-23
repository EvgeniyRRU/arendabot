from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from arendabot.application.ports import TelegramUserRepository, UnitOfWork
from arendabot.application.sync_telegram_user import (
    SyncTelegramUser,
    SyncTelegramUserCommand,
)
from arendabot.domain.telegram_user import TelegramUser


class FakeTelegramUserRepository(TelegramUserRepository):
    def __init__(self, user: TelegramUser | None = None) -> None:
        self.user = user
        self.saved: TelegramUser | None = None

    async def get_by_telegram_id(self, telegram_id: int) -> TelegramUser | None:
        if self.user is not None and self.user.telegram_id == telegram_id:
            return self.user
        return None

    async def save(self, user: TelegramUser) -> None:
        self.saved = user
        self.user = user


class FakeUnitOfWork(UnitOfWork):
    def __init__(self, repository: FakeTelegramUserRepository) -> None:
        self.users = repository
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True


def make_service(
    repository: FakeTelegramUserRepository,
    *,
    now: datetime,
) -> tuple[SyncTelegramUser, FakeUnitOfWork]:
    unit_of_work = FakeUnitOfWork(repository)

    def factory() -> UnitOfWork:
        return unit_of_work

    service = SyncTelegramUser(
        unit_of_work_factory=factory,
        clock=lambda: now,
        id_factory=lambda: UUID("22222222-2222-2222-2222-222222222222"),
    )
    return service, unit_of_work


async def test_creates_and_commits_a_new_user() -> None:
    now = datetime(2026, 8, 23, 11, tzinfo=UTC)
    repository = FakeTelegramUserRepository()
    service, unit_of_work = make_service(repository, now=now)

    result = await service.execute(
        SyncTelegramUserCommand(
            telegram_id=42,
            username="new_user",
            first_name="New",
            last_name=None,
            language_code="en",
            is_bot=False,
        )
    )

    assert result.id == UUID("22222222-2222-2222-2222-222222222222")
    assert result.telegram_id == 42
    assert result.created_at == now
    assert result.updated_at == now
    assert repository.saved == result
    assert unit_of_work.committed is True


async def test_refreshes_and_commits_an_existing_user() -> None:
    created_at = datetime(2026, 8, 20, 9, tzinfo=UTC)
    existing = TelegramUser(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        telegram_id=42,
        username="old_user",
        first_name="Old",
        last_name=None,
        language_code="en",
        is_bot=False,
        created_at=created_at,
        updated_at=created_at,
    )
    now = datetime(2026, 8, 23, 11, tzinfo=UTC)
    repository = FakeTelegramUserRepository(existing)
    service, unit_of_work = make_service(repository, now=now)

    result = await service.execute(
        SyncTelegramUserCommand(
            telegram_id=42,
            username="updated_user",
            first_name="Updated",
            last_name="Person",
            language_code="ru",
            is_bot=False,
        )
    )

    assert result.id == existing.id
    assert result.created_at == created_at
    assert result.updated_at == now
    assert result.username == "updated_user"
    assert result.first_name == "Updated"
    assert repository.saved == result
    assert unit_of_work.committed is True
