import pytest
from pydantic import ValidationError

from arendabot.bootstrap.settings import Settings, UpdateMode

BASE_SETTINGS = {
    "bot_token": "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
    "database_url": "postgresql+asyncpg://postgres:postgres@localhost/arendabot",
}


def test_polling_settings_do_not_require_webhook_values() -> None:
    settings = Settings(**BASE_SETTINGS, update_mode=UpdateMode.POLLING, _env_file=None)

    assert settings.webhook_url is None


def test_webhook_settings_require_url_and_secret() -> None:
    with pytest.raises(ValidationError, match="webhook_base_url and webhook_secret"):
        Settings(**BASE_SETTINGS, update_mode=UpdateMode.WEBHOOK, _env_file=None)


def test_webhook_url_uses_the_fixed_endpoint() -> None:
    settings = Settings(
        **BASE_SETTINGS,
        update_mode=UpdateMode.WEBHOOK,
        webhook_base_url="https://bot.example.com/base/",
        webhook_secret="valid_secret-123",
        _env_file=None,
    )

    assert settings.webhook_url == "https://bot.example.com/base/telegram/webhook"


def test_webhook_secret_rejects_unsupported_characters() -> None:
    with pytest.raises(ValidationError, match="letters, digits"):
        Settings(
            **BASE_SETTINGS,
            update_mode=UpdateMode.WEBHOOK,
            webhook_base_url="https://bot.example.com",
            webhook_secret="not valid!",
            _env_file=None,
        )
