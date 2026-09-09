"""Telegram-бот на aiogram: основной транспорт уведомлений (раздел 8).

Запуск: uv run --extra bot python -m bot.main
"""

import asyncio
import logging

from bot.config import setup_django

setup_django()

from aiogram import Bot, Dispatcher  # noqa: E402
from django.conf import settings  # noqa: E402

from bot.handlers import start, subscriptions  # noqa: E402

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_routers(start.router, subscriptions.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
