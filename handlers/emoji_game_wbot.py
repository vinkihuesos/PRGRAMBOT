import logging
import random
import asyncio
from datetime import datetime
from aiogram import Router, types, Bot, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.db import *
from config import *
from .play import send_game_selection_menu, user_mode
router = Router()
logger = logging.getLogger(__name__)



# Игровое состояние
class GameState(StatesGroup):
    waiting_for_bet = State()
    waiting_for_turn = State()

# Словари для отслеживания пользователей
user_selected_game = {}
user_selected_count = {}
user_last_play_time = {}


# **🔹 Создание игры**
@router.callback_query(F.data == "emoji_create_game_wbot")
async def handle_create_game_wbot(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_mode[callback.from_user.id] = "wbot"
    await callback.message.delete()
    user = await get_user(callback.from_user.id)

    caption = f'''
➕ *Создание игры в* 🎲 *Emoji-Game*

• Мин. Ставка: 5.000  PR GRAM 
• Макс. Ставка: 500.000  PR GRAM 
💰 Ваш баланс: {user["balance"]:,}  PR GRAM 

ℹ️ Введите размер ставки
'''
    await bot.send_photo(callback.message.chat.id, MAIN_GAME_PHOTO_URL, caption=caption,
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 Назад", callback_data="emoji_game")]]),
                         parse_mode="Markdown")
    await state.set_state(GameState.waiting_for_bet)
    await callback.answer()

# **🔹 Обработка ставки**
@router.message(GameState.waiting_for_bet, F.text.isdigit())
async def process_bet_wbot(message: types.Message, state: FSMContext, bot: Bot):
    amount = int(message.text)
    if not (5000 <= amount <= 500000):
        await message.answer("❌ *Ставка должна быть от 5.000 до 500.000 PR GRAM*", parse_mode="Markdown")
        return

    user = await get_user(message.from_user.id)
    if user['balance'] < amount:
        await message.answer(f"❌ Недостаточно средств, не хватает {amount - user['balance']}  PR GRAM ", parse_mode="Markdown")
        return

    await state.update_data(bet_amount=amount)
    await send_game_selection_menu(bot, message.chat.id)

@router.message(F.text == "❌ Отменить", lambda message: user_mode.get(message.chat.id) == "wbot")
async def cancel_game_wbot(message: types.Message, state: FSMContext, bot: Bot):
    """Отмена игры."""
    await bot.send_message(message.chat.id, text='❌', reply_markup=default_keyboard(message.from_user.id))
    await state.clear()
    await users_collection.update_one({"user_id": message.chat.id}, {"$set": {"is_played": False}})
    user_id = message.chat.id
    if user_id in user_selected_game:
        del user_selected_game[user_id]
        print(f'{user_selected_game} очищен {user_id}')
    if user_id in user_selected_count:
        del user_selected_count[user_id]
        print(f'{user_selected_count} очищен {user_id}')
    if user_id in user_mode:
        del user_mode[user_id]
    from .play import send_main_menu
    await send_main_menu(bot, message.chat.id)

# **🔹 Обработка выбора игры**
@router.message(F.dice, lambda message: user_mode.get(message.chat.id) == "wbot")
async def handle_game_choice_wbot(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.chat.id
    emoji = message.dice.emoji

    if user_id in user_selected_game:
        await message.answer("Вы уже выбрали игру!", show_alert=True)
        return

    user_selected_game[user_id] = emoji
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=f"{emoji}{i}") for i in range(1, 6)],
        [KeyboardButton(text="❌ Отменить")]
    ], resize_keyboard=True)
    
    await message.answer(f"\n{emoji} Укажите количество бросков", reply_markup=keyboard)
    await state.set_state(GameState.waiting_for_turn)

@router.message(GameState.waiting_for_turn, F.text)
async def process_turn_count_wbot(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.chat.id
    try:
        if user_id in user_selected_count:
            await message.answer("❌ Вы уже выбрали количество эмодзи")
            return
        emoji = message.text[0]
        count = int(message.text[1:])
        if count not in range(1, 6):
            await message.answer("❌ Неверное количество бросков.")
            return
        
        await state.update_data(turn_count=count)
        user_id = message.chat.id
        user_selected_count[user_id] = f"{emoji}{count}"
        await play_game_wbot(message, bot, state, user_id, emoji, count)
    except ValueError:
        await message.answer("❌ Неверный формат. Выберите количество бросков, нажав кнопку.")

# **🔹 Игровой процесс**
async def play_game_wbot(message: types.Message, bot: Bot, state: FSMContext, user_id: int, emoji: str, count: int):
    user_data = await state.get_data()
    bet_amount = user_data.get("bet_amount")

    user = await get_user(user_id)
    if user['balance'] < bet_amount:
        await message.answer("❌ Недостаточно средств для игры.")
        return

    await remove_balance(user_id, bet_amount)
    user_last_play_time[user_id] = datetime.now()
    await state.clear()

    bot_total, player_total = await send_game_turn_wbot(bot, message, emoji, count)

    await message.answer("Ждем итогов игры 🔥")
    await asyncio.sleep(4)

    await determine_winner_wbot(message, bot, user_id, bet_amount, player_total, bot_total, emoji)

async def send_game_turn_wbot(bot: Bot, message: types.Message, emoji: str, count: int):
    player_total, bot_total = 0, 0
    await message.answer(f"""
👀 Ход @{message.from_user.username}
            
⬇️⬇️⬇️⬇️⬇️
""", reply_markup=default_keyboard(message.from_user.id))
    for _ in range(count):
        player_dice = await bot.send_dice(message.chat.id, emoji=emoji)
        player_total += player_dice.dice.value
    await message.answer(f"""
👀 Ход @{BOT_USERNAME}
            
⬇️⬇️⬇️⬇️⬇️
""")
    for _ in range(count):
        bot_dice = await bot.send_dice(message.chat.id, emoji=emoji)
        bot_total += bot_dice.dice.value

    return bot_total, player_total

async def determine_winner_wbot(message: types.Message, bot: Bot, user_id: int, bet_amount: int, player_total: int, bot_total: int, emoji: str):
    if player_total > bot_total:
        reward = int(bet_amount * 1.8)
        await update_balance(user_id, reward)
        outcome = "🥇 Вы победили!"
        await add_win(user_id)
    elif player_total < bot_total:
        reward = 0
        outcome = "😞 Бот победил!"
        await add_loss(user_id)
    else:
        reward = bet_amount  # Возвращаем ставку в случае ничьи
        await update_balance(user_id, reward)
        outcome = "🤝 Ничья!"
        await add_dwaw(user_id)

    text=f"""
📊 Результат игры
{emoji} @{message.from_user.username} [{player_total}]
{emoji} @{BOT_USERNAME} [{bot_total}]

👀 {outcome}
💰 Выигрыш: {reward}  PR GRAM """
    await bot.send_photo(message.chat.id, MAIN_GAME_PHOTO_URL, caption=text, reply_markup=default_keyboard(message.from_user.id))
    del user_selected_count[user_id]
    del user_selected_game[user_id]
    del user_mode[message.from_user.id]
