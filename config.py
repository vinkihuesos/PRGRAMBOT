from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


#####################
#       BOT         
#####################
API_TOKEN = '8488496888:AAE4cMTS4zyXsT0C6FmbJEGhORQdqBde-NE'
API_TOKEN_TEST = '7276829561:AAFQYjZ001d6-W-9p1rHMxksYXZu3ECWrg4'
CHANNEL_USERNAME = "grampengu"  # Замените на свой канал
BOT_USERNAME = "pengugram_bot"
MONGO_URI = "mongodb+srv://sladk1y:zxcasdqwe@cas.s1v4j.mongodb.net/"
DB_NAME = "pengugram_bot"



#####################
#    IMAGES_URL         
#####################
MAGIC_CARD_PHOTO_URL = "https://cdn.discordapp.com/attachments/1342809094444023850/1343658222589968405/image.png?ex=67be12bc&is=67bcc13c&hm=a6f933ae33a4650ef6a34e8ea9d9ae6c7d903b2400fc14f5bb616783c05ce393&"
MAIN_MENU_PHOTO_URL = "https://media.discordapp.net/attachments/1260397703003639974/1416516116909523004/photo_2025-09-13_23-06-52.jpg?ex=68c720ef&is=68c5cf6f&hm=8428821ca045eb657cbfbd14b5eaaea01649c903d353f50acc3b0c3d4f66446c&=&format=webp&width=1056&height=704"
MAIN_GAME_PHOTO_URL = "https://media.discordapp.net/attachments/1260397703003639974/1416515033160089600/photo_2025-09-13_22-53-38.jpg?ex=68c71fed&is=68c5ce6d&hm=70f3c55530022076e0eb3d9ba0bc32f649dfb6bea4e454cdbec18e034adf7b6f&=&format=webp&width=1026&height=684"
MAIN_HELP_IMG = 'https://media.discordapp.net/attachments/1260397703003639974/1416516463275020359/photo_2025-09-13_23-08-49.jpg?ex=68c72142&is=68c5cfc2&hm=1556739234639c614295b3fa694ab7a6e5074c3fc6f3a8def615a4bca88384ec&=&format=webp&width=1056&height=704'
ADMIN_URL = 'https://vignette.wikia.nocookie.net/walkingdead/images/1/16/Walking_Mary_is_tired.jpg/revision/latest?cb=20171205170735&path-prefix=ru'
MAIN_WALLET_PHOTO_URL = 'https://media.discordapp.net/attachments/1260397703003639974/1416515033633915066/photo_2025-09-13_23-01-19.jpg?ex=68c71fed&is=68c5ce6d&hm=63e87fe6d699d9df9e8f5b7f75a189b97e3b2fb4258c04695f8b1c2a908078c9&=&format=webp&width=1026&height=684'
MAIN_PROFILE_PHOTO_URL = 'https://media.discordapp.net/attachments/1260397703003639974/1416515710997369027/photo_2025-09-13_22-53-38.jpg?ex=68c7208f&is=68c5cf0f&hm=c365f4047c5366c71e48f7bed129b9f38a91e29c770db48533e47e714f9516c1&=&format=webp&width=1056&height=704'
MAGIC_CARD_PHOTO_URL_INVISIBLE = 'https://media.discordapp.net/attachments/1342809094444023850/1343264305000349716/Untitled_1.png?ex=67c3e41e&is=67c2929e&hm=8fa88e56e9ca2b0f586cf3e103028c9f8d8b0344756aac478fc93aae700f76a6&=&format=webp&quality=lossless&width=971&height=559'



#####################
#      ADMINS         
#####################
ADMIN_LIST = [5938187650, 861704297, 717997178, 7512492677]


#####################
#    KEYBOARDS         
#####################
def default_keyboard(user_id: int):
    keyboard = [
        [KeyboardButton(text="🕹Играть")],
        [KeyboardButton(text="👛Кошелёк"), KeyboardButton(text="🙍‍♂️Профиль")],
        [KeyboardButton(text="Заработать PR GRAM"), KeyboardButton(text="ℹПомощь")]
    ]

    if user_id in ADMIN_LIST:
        keyboard.append([KeyboardButton(text="👑ADMIN")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
