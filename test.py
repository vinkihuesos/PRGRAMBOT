import random
from aiogram import Bot, Dispatcher, types
from aiogram.enums import DiceEmoji
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from config import API_TOKEN_TEST

# Здесь замени 'YOUR_API_TOKEN' на свой API-ключ от @BotFather
API_TOKEN = 'токен'

bot = Bot(token=API_TOKEN_TEST)
dp = Dispatcher()

@dp.message(Command("dice"))
async def roll_dice(message: Message):
    data = await message.answer_dice(emoji=DiceEmoji.DICE)
    await message.answer(f'значение кубика {data.dice.value}')

@dp.message(Command("dart"))
async def roll_dart(message: Message):
    data = await message.answer_dice(emoji=DiceEmoji.DART)
    await message.answer(f'значение дартс {data.dice.value}')

@dp.message(Command("bask"))
async def roll_basketball(message: Message):
    data = await message.answer_dice(emoji=DiceEmoji.BASKETBALL)
    await message.answer(f'значение баскет {data.dice.value}')

@dp.message(Command("foot"))
async def roll_football(message: Message):
    data = await message.answer_dice(emoji=DiceEmoji.FOOTBALL)
    await message.answer(f'значение футбол {data.dice.value}')

@dp.message(Command("bowl"))
async def roll_bowling(message: Message):
    data = await message.answer_dice(emoji=DiceEmoji.BOWLING)
    await message.answer(f'значение боулинг {data.dice.value}')

@dp.message(Command("slot"))
async def roll_slot(message: Message):
    data = await message.answer_dice(emoji=DiceEmoji.SLOT_MACHINE)
    await message.answer(f'значение слоты {data.dice.value}')

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())