import logging
from aiogram import Router, Bot, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import *
from aiogram.fsm.context import FSMContext
from utils.db import *
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

router = Router()
logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_balance = State()
    waiting_for_add_balance = State()
    waiting_for_remove_balance = State()

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Юзер"), KeyboardButton(text="💰 Финансы")],
            [KeyboardButton(text="⚙ Настройки"), KeyboardButton(text="🚀 Управление игрой")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def user_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Накрутить деньги"), KeyboardButton(text="💰 Снять деньги")],
            [KeyboardButton(text="🔄 Выбрать другого пользователя")],
            [KeyboardButton(text="🔄 В панель")],
        ],
        resize_keyboard=True
    )

async def usr_info(user_id, bot, message):
    user = await get_user(user_id)
    registration_date = user['registration_date']
    registration_date = registration_date.strftime("%d-%m-%Y %H:%M:%S")
    wins = user['game_stats'][0]
    loses = user['game_stats'][1]
    draw = user['game_stats'][2]
    caption = f"""
UID: {user['user_id']}

BALANCE: {user['balance']}

REG DATA: {registration_date}

WINS: {wins}

LOSES: {loses}

DRAWS: {draw}

"""
    await bot.send_photo(message.chat.id, photo=ADMIN_URL, caption=caption, reply_markup=user_admin_keyboard())

@router.message(F.text == '👑ADMIN')
async def handle_admin(message: types.Message, bot: Bot):
    """
    Обработчик команды ADMIN.
    """
    if message.from_user.id not in ADMIN_LIST:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    await bot.send_photo(caption="🔧 Здравствуй мой господин!", reply_markup=admin_keyboard(), photo=ADMIN_URL, chat_id=message.chat.id)

@router.message(F.text == "📊 Юзер")
async def request_user_id(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_LIST:
        return
    await message.answer("Введите ID пользователя:")
    await state.set_state(AdminStates.waiting_for_user_id)

@router.message(AdminStates.waiting_for_user_id, F.text.isdigit())
async def send_info_by_user_id(message: types.Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_LIST:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    user_id = int(message.text)
    await state.update_data(user_id=int(message.text))
    user = await get_user(user_id)
    registration_date = user['registration_date']
    registration_date = registration_date.strftime("%d-%m-%Y %H:%M:%S")
    await usr_info(user_id, bot, message)

@router.message(F.text == "💰 Накрутить деньги")
async def request_add_balance(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_LIST:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await message.answer("Введите сумму для начисления:")
    await state.set_state(AdminStates.waiting_for_add_balance)

@router.message(AdminStates.waiting_for_add_balance, F.text.isdigit())
async def add_balance(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")
    amount = int(message.text)
    await update_balance(user_id, amount)
    await message.answer(f"✅ Баланс пользователя {user_id} увеличен на {amount}.")
    await usr_info(user_id, bot, message)

@router.message(F.text == "💰 Снять деньги")
async def request_remove_balance(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_LIST:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await message.answer("Введите сумму для снятия:")
    await state.set_state(AdminStates.waiting_for_remove_balance)

@router.message(AdminStates.waiting_for_remove_balance, F.text.isdigit())
async def remove_balance(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")
    amount = int(message.text)
    await update_balance(user_id, -amount)
    await message.answer(f"✅ С баланса пользователя {user_id} снято {amount}.")
    await usr_info(user_id, bot, message)

@router.message(F.text == "🔄 Выбрать другого пользователя")
async def request_new_user_id(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_LIST:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await message.answer("Введите ID нового пользователя:")
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(F.text == "🔄 В панель")
async def back_v_admin(message: types.Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_LIST:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    await bot.send_photo(caption="🔧 Здравствуй мой господин!", reply_markup=admin_keyboard(), photo=ADMIN_URL, chat_id=message.chat.id)

@router.message(F.text == "🔙 Назад")
async def back_v_admin(message: types.Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_LIST:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    await bot.send_photo(caption="🔧 Здравствуй мой господин!", reply_markup=default_keyboard(message.from_user.id), photo=ADMIN_URL, chat_id=message.chat.id)