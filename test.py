import asyncio
from aiogram import Bot, Dispatcher, types
from config import API_TOKEN_TEST

bot = Bot(token=API_TOKEN_TEST)
dp = Dispatcher()

@dp.message()
async def echo(message: types.Message):
    print(message.chat.id)
    await message.answer(message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
