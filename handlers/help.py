import logging
from aiogram import Router, Bot, types, F
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == 'ℹПомощь')
async def handle_profile(message: types.Message, bot: Bot):
    photo=MAIN_HELP_IMG
    # Отправляем сообщение пользователю
    keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋Правила", url=f"https://telegra.ph/Pravila-proekta-02-23-2")],
                [InlineKeyboardButton(text="✍Соглашение", url=f"https://telegra.ph/Polzovatelskoe-soglashenie-02-23-10")]
            ]
        )
    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=photo,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
