"""Typed environment configuration."""

import re
from enum import StrEnum
from typing import Self

from pydantic import AnyHttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import make_url
from sqlalchemy.exc import ArgumentError

WEBHOOK_PATH = "/telegram/webhook"
_WEBHOOK_SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,256}$")


class UpdateMode(StrEnum):
    """Supported Telegram update delivery modes."""

    POLLING = "polling"
    WEBHOOK = "webhook"


class Settings(BaseSettings):
    """Application settings loaded from `ARENDABOT_` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="ARENDABOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: SecretStr
    database_url: str
    update_mode: UpdateMode = UpdateMode.POLLING
    webhook_base_url: AnyHttpUrl | None = None
    webhook_secret: SecretStr | None = None
    database_echo: bool = False
    drop_pending_updates: bool = False
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        try:
            driver_name = make_url(value).drivername
        except ArgumentError as error:
            raise ValueError("database_url must be a valid SQLAlchemy URL") from error
        if driver_name != "postgresql+asyncpg":
            raise ValueError("database_url must use the postgresql+asyncpg driver")
        return value

    @model_validator(mode="after")
    def validate_webhook_settings(self) -> Self:
        if self.update_mode is UpdateMode.WEBHOOK:
            if self.webhook_base_url is None or self.webhook_secret is None:
                raise ValueError("webhook_base_url and webhook_secret are required in webhook mode")
            if self.webhook_base_url.scheme != "https":
                raise ValueError("webhook_base_url must use HTTPS in webhook mode")
            if not _WEBHOOK_SECRET_PATTERN.fullmatch(self.webhook_secret.get_secret_value()):
                raise ValueError("webhook_secret may contain only letters, digits, '_' and '-'")
        return self

    @property
    def webhook_url(self) -> str | None:
        """Return the complete public webhook URL when configured."""
        if self.webhook_base_url is None:
            return None
        return f"{str(self.webhook_base_url).rstrip('/')}{WEBHOOK_PATH}"

    @property
    def webhook_secret_value(self) -> str | None:
        """Return the webhook secret for Telegram registration and verification."""
        if self.webhook_secret is None:
            return None
        return self.webhook_secret.get_secret_value()
