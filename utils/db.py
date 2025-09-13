from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict, Any, List
from aiogram import Bot



MONGO_URI = "mongodb+srv://sladk1y:zxcasdqwe@cas.s1v4j.mongodb.net/"
DB_NAME = "RandomlyGift"
# Подключение к MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]
emoji_games_collection = db["emoji_games"]

# Функция добавления пользователя в базу данных
async def add_user(user_id: int, referrer_id: Optional[int] = None) -> Dict[str, Any]:
    """Добавляет пользователя в базу, если его ещё нет."""
    user = await get_user(user_id)
    if user:
        return user
    
    new_user = {
        "user_id": user_id,
        "balance": 0,
        "registration_date": datetime.utcnow(),
        "games": [],
        "is_played": False,
        "game_stats": [0, 0, 0],
        "referrer_id": referrer_id,
        "referrals": [],
        "referral_confirmed": False
    }
    await users_collection.insert_one(new_user)
    return new_user

# Универсальная функция обновления статистики игр
async def update_game_stat(user_id: int, index: int) -> None:
    """Обновляет статистику игр: index=0 (победа), index=1 (поражение), index=2 (ничья)."""
    if index in {0, 1, 2}:
        await users_collection.update_one({"user_id": user_id}, {"$inc": {f"game_stats.{index}": 1}})

async def add_win(user_id: int) -> None:
    await update_game_stat(user_id, 0)

async def add_loss(user_id: int) -> None:
    await update_game_stat(user_id, 1)

async def add_dwaw(user_id: int) -> None:
    await update_game_stat(user_id, 2)

# Функция получения пользователя
async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает пользователя по user_id или None, если его нет."""
    return await users_collection.find_one({"user_id": user_id})

# Функции обновления баланса
async def update_balance(user_id: int, amount: int) -> None:
    """Добавляет сумму к балансу пользователя."""
    await users_collection.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})

async def remove_balance(user_id: int, amount: int) -> None:
    """Вычитает сумму из баланса пользователя."""
    await update_balance(user_id, -amount)

# Функция получения баланса
async def get_balance(user_id: int) -> int:
    """Возвращает баланс пользователя или 0, если его нет."""
    user = await users_collection.find_one({"user_id": user_id}, {"balance": 1})
    return user.get("balance", 0) if user else 0

# Функция добавления нового параметра ко всем пользователям
async def add_new_param(param: str, value: Any) -> None:
    """Добавляет или обновляет параметр у всех пользователей."""
    await users_collection.update_many({}, {'$set': {param: value}})

# Обработка реферальной программы
async def process_referral(user_id: int, referrer_id: int, bot: Bot) -> None:
    """Обрабатывает реферальную систему: добавляет пользователя и уведомляет пригласившего."""
    user = await get_user(user_id)
    
    if not user or user.get("referral_confirmed", False):
        return

    # Подтверждаем реферальную регистрацию
    await users_collection.update_one({"user_id": user_id}, {"$set": {"referral_confirmed": True}})
    await users_collection.update_one({"user_id": referrer_id}, {"$push": {"referrals": user_id}})

    # Получаем username приглашенного пользователя
    try:
        new_user = await bot.get_chat(user_id)
        username = f"@{new_user.username}" if new_user.username else f"ID: {user_id}"
    except Exception as e:
        username = f"ID: {user_id}"
    
    # Уведомляем реферала о новом приглашённом пользователе
    try:
        await update_balance(referrer_id, 1000)
        referrer = await get_user(referrer_id)
        await bot.send_message(referrer_id, f"🎉 Пользователь {username} зарегистрировался по вашей ссылке!\n💰Вы заработали: +1000 PR GRAM ️\n👛Ваш баланс: {referrer['balance']} PR GRAM ")
        
    except Exception:
        pass  # Игнорируем ошибку, если бот не может отправить сообщение

# Получение всех пользователей с ненулевым балансом
async def get_all_users_ids() -> List[Dict[str, Any]]:
    """Возвращает список пользователей, у которых баланс больше 0."""
    return [user async for user in users_collection.find({"balance": {"$gt": 0}}, {"user_id": 1, "balance": 1})]


# async def u():
#     from random import randint
#     for i in range(64):
#         await users_collection.update_one({"user_id": 861704297}, {"$push": {"referrals": randint(0,1000)}})
# import asyncio
# asyncio.run(u())