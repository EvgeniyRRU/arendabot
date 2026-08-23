from types import SimpleNamespace
from unittest.mock import AsyncMock

from arendabot.adapters.web.app import RuntimeResources
from arendabot.bootstrap.polling import run_polling


async def test_polling_removes_webhook_and_closes_resources() -> None:
    session = SimpleNamespace(close=AsyncMock())
    bot = SimpleNamespace(delete_webhook=AsyncMock(return_value=True), session=session)
    dispatcher = SimpleNamespace(start_polling=AsyncMock())
    engine = SimpleNamespace(dispose=AsyncMock())
    resources = RuntimeResources(
        bot=bot,
        dispatcher=dispatcher,
        engine=engine,
        readiness=SimpleNamespace(),
    )

    await run_polling(resources)

    bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=False)
    dispatcher.start_polling.assert_awaited_once_with(bot, close_bot_session=False)
    bot.session.close.assert_awaited_once()
    engine.dispose.assert_awaited_once()
