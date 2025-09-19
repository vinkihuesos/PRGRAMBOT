from aiogram import Router, types, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from datetime import datetime, timedelta
from utils.db import get_user, update_balance, users_collection
from config import BOT_USERNAME, MAIN_GAME_PHOTO_URL, BOT_USERNAME_TEST

router = Router()

@router.message(F.text == "Заработать PR GRAM")
async def earn_prgram_menu(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    # Проверяем доступность бонусов
    #can_claim_daily, daily_streak = await can_claim_daily_bonus(user_id)
    сcan_claim_game_bonus = await can_claim_game_bonus(user_id)
    сcan_claim_username_bonus = await can_claim_username_bonus(user_id, message.from_user.username, message.from_user.full_name)
    
    text = f"""
💰 *Способы заработка PR GRAM*

Выберите способ заработка:

1. 🎯 *Реферальная система*
   - Получайте 1000 PR GRAM за каждого приглашенного друга
   - 💰 Доход: 1000 PR GRAM за реферала

2. 🎮 *Ежедневный игровой бонус*
   - Получайте 2500 PR GRAM каждые 24 часа
   - 🎯 Условие: сыграть минимум 1 игру за день
   - {'✅ Доступно сейчас' if сcan_claim_game_bonus else '⏳ Недоступно'}

3. 📝 *Бонус за упоминание*
   - Получайте 1500 PR GRAM один раз
   - 📌 Условие: указать в username/имени/био ссылку на проект
   - {'✅ Доступно' if сcan_claim_username_bonus else '❌ Не выполнено'}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Реферальная система", callback_data="earn_referral")],
        [InlineKeyboardButton(text="🎮 Ежедневный игровой бонус", callback_data="earn_game_bonus")],
        [InlineKeyboardButton(text="📝 Бонус за упоминание", callback_data="earn_username_bonus")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

    await bot.send_photo(message.chat.id, MAIN_GAME_PHOTO_URL, caption=text, 
                        reply_markup=keyboard, parse_mode="Markdown")

# 1. Реферальная система
@router.callback_query(F.data == "earn_referral")
async def referral_system(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    user = await get_user(user_id)
    referrals = user.get("referrals", [])
    count = len(referrals)
    total_earned = count * 1000
    
    text = f"""
🎯 *Реферальная система*

Получай +1000 PR GRAM за каждого приглашенного друга!

📎 Твоя реферальная ссылка:
`{referral_link}`

📊 Статистика:
- Приглашено друзей: {count}
- Заработано: {total_earned} PR GRAM

🎉 Приглашай по этой ссылке своих друзей, отправляй её во все чаты и зарабатывай!

💡 *Как работает:*
1. Друг переходит по твоей ссылке
2. Начинает играть в боте
3. Ты автоматически получаешь 1000 PR GRAM
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", 
                            url=f"https://t.me/share/url?url={referral_link}&text=Присоединяйся%20к%20игре!")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="earn_menu")]
    ])

    await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# 2. Ежедневный игровой бонус
async def can_claim_game_bonus(user_id: int):
    user = await get_user(user_id)
    if not user:
        return False
    
    last_game_bonus = user.get("last_game_bonus")
    games_today = user.get("games_today", 0)
    
    # Проверяем, прошло ли 24 часа
    if last_game_bonus:
        last_time = last_game_bonus.replace(tzinfo=None) if last_game_bonus.tzinfo else last_game_bonus
        if datetime.now() - last_time < timedelta(hours=24):
            return False
    
    # Проверяем, сыграл ли пользователь хотя бы одну игру сегодня
    return games_today > 0

@router.callback_query(F.data == "earn_game_bonus")
async def game_bonus(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    can_claim = await can_claim_game_bonus(user_id)
    user = await get_user(user_id)
    games_today = user.get("games_today", 0)
    
    if can_claim:
        text = f"""
🎮 <b>Ежедневный игровой бонус</b>

✅ Вы можете получить 2500 PR GRAM!

🎯 <b>Условия выполнены:</b>
- Сыграно игр сегодня: {games_today}
- Прошло более 24 часов с последнего получения

💰 <b>Нажмите кнопку ниже чтобы получить бонус!</b>
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Получить 2500 PR GRAM", callback_data="claim_game_bonus")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="earn_menu")]
        ])
    else:
        next_bonus_time = await get_next_bonus_time(user.get('last_game_bonus'))
        text = f"""
🎮 <b>Ежедневный игровой бонус</b>

❌ Бонус пока недоступен

🎯 <b>Условия для получения:</b>
- Сыграть минимум 1 игру за сегодня
- Прошло 24 часа с последнего получения

📊 <b>Ваша статистика:</b>
- Сыграно игр сегодня: {games_today}
- Следующий бонус: через {next_bonus_time}

💡 Сыграйте хотя бы одну игру и возвращайтесь за бонусом!
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Сыграть в игру", callback_data="emoji_game")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="earn_menu")]
        ])

    await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "claim_game_bonus")
async def claim_game_bonus(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if await can_claim_game_bonus(user_id):
        await update_balance(user_id, 2500)
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_game_bonus": datetime.now()}}
        )
        
        user = await get_user(user_id)
        text = f"""
🎮 *Бонус получен!*

✅ Вы получили 2500 PR GRAM!

💰 Теперь на вашем балансе: {user['balance']:,} PR GRAM

🎯 Возвращайтесь завтра после игры за новым бонусом!
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Сыграть еще", callback_data="emoji_game")],
            [InlineKeyboardButton(text="💰 Заработать еще", callback_data="earn_menu")]
        ])
    else:
        text = "❌ Бонус больше не доступен. Условия не выполнены."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="earn_game_bonus")]
        ])
    
    await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# 3. Бонус за упоминание
async def can_claim_username_bonus(user_id: int, username: str, full_name: str):
    user = await get_user(user_id)
    if user and user.get("claimed_username_bonus"):
        return False

    # Проверяем наличие упоминания в username или имени
    project_keywords = ["PENGUGRAM", "PENGU_GRAM", "PENGU-GRAM", "PENGU GRAM", BOT_USERNAME.lower()]
    
    user_text = f"{username or ''} {full_name or ''}".lower()
    
    for keyword in project_keywords:
        if keyword.lower() in user_text:
            return True
    
    return False

@router.callback_query(F.data == "earn_username_bonus")
async def username_bonus(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    can_claim = await can_claim_username_bonus(user_id, callback.from_user.username, callback.from_user.full_name)
    if user['claimed_username_bonus'] is True:
        text = "❌ Вы уже получали бонус за упоминание в нике"
        await callback.message.edit_caption(caption=text, parse_mode="Markdown")
        return
    if can_claim:
        text = f"""
📝 *Бонус за упоминание*

✅ Вы можете получить 1500 PR GRAM!

🎯 Условие выполнено: в вашем username/имени есть упоминание проекта

💰 Нажмите кнопку ниже чтобы получить бонус!
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Получить 1500 PR GRAM", callback_data="claim_username_bonus")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="earn_menu")]
        ])
    else:
        text = f"""
📝 *Бонус за упоминание*

❌ Бонус пока недоступен

🎯 Условие для получения:
Добавьте в ваш username или имя упоминание проекта:
- PENGUGRAM
- PENGU_GRAM 
- PENGU-GRAM
- PENGU GRAM
- {BOT_USERNAME}

💡 Пример ника: `джон_PRGRAM` или `PRGRAM_алекс`

💰 После изменения ника нажмите кнопку проверки!
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="earn_username_bonus")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="earn_menu")]
        ])

    await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "claim_username_bonus")
async def claim_username_bonus(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if await can_claim_username_bonus(user_id, callback.from_user.username, callback.from_user.full_name):
        await update_balance(user_id, 1500)
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"claimed_username_bonus": True}}
        )
        
        user = await get_user(user_id)
        text = f"""
📝 *Бонус получен!*

✅ Вы получили 1500 PR GRAM!

💰 Теперь на вашем балансе: {user['balance']:,} PR GRAM

🎉 Спасибо за поддержку проекта!
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Начать играть", callback_data="emoji_game")],
            [InlineKeyboardButton(text="💰 Заработать еще", callback_data="earn_menu")]
        ])
    else:
        text = "❌ Условия не выполнены. Добавьте упоминание проекта в username/имя."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="earn_username_bonus")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="earn_menu")]
        ])
    
    await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# Вспомогательные функции
async def get_next_bonus_time(last_bonus_time):
    if not last_bonus_time:
        return "сейчас"
    
    next_time = last_bonus_time + timedelta(hours=24)
    time_left = next_time - datetime.now()
    
    if time_left.total_seconds() <= 0:
        return "сейчас"
    
    hours = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)
    
    return f"{hours}ч {minutes}м"

@router.callback_query(F.data == "earn_menu")
async def back_to_earn_menu(callback: types.CallbackQuery, bot: Bot):
    await earn_prgram_menu(callback.message, bot)
    await callback.answer()


