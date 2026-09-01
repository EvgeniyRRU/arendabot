from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from arendabot.adapters.web.app import RuntimeResources, create_app
from arendabot.bootstrap.settings import Settings, UpdateMode

VALID_UPDATE = {
    "update_id": 1,
    "message": {
        "message_id": 10,
        "date": 0,
        "chat": {"id": 42, "type": "private"},
        "from": {"id": 42, "is_bot": False, "first_name": "Test"},
        "text": "/start",
    },
}


class FakeReadinessProbe:
    def __init__(self, ready: bool) -> None:
        self.ready = ready

    async def is_ready(self) -> bool:
        return self.ready


def make_settings() -> Settings:
    return Settings(
        bot_token="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
        database_url="postgresql+asyncpg://postgres:postgres@localhost/arendabot",
        update_mode=UpdateMode.WEBHOOK,
        webhook_base_url="https://bot.example.com",
        webhook_secret="valid_secret-123",
        _env_file=None,
    )


def make_resources(*, ready: bool = True) -> RuntimeResources:
    session = SimpleNamespace(close=AsyncMock())
    bot = SimpleNamespace(set_webhook=AsyncMock(return_value=True), session=session)
    dispatcher = SimpleNamespace(
        feed_update=AsyncMock(return_value=None),
        emit_startup=AsyncMock(),
        emit_shutdown=AsyncMock(),
        resolve_used_update_types=lambda: ["message"],
    )
    engine = SimpleNamespace(dispose=AsyncMock())
    return RuntimeResources(
        bot=bot,
        dispatcher=dispatcher,
        engine=engine,
        readiness=FakeReadinessProbe(ready),
    )


async def request(app: object, method: str, path: str, **kwargs: object):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.request(method, path, **kwargs)


async def test_liveness_is_process_only() -> None:
    app = create_app(make_settings(), resources=make_resources(ready=False))

    response = await request(app, "GET", "/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(("ready", "status_code"), [(True, 200), (False, 503)])
async def test_readiness_reflects_database_state(ready: bool, status_code: int) -> None:
    app = create_app(make_settings(), resources=make_resources(ready=ready))

    response = await request(app, "GET", "/health/ready")

    assert response.status_code == status_code


async def test_webhook_rejects_a_missing_or_wrong_secret() -> None:
    app = create_app(make_settings(), resources=make_resources())

    missing = await request(app, "POST", "/telegram/webhook", json=VALID_UPDATE)
    wrong = await request(
        app,
        "POST",
        "/telegram/webhook",
        json=VALID_UPDATE,
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )

    assert missing.status_code == 403
    assert wrong.status_code == 403


async def test_webhook_rejects_a_malformed_update() -> None:
    app = create_app(make_settings(), resources=make_resources())

    response = await request(
        app,
        "POST",
        "/telegram/webhook",
        json={"not": "an update"},
        headers={"X-Telegram-Bot-Api-Secret-Token": "valid_secret-123"},
    )

    assert response.status_code == 400


async def test_webhook_dispatches_a_valid_update() -> None:
    resources = make_resources()
    app = create_app(make_settings(), resources=resources)

    response = await request(
        app,
        "POST",
        "/telegram/webhook",
        json=VALID_UPDATE,
        headers={"X-Telegram-Bot-Api-Secret-Token": "valid_secret-123"},
    )

    assert response.status_code == 200
    resources.dispatcher.feed_update.assert_awaited_once()


async def test_webhook_returns_500_when_dispatch_fails() -> None:
    resources = make_resources()
    resources.dispatcher.feed_update.side_effect = RuntimeError("dispatch failed")
    app = create_app(make_settings(), resources=resources)

    response = await request(
        app,
        "POST",
        "/telegram/webhook",
        json=VALID_UPDATE,
        headers={"X-Telegram-Bot-Api-Secret-Token": "valid_secret-123"},
    )

    assert response.status_code == 500


async def test_lifespan_registers_webhook_and_closes_resources() -> None:
    settings = make_settings()
    resources = make_resources()
    app = create_app(settings, resources=resources)

    async with app.router.lifespan_context(app):
        resources.dispatcher.emit_startup.assert_awaited_once()
        resources.bot.set_webhook.assert_awaited_once_with(
            url="https://bot.example.com/telegram/webhook",
            secret_token="valid_secret-123",
            allowed_updates=["message"],
        )

    resources.dispatcher.emit_shutdown.assert_awaited_once()
    resources.bot.session.close.assert_awaited_once()
    resources.engine.dispose.assert_awaited_once()


async def test_lifespan_cleans_up_when_webhook_registration_fails() -> None:
    resources = make_resources()
    resources.bot.set_webhook.side_effect = RuntimeError("Telegram unavailable")
    app = create_app(make_settings(), resources=resources)

    with pytest.raises(RuntimeError, match="Telegram unavailable"):
        async with app.router.lifespan_context(app):
            pass

    resources.dispatcher.emit_shutdown.assert_awaited_once()
    resources.bot.session.close.assert_awaited_once()
    resources.engine.dispose.assert_awaited_once()


async def test_lifespan_closes_resources_when_shutdown_hook_fails() -> None:
    resources = make_resources()
    resources.dispatcher.emit_shutdown.side_effect = RuntimeError("shutdown failed")
    app = create_app(make_settings(), resources=resources)

    with pytest.raises(RuntimeError, match="shutdown failed"):
        async with app.router.lifespan_context(app):
            pass

    resources.bot.session.close.assert_awaited_once()
    resources.engine.dispose.assert_awaited_once()
