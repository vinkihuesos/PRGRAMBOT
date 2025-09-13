from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict, Any, List
from aiogram import Bot
import asyncio
from random import randint

MONGO_URI = "mongodb+srv://sladk1y:zxcasdqwe@cas.s1v4j.mongodb.net/"
DB_NAME = "RandomlyGift"
# Подключение к MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
emoji_games_collection = db["emoji_games"]

async def reg_game(user_id: int, game_bid: int, game_type: str, game_emoji_count: int, game_id: int, username):
    new_game = {
        "creator_id": user_id,
        "username": username,
        "game_id": game_id,
        "game_bid": game_bid,
        "game_type": game_type,
        "game_emoji_count": game_emoji_count
    }
    await emoji_games_collection.insert_one(new_game)
    return new_game

async def delete_game(game_id: int):
    await emoji_games_collection.delete_one({"game_id": game_id})

async def get_all_games():
    games = []
    async for game in emoji_games_collection.find():
        games.append(game)
    return games

async def get_game(game_id: int):
    return await emoji_games_collection.find_one({"game_id": game_id})