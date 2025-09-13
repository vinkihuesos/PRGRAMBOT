import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import API_TOKEN, API_TOKEN_TEST  
from handlers import register_all_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def main():
    logging.info("Запуск бота...")

    async with Bot(token=API_TOKEN) as bot:
        dp = Dispatcher()

        register_all_handlers(dp)

        logging.info("Бот успешно запущен. Ожидание сообщений...")
        
        await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот был остановлен вручную.")
