import logging
import random
from aiogram import Router, Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from utils.db import get_user, update_balance, remove_balance
from config import *
router = Router()
logger = logging.getLogger(__name__)

MAGIC_CARD_COST = 75

CARD_PRICES = {
    "card1": 15, "card2": 20, "card3": 25, "card4": 25,
    "card5": 50, "card6": 50, "card7": 75, "card8": 150, "card9": 250,
}

CARD_IMAGES = {
    "card1": "https://media.discordapp.net/attachments/1342809094444023850/1343259440710684692/photo_4_2025-02-23_18-39-58.jpg?ex=67c3df97&is=67c28e17&hm=637a090439937abb6a8c2400c57ba935320d584ab7e81b1928c22454285f02c8&=&format=webp&width=994&height=559",
    "card2": "https://media.discordapp.net/attachments/1342809094444023850/1343259806642999368/photo_2025-02-23_18-47-08.jpg?ex=67c3dfee&is=67c28e6e&hm=d4e57c1047c7241700aa6c94b3f484668302e7e68dcd296c62f82073a67f0d99&=&format=webp&width=994&height=559",
    "card3": "https://media.discordapp.net/attachments/1342809094444023850/1343259439817297920/photo_1_2025-02-23_18-39-58.jpg?ex=67c3df97&is=67c28e17&hm=adffdbab18223db2528d575ac82ac91a709bf1b5b00d2536cffe10b3c87f1033&=&format=webp&width=994&height=559",
    "card4": "https://media.discordapp.net/attachments/1342809094444023850/1343259439817297920/photo_1_2025-02-23_18-39-58.jpg?ex=67c3df97&is=67c28e17&hm=adffdbab18223db2528d575ac82ac91a709bf1b5b00d2536cffe10b3c87f1033&=&format=webp&width=994&height=559",
    "card5": "https://media.discordapp.net/attachments/1342809094444023850/1343259440463347775/photo_3_2025-02-23_18-39-58.jpg?ex=67c3df97&is=67c28e17&hm=59a7f3f410dc05254cb6b5930fcb3d2207a4fa949b729000df875f704f646823&=&format=webp&width=994&height=559",
    "card6": "https://media.discordapp.net/attachments/1342809094444023850/1343259440463347775/photo_3_2025-02-23_18-39-58.jpg?ex=67c3df97&is=67c28e17&hm=59a7f3f410dc05254cb6b5930fcb3d2207a4fa949b729000df875f704f646823&=&format=webp&width=994&height=559",
    "card7": "https://media.discordapp.net/attachments/1342809094444023850/1343259441281236992/photo_6_2025-02-23_18-39-58.jpg?ex=67c3df97&is=67c28e17&hm=bddb102aedeb76e64ac6ce4187a382fa8ee4052faa8742d76724bd99296c33bf&=&format=webp&width=994&height=559",
    "card8": "https://media.discordapp.net/attachments/1342809094444023850/1343259440123478098/photo_2_2025-02-23_18-39-58.jpg?ex=67c3df97&is=67c28e17&hm=ddc9985e0714931c6282887511af57f7a984a7518b6583223f8c38bbc584436e&=&format=webp&width=994&height=559",
    "card9": "https://media.discordapp.net/attachments/1342809094444023850/1343658985332670594/photo_2025-02-24_21-52-37.jpg?ex=67c40232&is=67c2b0b2&hm=08f19cfa645c096cc156d47eb77981674d074d3d633a8806f5600c061bc60bd6&=&format=webp&width=994&height=559",
}

user_selected = {}

async def send_magic_cards_menu(bot: Bot, chat_id: int):
    """Отправляет меню Magic Cards"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать игру", callback_data="card_create_game")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    caption = (
        "🔮 *Magic Cards*\n\n"
        "✍️ Об игре: [перейти](https://telegra.ph/Igra-s-kartochkami-02-23)\n"
        "🔗 Наш канал: [перейти](https://t.me/RandomlyGift)\n"
        "⚙ *Игра против бота*\n"
        f'ℹ *Нажимая "Создать игру", с вашего баланса спишется {MAGIC_CARD_COST} PR GRAM *'
    )
    await bot.send_photo(
        chat_id=chat_id, photo=MAGIC_CARD_PHOTO_URL,
        caption=caption, parse_mode="Markdown", reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "magic_card")
async def handle_magic_card(callback: types.CallbackQuery, bot: Bot):
    """Обработчик кнопки '🔮 Magic Cards'"""
    await callback.message.delete()
    await send_magic_cards_menu(bot, callback.message.chat.id)
    await callback.answer()

@router.callback_query(lambda c: c.data == "card_create_game")
async def handle_card_create_game(callback: types.CallbackQuery, bot: Bot):
    """Создание игры, проверка баланса и запуск игрового поля"""
    user = await get_user(callback.from_user.id)
    if user["balance"] < MAGIC_CARD_COST:
        await callback.answer(f"❌ Вам не хватает {MAGIC_CARD_COST - user['balance']}  PR GRAM  для запуска игры")
        return

    await remove_balance(user["user_id"], MAGIC_CARD_COST)
    await send_magic_cards_game(bot, callback.message.chat.id)
    await callback.answer()

def get_random_cards():
    """Возвращает перемешанный список карт"""
    card_ids = list(CARD_IMAGES.keys())
    random.shuffle(card_ids)
    return card_ids

async def send_magic_cards_game(bot: Bot, chat_id: int):
    """Отправляет игровое поле из 9 карт"""
    card_ids = get_random_cards()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬛", callback_data=card_ids[i + j]) for j in range(3)]
        for i in range(0, 9, 3)
    ])
    await bot.send_photo(chat_id=chat_id, caption="Выберите карту:", reply_markup=keyboard, photo=MAGIC_CARD_PHOTO_URL_INVISIBLE)

@router.callback_query(lambda c: c.data in CARD_IMAGES.keys())
async def card_callback_handler(callback: types.CallbackQuery, bot: Bot):
    """Обработчик выбора карты"""
    user_id = callback.from_user.id
    selected_card = callback.data

    if user_id in user_selected:
        await callback.answer("Вы уже выбрали подарок!", show_alert=True)
        return

    user_selected[user_id] = selected_card
    card_price = CARD_PRICES.get(selected_card, 0)
    image_url = CARD_IMAGES.get(selected_card, "")

    await update_balance(user_id, card_price)
    user = await get_user(user_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Еще!", callback_data="repeat_btn")]
    ])
    await callback.message.delete()
    await bot.send_photo(
        chat_id=callback.message.chat.id, photo=image_url, reply_markup=keyboard,
        caption=f"📊 *Результат игры*\n\n💰 *Выигрыш:* {card_price}  PR GRAM \n💸 *Баланс:* {user['balance']}  PR GRAM \n🌟 *Игра:* Magic Cards",
        parse_mode="Markdown"
    )

    del user_selected[user_id]
    await callback.answer()

@router.callback_query(lambda c: c.data == "back")
async def handle_back(callback: types.CallbackQuery, bot: Bot):
    """Возвращает в главное меню"""
    from .play import send_main_menu
    await callback.message.delete()
    await send_main_menu(bot, callback.message.chat.id)
    await callback.answer()

@router.callback_query(lambda c: c.data == "repeat_btn")
async def handle_repeat(callback: types.CallbackQuery, bot: Bot):
    """Запускает игру заново"""
    user = await get_user(callback.from_user.id)
    if user["balance"] < MAGIC_CARD_COST:
        await callback.answer(f"❌ Вам не хватает {MAGIC_CARD_COST - user['balance']}  PR GRAM  для запуска игры")
        return
    await remove_balance(user["user_id"], MAGIC_CARD_COST)
    await send_magic_cards_game(bot, callback.message.chat.id)
    await callback.answer()
