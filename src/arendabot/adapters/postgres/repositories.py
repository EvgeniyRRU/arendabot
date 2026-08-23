"""SQLAlchemy repository implementations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arendabot.adapters.postgres.models import TelegramUserModel
from arendabot.application.ports import TelegramUserRepository
from arendabot.domain.telegram_user import TelegramUser


class SqlAlchemyTelegramUserRepository(TelegramUserRepository):
    """Persist Telegram users through an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> TelegramUser | None:
        statement = select(TelegramUserModel).where(TelegramUserModel.telegram_id == telegram_id)
        model = await self._session.scalar(statement)
        return None if model is None else _to_domain(model)

    async def save(self, user: TelegramUser) -> None:
        await self._session.merge(_to_model(user))


def _to_domain(model: TelegramUserModel) -> TelegramUser:
    return TelegramUser(
        id=model.id,
        telegram_id=model.telegram_id,
        username=model.username,
        first_name=model.first_name,
        last_name=model.last_name,
        language_code=model.language_code,
        is_bot=model.is_bot,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_model(user: TelegramUser) -> TelegramUserModel:
    return TelegramUserModel(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_bot=user.is_bot,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
