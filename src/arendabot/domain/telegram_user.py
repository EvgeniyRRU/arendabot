"""Telegram user domain entity."""

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TelegramUser:
    """A Telegram user known to the application."""

    id: UUID
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    language_code: str | None
    is_bot: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.created_at.utcoffset() is None or self.updated_at.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")

    def refresh_profile(
        self,
        *,
        username: str | None,
        first_name: str,
        last_name: str | None,
        language_code: str | None,
        is_bot: bool,
        updated_at: datetime,
    ) -> TelegramUser:
        """Return this user with current Telegram profile details."""
        return replace(
            self,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_bot=is_bot,
            updated_at=updated_at,
        )
