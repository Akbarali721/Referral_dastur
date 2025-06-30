import logging
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.handlers import start, referral, admin_stats
from bot.middlewares.db_session import DBSessionMiddleware
from aiogram.client.default import DefaultBotProperties
# Logger
logging.basicConfig(level=logging.INFO)

# .env orqali token olish
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Bot obyektini yaratish (MUHIM: bu yerda bot = Bot(...) bo'lishi kerak!)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Dispatcher yaratamiz
dp = Dispatcher()

# Routerlarni ulamiz
dp.include_router(start.router)
dp.include_router(referral.router)
dp.include_router(admin_stats.router)

# Middleware ulash
dp.update.middleware(DBSessionMiddleware())

# Asosiy polling funksiyasi
async def main():
    await dp.start_polling(bot)

# Boshlanish nuqtasi
if __name__ == "__main__":
    asyncio.run(main())
