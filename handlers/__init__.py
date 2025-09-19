from .start import router as start_router
from .emoji_game_wbot import router as emoji_game__wbot_router
from .emoji_game_wplayer import router as emoji_game__wplayer_router
from .magic_cards import router as magic_cards_router
from .poker import router as poker_router
from .blackjack import router as blackjack_router
from .baccara import router as baccara_router
from .more_less import router as more_less_router
from .play import router as play_router
from .wallet import router as wallet_router  # Исправлено на wallet.py (по скриншоту)
from .profile import router as profile_router
from .help import router as help_router
from .admin import router as admin_router
from .cryptobot_pay import router as cryptobot_pay_router
from .stars_pay import router as stars_pay_router  # Добавлен обработчик из файла stars_pay.py
from .earn import router as earn_router

def register_all_handlers(dp):
    """
    Подключает все обработчики (роутеры) из файлов в handlers/ к диспетчеру dp.
    """
    dp.include_router(start_router)
    dp.include_router(emoji_game__wbot_router)
    dp.include_router(emoji_game__wplayer_router)
    dp.include_router(magic_cards_router)
    dp.include_router(poker_router)
    dp.include_router(blackjack_router)
    dp.include_router(baccara_router)
    dp.include_router(more_less_router)
    dp.include_router(play_router)
    dp.include_router(wallet_router)
    dp.include_router(profile_router)
    dp.include_router(help_router)
    dp.include_router(admin_router)
    dp.include_router(cryptobot_pay_router)
    dp.include_router(stars_pay_router)  # Добавлен обработчик оплаты через stars_pay.py
    dp.include_router(earn_router)
