from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from arendabot.domain.telegram_user import TelegramUser


def test_refresh_profile_preserves_identity_and_creation_time() -> None:
    created_at = datetime(2026, 8, 23, 10, tzinfo=UTC)
    user = TelegramUser(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        telegram_id=42,
        username="old_name",
        first_name="Old",
        last_name=None,
        language_code="en",
        is_bot=False,
        created_at=created_at,
        updated_at=created_at,
    )
    updated_at = created_at + timedelta(minutes=5)

    refreshed = user.refresh_profile(
        username="new_name",
        first_name="New",
        last_name="Name",
        language_code="ru",
        is_bot=True,
        updated_at=updated_at,
    )

    assert refreshed.id == user.id
    assert refreshed.telegram_id == 42
    assert refreshed.created_at == created_at
    assert refreshed.updated_at == updated_at
    assert refreshed.username == "new_name"
    assert refreshed.first_name == "New"
    assert refreshed.last_name == "Name"
    assert refreshed.language_code == "ru"
    assert refreshed.is_bot is True


def test_rejects_naive_timestamps() -> None:
    naive = datetime(2026, 8, 23, 10)

    with pytest.raises(ValueError, match="timezone-aware"):
        TelegramUser(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            telegram_id=42,
            username=None,
            first_name="Name",
            last_name=None,
            language_code=None,
            is_bot=False,
            created_at=naive,
            updated_at=naive,
        )
