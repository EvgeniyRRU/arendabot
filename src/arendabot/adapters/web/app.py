"""FastAPI application and Telegram webhook adapter."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from json import JSONDecodeError
from secrets import compare_digest

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine

from arendabot.adapters.postgres.database import ReadinessProbe
from arendabot.bootstrap.logging import configure_logging
from arendabot.bootstrap.settings import WEBHOOK_PATH, Settings, UpdateMode

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeResources:
    """Runtime objects owned by an application process."""

    bot: Bot
    dispatcher: Dispatcher
    engine: AsyncEngine
    readiness: ReadinessProbe


def create_app(
    settings: Settings | None = None,
    *,
    resources: RuntimeResources | None = None,
) -> FastAPI:
    """Create a fully wired ASGI application."""
    resolved_settings = settings or Settings()  # pyright: ignore[reportCallIssue]
    configure_logging(resolved_settings.log_level)
    if resources is None:
        from arendabot.bootstrap.container import build_resources

        resources = build_resources(resolved_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        dispatcher_started = False
        try:
            await resources.dispatcher.emit_startup(bot=resources.bot)
            dispatcher_started = True
            if resolved_settings.update_mode is UpdateMode.WEBHOOK:
                webhook_url = resolved_settings.webhook_url
                webhook_secret = resolved_settings.webhook_secret_value
                if webhook_url is None or webhook_secret is None:
                    raise RuntimeError("webhook settings were not validated")
                await resources.bot.set_webhook(
                    url=webhook_url,
                    secret_token=webhook_secret,
                    allowed_updates=resources.dispatcher.resolve_used_update_types(),
                )
            yield
        finally:
            try:
                if dispatcher_started:
                    await resources.dispatcher.emit_shutdown(bot=resources.bot)
            finally:
                try:
                    await resources.bot.session.close()
                finally:
                    await resources.engine.dispose()

    app = FastAPI(title="arendabot", lifespan=lifespan)

    @app.get("/health/live")
    async def liveness() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"status": "ok"}

    @app.get("/health/ready", response_model=None)
    async def readiness() -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
        ready = await resources.readiness.is_ready()
        return JSONResponse(
            status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "ok" if ready else "unavailable"},
        )

    @app.post(WEBHOOK_PATH, status_code=status.HTTP_200_OK)
    async def telegram_webhook(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        secret_token: str | None = Header(
            default=None,
            alias="X-Telegram-Bot-Api-Secret-Token",
        ),
    ) -> Response:
        expected_secret = resolved_settings.webhook_secret_value
        if (
            secret_token is None
            or expected_secret is None
            or not compare_digest(secret_token, expected_secret)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        try:
            payload = await request.json()
            update = Update.model_validate(payload, context={"bot": resources.bot})
        except (JSONDecodeError, ValidationError) as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST) from error

        try:
            await resources.dispatcher.feed_update(resources.bot, update)
        except Exception as error:
            logger.exception(
                "Telegram update dispatch failed", extra={"update_id": update.update_id}
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from error
        return Response(status_code=status.HTTP_200_OK)

    return app
