from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.db import get_balance
from config import MAIN_WALLET_PHOTO_URL

router = Router()

@router.message(lambda message: message.text == "👛Кошелёк")
async def on_wallet(message: types.Message):
    """Отправляет пользователю его баланс и предлагает методы пополнения"""
    balance = await get_balance(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Пополнить баланс PRGRAM", callback_data="dep")],
        # [InlineKeyboardButton(text="💰 Пополнить баланс CryptoBot", callback_data="depcb")],
        [InlineKeyboardButton(text="💳 Вывод", callback_data="with")],
    ])
    
    photo_url = MAIN_WALLET_PHOTO_URL
    
    await message.answer_photo(
        photo=photo_url,
        reply_markup=keyboard,
        caption=f"💰 *Кошелек*\n\n💸 *Баланс:* {balance:,}  PR GRAM ",
        parse_mode="Markdown"
    )
