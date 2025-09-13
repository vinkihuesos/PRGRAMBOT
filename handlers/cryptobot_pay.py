import asyncio
import logging
import requests
from aiogram import Router, Bot, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.db import *

PAY_API_TOKEN = "348231:AATklSdicWYi20Ds6sKBjILMoKK01z75trz"

router = Router()
logger = logging.getLogger(__name__)

class PaymentState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_currency = State()

invoices = {}

# Курсы криптовалют к рублю
CRYPTO_RATES = {
    "TON": 320,
    "USDT": 93,
}
STARS_RUB = 1.49

@router.callback_query(lambda c: c.data == "depcb")
async def deposit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(f"💰 Укажите сумму пополнения в звездах PR GRAM \n1 STARS = {STARS_RUB} RUB")
    await state.set_state(PaymentState.waiting_for_amount)
    await callback.answer()

@router.message(PaymentState.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount_rub = float(message.text)
        if amount_rub < 50:
            await message.answer(f"ℹМинимальное пополнение - 50 STARS ≈ {round(STARS_RUB*50, 2)} RUB")
            return
        await state.update_data(amount_rub=amount_rub)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💎 TON", callback_data="crypto_TON")],
            [types.InlineKeyboardButton(text="💵 USDT", callback_data="crypto_USDT")]
        ])
        await message.answer("Выберите криптовалюту для оплаты:", reply_markup=keyboard)
        await state.set_state(PaymentState.waiting_for_currency)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.callback_query(F.data.startswith("crypto_"))
async def process_currency(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    currency = call.data.split("crypto_")[1]
    user_data = await state.get_data()
    amount_rub = user_data.get("amount_rub") * STARS_RUB
    if currency in CRYPTO_RATES:
        amount_crypto = round(amount_rub / CRYPTO_RATES[currency], 6)
        chat_id = call.message.chat.id
        pay_link, invoice_id = get_pay_link(amount_crypto, currency)
        if pay_link and invoice_id:
            invoices[chat_id] = invoice_id  # Сохраняем счет
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=f"Оплатить {amount_crypto} {currency}", url=pay_link)],
                [types.InlineKeyboardButton(text="Проверить оплату", callback_data=f"check_payment_{invoice_id}")]
            ])
            await call.message.answer("Перейдите по ссылке для оплаты и нажмите 'Проверить оплату'", reply_markup=keyboard)
            await state.update_data(amount_crypto=amount_crypto, currency=currency, amount_rub=amount_rub)
        else:
            await call.message.answer("Ошибка: Не удалось создать счет на оплату.")
    else:
        await call.message.answer("Выбранная криптовалюта не поддерживается.")
    await call.answer()

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    chat_id = call.message.chat.id
    invoice_id = call.data.split("check_payment_")[1]
    payment_status = check_payment_status(invoice_id)
    user_data = await state.get_data()
    amount_rub = user_data.get("amount_rub")
    if payment_status and payment_status.get("ok"):
        if "items" in payment_status["result"]:
            invoice = next((inv for inv in payment_status["result"]["items"] if str(inv["invoice_id"]) == invoice_id), None)
            if invoice:
                status = invoice["status"]
                if status == "paid":
                    await call.message.answer("Оплата прошла успешно!✅")
                    await update_balance(call.message.chat.id, amount_rub)
                    await call.message.delete()
                    if invoices[chat_id]:
                        del invoices[chat_id]
                    await call.answer()
                else:
                    await call.answer("Оплата не найдена❌", show_alert=True)
            else:
                await call.answer("Счет не найден.", show_alert=True)
        else:
            logging.error(f"Ответ API не содержит 'items': {payment_status}")
            await call.answer("Ошибка при получении статуса оплаты.", show_alert=True)
    else:
        logging.error(f"Ошибка при запросе статуса оплаты: {payment_status}")
        await call.answer("Ошибка при получении статуса оплаты.", show_alert=True)

def get_pay_link(amount, currency):
    headers = {"Crypto-Pay-API-Token": PAY_API_TOKEN}
    data = {"asset": currency, "amount": amount}
    response = requests.post("https://pay.crypt.bot/api/createInvoice", headers=headers, json=data)
    if response.ok:
        response_data = response.json()
        return response_data["result"]["pay_url"], response_data["result"]["invoice_id"]
    return None, None

def check_payment_status(invoice_id):
    headers = {
        "Crypto-Pay-API-Token": PAY_API_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.post("https://pay.crypt.bot/api/getInvoices", headers=headers, json={})
    if response.ok:
        return response.json()
    else:
        logging.error(f"Ошибка запроса к API: {response.status_code}, {response.text}")
        return None
