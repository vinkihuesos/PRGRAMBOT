
from aiogram import Router, types, Bot, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.db import get_user, get_balance, update_balance, remove_balance
import re

router = Router()
ADMINS_LIST = [717997178, 5938187650, 7512492677]  # ID администраторов

# Состояния для пополнения через чек
class DepositState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()

# Состояния для вывода
class WithdrawState(StatesGroup):
    amount = State()
    username = State()

# Состояния для админской проверки чека
class AdminCheckState(StatesGroup):
    waiting_for_comment = State()

user_selected_game = {}
user_selected_count = {}

# Обработчик кнопки "Пополнить баланс"
@router.callback_query(F.data == "dep")
async def deposit(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💰 Укажите сумму пополнения:")
    await state.set_state(DepositState.waiting_for_amount)
    await callback.answer()

# Обработчик введенной суммы пополнения
@router.message(DepositState.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) > 1000000 or int(message.text) < 10000:
        await message.answer("❌ Введите корректную сумму (от 10000 до 100000 PR GRAM ).")
        return

    amount = int(message.text)
    await state.update_data(amount=amount)
    await message.answer(f"💳 Сумма пополнения: {amount} PR GRAM \n\n📎 Теперь отправьте ссылку на чек (https://...)")
    await state.set_state(DepositState.waiting_for_receipt)

# Обработчик ссылки на чек
@router.message(DepositState.waiting_for_receipt)
async def process_deposit_receipt(message: Message, state: FSMContext, bot: Bot):
    # Проверяем, что это валидная HTTPS ссылка
    url_pattern = r'^https://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, message.text):
        await message.answer("❌ Пожалуйста, отправьте корректную HTTPS ссылку на чек.")
        return

    receipt_url = message.text
    user_data = await state.get_data()
    amount = user_data.get("amount")
    user_id = message.from_user.id
    username = message.from_user.username or "Нет username"

    # Создаем клавиатуру для админа
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_dep_{user_id}_{amount}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_dep_{user_id}")
        ]
    ])

    # Отправляем заявку всем админам
    for admin_id in ADMINS_LIST:
        try:
            await bot.send_message(
                admin_id,
                f"🔔 Новая заявка на пополнение!\n\n"
                f"👤 Пользователь: @{username} (ID: {user_id})\n"
                f"💰 Сумма: {amount} PR GRAM \n"
                f"📎 Чек: {receipt_url}",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")

    await message.answer("✅ Заявка на пополнение отправлена администратору. Ожидайте проверки.")
    await state.clear()

# Обработчик подтверждения пополнения админом
@router.callback_query(F.data.startswith("approve_dep_"))
async def approve_deposit(callback: CallbackQuery, bot: Bot):
    data_parts = callback.data.split("_")
    user_id = int(data_parts[2])
    amount = int(data_parts[3])
    
    # Пополняем баланс пользователя
    await update_balance(user_id, amount)
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            user_id,
            f"✅ Ваш платеж на {amount} PR GRAM  успешно прошел проверку!\n"
            f"💰 Баланс пополнен."
        )
    except Exception as e:
        print(f"Ошибка отправки пользователю {user_id}: {e}")
    
    # Уведомляем админа
    await callback.message.edit_text(
        f"✅ Пополнение подтверждено\n"
        f"👤 Пользователь: {user_id}\n"
        f"💰 Сумма: {amount} PR GRAM \n"
        f"✅ Баланс пополнен"
    )
    await callback.answer("Пополнение подтверждено")

# Обработчик отклонения пополнения админом
@router.callback_query(F.data.startswith("reject_dep_"))
async def reject_deposit(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[2])
    
    # Сохраняем ID пользователя для комментария
    await state.update_data(reject_user_id=user_id, action_type="reject_deposit")
    await state.set_state(AdminCheckState.waiting_for_comment)
    
    await callback.message.answer(
        "📝 Введите причину отклонения чека:\n"
        "(Для отмены напишите -)"
    )
    await callback.answer()

@router.callback_query(F.data == "with")
async def ask_withdraw_amount(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.from_user.id)
    
    await callback.message.answer(
        f"💳 *Вывод PR GRAM*\n\n"
        f"• Минимум: *10,000 PR GRAM*\n"
        f"💰 *Ваш баланс:* {user['balance']} PR GRAM\n\n"
        f"ℹ️ Введите сумму для вывода:",
        parse_mode='Markdown'
    )
    await state.set_state(WithdrawState.amount)
    await callback.answer()

@router.message(WithdrawState.amount)
async def ask_withdraw_username(message: Message, state: FSMContext):
    user = await get_user(message.chat.id)

    if not message.text.isdigit() or int(message.text) < 10000 or int(message.text) > user['balance']:
        await message.answer("❌ Введите корректную сумму вывода (мин. 10,000 PR GRAM).")
        return
    
    await state.update_data(amount=message.text)
    await message.answer("📝 Введите ваш юзернейм для вывода PR GRAM (например: @username):")
    await state.set_state(WithdrawState.username)

@router.message(WithdrawState.username)
async def confirm_withdraw(message: Message, state: FSMContext, bot: Bot):
    username = message.text.strip()
    if not username.startswith('@'):
        username = '@' + username
    
    user_data = await state.get_data()
    amount = user_data.get("amount")
    
    # Сохраняем сумму для возможного возврата при отклонении
    await state.update_data(amount=amount)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить вывод", callback_data=f"approve_with_{message.chat.id}_{amount}"),
            InlineKeyboardButton(text="❌ Отклонить вывод", callback_data=f"reject_with_{message.chat.id}_{amount}")
        ],
        [InlineKeyboardButton(text="✏️ Оставить комментарий", callback_data=f"comment_with_{message.chat.id}")]
    ])

    for admin in ADMINS_LIST:
        await bot.send_message(
            admin,
            f"🔔 Новая заявка на вывод PR GRAM!\n\n"
            f"👤 Пользователь: @{message.from_user.username or 'нет username'}\n"
            f"💰 Сумма: {amount} PR GRAM\n"
            f"📝 Юзернейм для вывода: {username}\n"
            f"🆔 ID пользователя: {message.chat.id}",
            reply_markup=keyboard
        )

    await message.answer(f"""
🟢 Заявка на вывод отправлена администратору, ожидайте oбрaбoтки🔄

💰 Суммa: {amount} PR GRAM

❗️ Спaм в стoрoну aдминистрaции - зaдeржит Вaш вывoд дo 24 чaсoв!""")
    await remove_balance(message.chat.id, int(amount))
    await state.clear()

@router.callback_query(F.data.startswith("approve_with_"))
async def approve_withdraw(callback: CallbackQuery, bot: Bot):
    data_parts = callback.data.split("_")
    user_id = int(data_parts[2])
    amount = data_parts[3]
    
    await bot.send_message(user_id, f"✅ Ваш вывод {amount} PR GRAM был успешно обработан!")
    user = await bot.get_chat(user_id)
    await callback.message.edit_text(f"✅ Вывод {amount}\nДля ID: @{user.username} || {user_id}\n\nОдобрен")
    await callback.answer()

@router.callback_query(F.data.startswith("reject_with_"))
async def reject_withdraw(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    user_id = int(data_parts[2])
    amount = data_parts[3]
    
    await state.update_data(
        reject_user_id=user_id,
        amount=amount,
        action_type="reject_withdraw"
    )
    await state.set_state(AdminCheckState.waiting_for_comment)
    
    await callback.message.answer(
        "📝 Введите причину отклонения вывода:\n"
        "(Для отмены напишите -)"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("comment_with_"))
async def ask_for_comment(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[2])

    await state.update_data(
        comment_user_id=user_id,
        action_type="comment_withdraw"
    )
    await state.set_state(AdminCheckState.waiting_for_comment)
    
    await callback.message.answer(
        "📝 Введите комментарий для пользователя:\n"
        "(Для отмены напишите -)"
    )
    await callback.answer()

# Обработчик комментария при отклонении
@router.message(AdminCheckState.waiting_for_comment)
async def handle_comment(message: Message, state: FSMContext, bot: Bot):
    comment = message.text
    user_data = await state.get_data()
    action_type = user_data.get("action_type")
    
    if comment == '-':
        await state.clear()
        await message.answer("❌ Действие отменено.")
        return
    
    if action_type == "reject_deposit":
        user_id = user_data.get("reject_user_id")
        if user_id:
            try:
                await bot.send_message(
                    user_id,
                    f"❌ Ваш чек был отклонен администратором.\n\n"
                    f"📝 Причина: {comment}\n\n"
                    f"ℹ️ Пожалуйста, проверьте:\n"
                    f"• Корректность ссылки на чек\n"
                    f"• Актуальность чека\n"
                    f"• Соответствие суммы\n"
                    f"• Ликвидность чека"
                )
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")
            
            await message.answer("✅ Пользователь уведомлен об отклонении чека.")
    
    elif action_type == "reject_withdraw":
        user_id = user_data.get("reject_user_id")
        amount = user_data.get("amount")
        if user_id and amount:
            try:
                await bot.send_message(
                    user_id,
                    f"❌ Ваш вывод был отклонен администратором.\n\n"
                    f"📝 Причина: {comment}\n\n"
                    f"💰 Средства возвращены на баланс."
                )
                # Возвращаем средства на баланс
                await update_balance(user_id, int(amount))
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")
            
            await message.answer("✅ Пользователь уведомлен об отклонении вывода.")
    
    elif action_type == "comment_withdraw":
        user_id = user_data.get("comment_user_id")
        if user_id:
            try:
                await bot.send_message(
                    user_id,
                    f"💬 Администратор оставил комментарий к вашему выводу:\n\n{comment}"
                )
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")
            
            await message.answer("✅ Комментарий отправлен пользователю.")
    
    await state.clear()