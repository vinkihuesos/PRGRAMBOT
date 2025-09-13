from aiogram import Router, types, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from utils.db import *
from config import *
router = Router()

# ID или юзернейм канала (без @)


@router.message(Command("start"))
async def on_start(message: types.Message, command: CommandObject, bot: Bot):
    user_id = message.from_user.id
    args = command.args  # Получаем аргумент реферальной ссылки
    referrer_id = int(args) if args and args.isdigit() else None
    
    user = await get_user(user_id)
    if not user:
        await add_user(user_id, referrer_id)  # Добавляем юзера и реферала
    
    keyboard = default_keyboard(user_id)
    
    if await check_subscription(bot, user_id):
        if referrer_id and referrer_id != user_id:
            await process_referral(user_id, referrer_id, bot)
        
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=MAIN_MENU_PHOTO_URL,
            caption="🎰 Добро пожаловать в Pengu Gram!",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME}")],
                [InlineKeyboardButton(text="✅ Проверить", callback_data="check_subscription")]
            ]
        )

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=MAIN_MENU_PHOTO_URL,
            caption="""
Добро пожаловать в мир азартных игр на PR GRAM! Испытайте удачу и выигрывайте в увлекательных играх через Telegram-эмодзи.

Все игры проходят между игроками, если нет игроков, вы можете поиграть с ботом!

🎯 Доступные игры:
🎲 Кости - Бросайте кубики и выигрывайте! 
🏀 Баскетбол - Забрасывайте мяч в корзину и выигрывайте PR GRAM!
⚽️ Футбол - Забивайте голы и выигрывайте игроков!
🎯- Дартс - Попадайте в мишень, кто более точнее тот победил!

✨ Преимущества:
• 💰 Играйте на PR GRAM
• 🎯 Простой геймплей через эмодзи
• 🔄 Честная случайная система
• 🆕 Постоянно новые игры

Вам нужно подписаться на канал, чтобы использовать бота.
""",
            reply_markup=keyboard
        )

async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        chat_member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return False

@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    referrer_id = user.get("referrer_id") if user else None

    if await check_subscription(bot, user_id):
        if referrer_id:
            await process_referral(user_id, referrer_id, bot)

        await callback.message.answer("✅ Вы подписались! Теперь можете использовать бота.")
        await callback.answer()
    else:
        await callback.answer("❌ Вы еще не подписались на канал!", show_alert=True)

@router.message(F.text == "Заработать PR GRAM")
async def referral_system(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    user = await get_user(user_id)
    referrals = user.get("referrals", []) if user else []
    count = len(referrals)
    text = f"""
Получай +1000  PR GRAM ️ за каждого приглашенного друга!

📎 Твоя реферальная ссылка:
{referral_link}

🎉 Приглашай по этой ссылке своих друзей, отправляй её во все чаты и зарабатывай!

Приглашено вами: {count}
"""
    await bot.send_message(chat_id=message.chat.id, text=text)

def register(dp):
    dp.include_router(router)
