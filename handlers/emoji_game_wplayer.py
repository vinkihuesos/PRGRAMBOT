import logging
import random
import asyncio
from datetime import datetime
from aiogram import Router, types, Bot, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.db import *
from utils.emoji_games_db import *
from config import *
from .play import send_game_selection_menu, user_mode
router = Router()
logger = logging.getLogger(__name__)



# Игровое состояние
class GameStateWPlayer(StatesGroup):
    waiting_for_bet = State()
    waiting_for_turn = State()

# Словари для отслеживания пользователей
user_selected_game = {}
user_selected_count = {}
user_last_play_time = {}


# **🔹 Создание игры**
@router.callback_query(F.data == "emoji_create_game_wplayer")
async def handle_create_game_wplayer(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_mode[callback.from_user.id] = "wplayer"
    await callback.message.delete()
    user = await get_user(callback.from_user.id)

    caption = f'''
➕ *Создание игры в* 🎲 *Emoji-Game*

• Мин. Ставка: 5000  PR GRAM 
💰 Ваш баланс: {user["balance"]:,}  PR GRAM 

ℹ️ Введите размер ставки
'''
    await bot.send_photo(callback.message.chat.id, MAIN_GAME_PHOTO_URL, caption=caption,
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 Назад", callback_data="emoji_game")]]),
                         parse_mode="Markdown")
    await state.set_state(GameStateWPlayer.waiting_for_bet)
    await callback.answer()

# **🔹 Обработка ставки**
@router.message(GameStateWPlayer.waiting_for_bet, F.text.isdigit())
async def process_bet_wplayer(message: types.Message, state: FSMContext, bot: Bot):
    amount = int(message.text)
    if not (5000 <= amount):
        await message.answer("❌ *Ставка должна быть от 5000  PR GRAM *", parse_mode="Markdown")
        return

    user = await get_user(message.from_user.id)
    if user['balance'] < amount:
        await message.answer(f"❌ Недостаточно средств, не хватает {amount - user['balance']}  PR GRAM ", parse_mode="Markdown")
        return

    await state.update_data(bet_amount=amount)
    await send_game_selection_menu(bot, message.chat.id)


@router.message(F.text == "❌ Отменить")
async def cancel_game(message: types.Message, state: FSMContext, bot: Bot):
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
@router.message(F.dice, lambda message: user_mode.get(message.chat.id) == "wplayer")
async def handle_game_choice_wplayer(message: types.Message, bot: Bot, state: FSMContext):
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
    await state.set_state(GameStateWPlayer.waiting_for_turn)

@router.message(GameStateWPlayer.waiting_for_turn, F.text)
async def process_turn_count_wplayer(message: types.Message, bot: Bot, state: FSMContext):
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
        user_data = await state.get_data()
        bet_amount = user_data.get("bet_amount")
        user_selected_count[user_id] = f"{emoji}{count}"
        game_id = int(user_id*10/randint(100, 10000))
        await reg_game(user_id, bet_amount, emoji, count, game_id, message.from_user.username)
        await remove_balance(user_id, bet_amount)
        text = f"""
🎲 Emoji-Game №{game_id}

💰 Стaвкa: {bet_amount}  PR GRAM 

✍️ Тип игры: {emoji}
👥 Кoл-вo игрoкoв: 2

ℹ️ Игрa успeшнo сoздaнa
"""
        await bot.send_photo(message.chat.id, photo=MAIN_GAME_PHOTO_URL, caption=text, reply_markup=default_keyboard(message.from_user.id))
        await state.clear()
        del user_selected_count[user_id]
        del user_selected_game[user_id]
        del user_mode[message.from_user.id]
        
    except ValueError:
        await message.answer("❌ Неверный формат. Выберите количество бросков, нажав кнопку.")
    
@router.callback_query(F.data.startswith("emogame_"))
async def start_game(callback: types.CallbackQuery, bot: Bot):
    game_id = callback.data.split("emogame_")[1]
    game = await get_game(int(game_id))
    if callback.from_user.id == game['creator_id']:
        await callback.answer("❌ Нельзя играть с самим собой.", show_alert=True)
        return
    if not game:
        await callback.answer("❌ Игра не найдена.", show_alert=True)
        return

    # Берем данные игроков из базы
    creator = game['username']
    opponent_user = callback.from_user.username

    if not creator or not opponent_user:
        await callback.answer("❌ Ошибка: не удалось загрузить данные игроков.", show_alert=True)
        return
    text = f"""
🎲 Зaпускaeм Emoji-Game №{game_id}

💰 Стaвкa: {game['game_bid']}  PR GRAM 

✍️ Тип игры: {game['game_type']}
👥 Кoл-вo игрoкoв: 2
"""
    opponent = await get_user(callback.from_user.id)
    creator = await get_user(game['creator_id'])
    if opponent['balance'] < game['game_bid']:
        await bot.send_message(callback.from_user.id, "❌ Недостаточно средств для игры.")
        await callback.answer()
        return
    await bot.send_photo(callback.from_user.id, caption=text, photo=MAIN_GAME_PHOTO_URL)
    await bot.send_photo(game["creator_id"], caption=text, photo=MAIN_GAME_PHOTO_URL)
    # Снимаем ставку у обоих игроков
    await remove_balance(callback.from_user.id, game['game_bid'])
    await delete_game(int(game_id))
    creator = game['username']
    opponent_user = callback.from_user.username
    await play_game_wplayer(
        bot, game['creator_id'], callback.from_user.id, 
        game['game_bid'], game['game_type'], game['game_emoji_count'], 
        creator, opponent_user
    )

# Игра между двумя игроками
async def play_game_wplayer(
    bot: Bot, creator_id: int, opponent_id: int, 
    game_bid: int, emoji: str, count: int, 
    creator_username: str, opponent_username: str
):
    # Получаем информацию о пользователях
    opponent = await get_user(opponent_id)
    creator = await get_user(creator_id)

    # Запуск игры (получаем 3 значения)
    creator_total, opponent_total, rolled_dices = await send_game_turn(
        bot, creator_id, opponent_id, emoji, count, creator_username, opponent_username
    )

    await bot.send_message(creator_id, "Ждем итогов игры 🔥")
    await bot.send_message(opponent_id, "Ждем итогов игры 🔥")
    await asyncio.sleep(4)

    # Определение победителя
    await determine_winner(
        bot, creator_id, opponent_id, game_bid, 
        creator_total, opponent_total, 
        creator_username, opponent_username, rolled_dices
    )


async def send_game_turn(
    bot: Bot, creator_id: int, opponent_id: int, emoji: str, count: int, 
    creator_username: str, opponent_username: str
):
    creator_total, opponent_total = 0, 0
    rolled_dices = []

    # Уведомление о ходе создателя
    await bot.send_message(creator_id, f"👀 Ход @{creator_username}")
    await bot.send_message(opponent_id, f"👀 Ход @{creator_username}")

    # Бросаем дайсы для создателя и пересылаем их оппоненту
    for _ in range(count):
        dice_message = await bot.send_dice(creator_id, emoji=emoji)  # Бросаем дайс у создателя

        dice_value = dice_message.dice.value  # Получаем значение броска
        rolled_dices.append(dice_value)
        creator_total += dice_value

        # Пересылаем дайс оппоненту
        await bot.forward_message(opponent_id, creator_id, dice_message.message_id)

    # Уведомление о ходе оппонента
    await bot.send_message(creator_id, f"👀 Ход @{opponent_username}")
    await bot.send_message(opponent_id, f"👀 Ход @{opponent_username}")

    # Бросаем дайсы для оппонента и пересылаем их создателю
    for _ in range(count):
        dice_message = await bot.send_dice(opponent_id, emoji=emoji)  # Бросаем дайс у оппонента

        dice_value = dice_message.dice.value  # Получаем значение броска
        rolled_dices.append(dice_value)
        opponent_total += dice_value

        # Пересылаем дайс создателю
        await bot.forward_message(creator_id, opponent_id, dice_message.message_id)

    return creator_total, opponent_total, rolled_dices



# Определение победителя
async def determine_winner(
    bot: Bot, creator_id: int, opponent_id: int, game_bid: int, 
    creator_total: int, opponent_total: int, 
    creator_username: str, opponent_username: str, rolled_dices: list
):
    if opponent_total > creator_total:
        winner_id, loser_id = opponent_id, creator_id
        winner_username, loser_username = opponent_username, creator_username
        outcome_winner, outcome_loser = "🥇 Вы победили!", "😞 Вы проиграли"
    elif opponent_total < creator_total:
        winner_id, loser_id = creator_id, opponent_id
        winner_username, loser_username = creator_username, opponent_username
        outcome_winner, outcome_loser = "🥇 Вы победили!", "😞 Вы проиграли"
    else:
        # Ничья
        await update_balance(opponent_id, game_bid)
        await update_balance(creator_id, game_bid)
        await add_dwaw(opponent_id)  
        await add_dwaw(creator_id)  

        text = f"""
📊 Результат игры
🎲 @{opponent_username} [{opponent_total}]
🎲 @{creator_username} [{creator_total}]

🤝 Ничья!
💰 Ставка возвращена: {game_bid}  PR GRAM 
"""
        await bot.send_photo(chat_id=creator_id, caption=text, photo=MAIN_GAME_PHOTO_URL)
        await bot.send_photo(chat_id=opponent_id, caption=text, photo=MAIN_GAME_PHOTO_URL)
        return

    # Победитель получает приз
    reward = int(game_bid * 1.95)
    await update_balance(winner_id, reward)
    await add_win(winner_id)
    await add_loss(loser_id)

    text_winner = f"""
📊 Результат игры
🎲 @{opponent_username} [{opponent_total}]
🎲 @{creator_username} [{creator_total}]

👀 {outcome_winner}
💰 Выигрыш: {reward}  PR GRAM 
"""

    text_loser = f"""
📊 Результат игры
🎲 @{opponent_username} [{opponent_total}]
🎲 @{creator_username} [{creator_total}]

👀 {outcome_loser}
"""

    await bot.send_photo(chat_id=winner_id, caption=text_winner, photo=MAIN_GAME_PHOTO_URL)
    await bot.send_photo(chat_id=loser_id, caption=text_loser, photo=MAIN_GAME_PHOTO_URL)
