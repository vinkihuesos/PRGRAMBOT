import logging
from aiogram import Router, Bot, types

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == "more_less")
async def handle_poker(callback: types.CallbackQuery):
    """
    Пример простого обработчика для Poker.
    """
    await callback.message.answer("*More Less* находится в разработке.\nКак только игра появится, мы оповестим вас в телеграм канале", parse_mode="Markdown")
    await callback.answer()
