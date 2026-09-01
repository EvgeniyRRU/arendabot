"""Composition root for runtime dependencies."""

from aiogram import Bot, Dispatcher

from arendabot.adapters.postgres.database import (
    SqlAlchemyReadinessProbe,
    create_engine,
)
from arendabot.adapters.telegram.router import create_router
from arendabot.adapters.web.app import RuntimeResources
from arendabot.bootstrap.settings import Settings


def build_resources(settings: Settings) -> RuntimeResources:
    """Construct process-owned runtime resources."""
    bot = Bot(token=settings.bot_token.get_secret_value())
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router())
    engine = create_engine(settings.database_url, echo=settings.database_echo)
    return RuntimeResources(
        bot=bot,
        dispatcher=dispatcher,
        engine=engine,
        readiness=SqlAlchemyReadinessProbe(engine),
    )
