from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import URL, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from arendabot.adapters.postgres.database import create_session_factory
from arendabot.adapters.postgres.models import TelegramUserModel
from arendabot.adapters.postgres.uow import SqlAlchemyUnitOfWork
from arendabot.domain.telegram_user import TelegramUser

pytestmark = pytest.mark.integration


def make_user(telegram_id: int) -> TelegramUser:
    now = datetime.now(UTC)
    return TelegramUser(
        id=uuid4(),
        telegram_id=telegram_id,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_bot=False,
        created_at=now,
        updated_at=now,
    )


async def test_migration_creates_telegram_users_table(postgres_url: URL) -> None:
    engine = create_async_engine(postgres_url)
    try:
        async with engine.connect() as connection:
            table_name = await connection.scalar(text("SELECT to_regclass('telegram_users')"))
    finally:
        await engine.dispose()

    assert table_name == "telegram_users"


async def test_repository_round_trip_and_update(postgres_url: URL) -> None:
    engine = create_async_engine(postgres_url)
    session_factory = create_session_factory(engine)
    user = make_user(1001)
    try:
        async with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            await unit_of_work.users.save(user)
            await unit_of_work.commit()

        async with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            loaded = await unit_of_work.users.get_by_telegram_id(user.telegram_id)
            assert loaded == user

            assert loaded is not None
            updated = loaded.refresh_profile(
                username="changed",
                first_name=loaded.first_name,
                last_name=loaded.last_name,
                language_code=loaded.language_code,
                is_bot=loaded.is_bot,
                updated_at=loaded.updated_at + timedelta(seconds=1),
            )
            await unit_of_work.users.save(updated)
            await unit_of_work.commit()

        async with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            loaded = await unit_of_work.users.get_by_telegram_id(user.telegram_id)
            assert loaded == updated
    finally:
        await engine.dispose()


async def test_unit_of_work_rolls_back_without_commit(postgres_url: URL) -> None:
    engine = create_async_engine(postgres_url)
    session_factory = create_session_factory(engine)
    user = make_user(1002)
    try:
        async with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            await unit_of_work.users.save(user)

        async with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            assert await unit_of_work.users.get_by_telegram_id(user.telegram_id) is None
    finally:
        await engine.dispose()


async def test_database_rejects_duplicate_telegram_id(postgres_url: URL) -> None:
    engine = create_async_engine(postgres_url)
    session_factory = create_session_factory(engine)
    first = make_user(1003)
    duplicate = make_user(1003)
    try:
        async with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
            await unit_of_work.users.save(first)
            await unit_of_work.commit()

        with pytest.raises(IntegrityError):
            async with SqlAlchemyUnitOfWork(session_factory) as unit_of_work:
                await unit_of_work.users.save(duplicate)
                await unit_of_work.commit()
    finally:
        await engine.dispose()


async def test_database_rejects_update_before_creation(postgres_url: URL) -> None:
    engine = create_async_engine(postgres_url)
    session_factory = create_session_factory(engine)
    created_at = datetime.now(UTC)
    invalid = TelegramUserModel(
        id=uuid4(),
        telegram_id=1004,
        username=None,
        first_name="Invalid",
        last_name=None,
        language_code=None,
        is_bot=False,
        created_at=created_at,
        updated_at=created_at - timedelta(seconds=1),
    )
    try:
        with pytest.raises(IntegrityError):
            async with session_factory() as session:
                session.add(invalid)
                await session.commit()
    finally:
        await engine.dispose()
