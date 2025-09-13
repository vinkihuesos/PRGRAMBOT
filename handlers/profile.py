import logging
from aiogram import Router, Bot, types, F
from datetime import datetime
from utils.db import get_user
from config import *

router = Router()
logger = logging.getLogger(__name__)


async def get_user_profile_text(user_id: int, username: str, user_data: dict) -> str:
    """Формирует текст профиля пользователя"""
    registration_date = user_data.get("registration_date", datetime.utcnow()).strftime("%d-%m-%Y %H:%M:%S")
    wins, losses, draws = user_data.get("game_stats", [0, 0, 0])

    return (
        f"👤 *Профиль*\n\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"👤 *Username:* `{f'@{username}' if username else 'Не указан'}`\n"
        f"🕐 *Дата регистрации:* `{registration_date}`\n\n"
        f"🟢 *Победы:* {wins}\n"
        f"🔴 *Поражения:* {losses}\n"
        f"🟡 *Ничья:* {draws}"
    )

@router.message(F.text == "🙍‍♂️Профиль")
async def handle_profile(message: types.Message, bot: Bot):
    """Обработчик команды 'Профиль'"""
    user_id = message.from_user.id
    username = message.from_user.username

    user_data = await get_user(user_id)

    if not user_data:
        await message.answer("⚠️ Ошибка: Пользователь не найден в базе данных.")
        return

    profile_text = await get_user_profile_text(user_id, username, user_data)

    await bot.send_photo(
        chat_id=user_id,
        photo=MAIN_PROFILE_PHOTO_URL,
        caption=profile_text,
        parse_mode="Markdown"
    )
