from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Авторизация: связываем telegram_id с пользователем. TODO(этап 1)."""
    await message.answer(
        "Сервис поиска потерянных животных.\n"
        "«Следить за районом» — присылать уведомления о новых отметках рядом."
    )
