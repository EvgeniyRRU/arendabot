"""Development polling entry point."""

import asyncio

from arendabot.adapters.web.app import RuntimeResources
from arendabot.bootstrap.container import build_resources
from arendabot.bootstrap.logging import configure_logging
from arendabot.bootstrap.settings import Settings, UpdateMode


async def run_polling(resources: RuntimeResources, *, drop_pending_updates: bool = False) -> None:
    """Consume Telegram updates through long polling and release resources."""
    try:
        await resources.bot.delete_webhook(drop_pending_updates=drop_pending_updates)
        await resources.dispatcher.start_polling(  # pyright: ignore[reportUnknownMemberType]
            resources.bot,
            close_bot_session=False,
        )
    finally:
        await resources.bot.session.close()
        await resources.engine.dispose()


def main() -> None:
    """Load polling configuration and run until interrupted."""
    settings = Settings()  # pyright: ignore[reportCallIssue]
    if settings.update_mode is not UpdateMode.POLLING:
        raise RuntimeError("arendabot-polling requires ARENDABOT_UPDATE_MODE=polling")
    configure_logging(settings.log_level)
    resources = build_resources(settings)
    asyncio.run(run_polling(resources, drop_pending_updates=settings.drop_pending_updates))


if __name__ == "__main__":
    main()
