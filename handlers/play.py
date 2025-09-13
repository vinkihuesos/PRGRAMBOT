import random
import logging
from aiogram import Router, types, Bot, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from config import *
from utils.emoji_games_db import *
router = Router()



async def send_main_menu(bot: Bot, chat_id: int):
    """Отправляет главное меню с кнопками игр."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Emoji-Game", callback_data="emoji_game")],
        [InlineKeyboardButton(text="♠ Poker[soon]", callback_data="poker"),
         InlineKeyboardButton(text="🃏 BlackJack[soon]", callback_data="blackjack")],
        [InlineKeyboardButton(text="🃏 Baccara[soon]", callback_data="baccara")],
        [InlineKeyboardButton(text="⬆ More/Less[soon]", callback_data="more_less")],
        #[InlineKeyboardButton(text="🔮 Magic Cards", callback_data="magic_card")],
    ])
    await bot.send_photo(
        chat_id=chat_id,
        photo=MAIN_GAME_PHOTO_URL,
        reply_markup=keyboard
    )

@router.message(F.text == "🕹Играть")
async def on_play(message: types.Message, bot: Bot):
    await send_main_menu(bot, message.chat.id)

# **🔹 Отправка меню Emoji-Game**
async def send_emoji_game_menu(bot: Bot, chat_id: int):
    all_games = await get_all_games()
    
    # Формируем список кнопок с играми (по одной в строке)
    game_buttons = [
        [InlineKeyboardButton(
            text=f"{game['game_type']} Игра №{game['game_id']} | {game['game_bid']}  PR GRAM ",
            callback_data=f"emogame_{game['game_id']}"
        )] for game in all_games
    ] if all_games else [
        [InlineKeyboardButton(text="Нет активных игр", callback_data="nogames")]
    ]

    # Основные кнопки меню
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=game_buttons + [  # Добавляем кнопки игр
            [InlineKeyboardButton(text="📁 Мои игры", callback_data="mygames")],
            [
                InlineKeyboardButton(text="➕ Создать игру", callback_data="emoji_create_game_wplayer"),
                InlineKeyboardButton(text="➕ Создать игру с ботом", callback_data="emoji_create_game_wbot")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back")],
        ]
    )

    caption = (
        "🎲 *Emoji-Game*\n\n"
        "✍️ [Об игре](https://telegra.ph/Emoji-Game-02-26-3)\n"
        "🔗 [Наш канал](t.me/RandomlyGift)"
    )

    await bot.send_photo(
        chat_id, MAIN_GAME_PHOTO_URL, caption=caption,
        parse_mode="Markdown", reply_markup=keyboard
    )

@router.callback_query(F.data == "nogames")
async def handle_emoji_game(callback: types.CallbackQuery, bot: Bot):
    await callback.answer("❌ Нет активных игр", show_alert=True)
    await callback.answer()

@router.callback_query(F.data == "emoji_game")
async def handle_emoji_game(callback: types.CallbackQuery, bot: Bot):
    await callback.message.delete()
    await send_emoji_game_menu(bot, callback.message.chat.id)
    await callback.answer()

async def send_game_selection_menu(bot: Bot, chat_id: int):
    """Отправляет выбор типа игры."""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=emoji) for emoji in ["🎲", "🏀", "🎳", "⚽", "🎯"]],
        [KeyboardButton(text="❌ Отменить")]
    ], resize_keyboard=True)
    await bot.send_photo(chat_id, MAIN_GAME_PHOTO_URL, caption="➕ Выберите тип игры", reply_markup=keyboard)

@router.message(F.dice)
async def handle_game_choice_wbot(message: types.Message, bot: Bot):
    print(user_mode)

user_mode = {}