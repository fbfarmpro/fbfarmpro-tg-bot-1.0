from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# buttons

# For menu
MY_PROFILE_BTN_RU = InlineKeyboardButton("Мой профиль", callback_data="my_profile")
MY_PROFILE_BTN_EN = InlineKeyboardButton("My profile", callback_data="my_profile")

ADD_BALANCE_BTN_RU = InlineKeyboardButton("Пополнить баланс", callback_data="add_balance")
ADD_BALANCE_BTN_EN = InlineKeyboardButton("Add balance", callback_data="add_balance")

TRON_COIN_BTN = InlineKeyboardButton("Tron", callback_data="trx_coin")
ETHEREUM_COIN_BTN = InlineKeyboardButton("Ethereum", callback_data="eth_coin")
USDT_COIN_BTN = InlineKeyboardButton("USDT TRC20", callback_data="usdt_coin")
BINANCE_COIN_BTN = InlineKeyboardButton("Binance (BSC)", callback_data="bnb_coin")
BITCOIN_COIN_BTN = InlineKeyboardButton("Bitcoin", callback_data="btc_coin")
LITECOIN_COIN_BTN = InlineKeyboardButton("Litecoin", callback_data="ltc_coin")

MY_PURCHASE_HISTORY_RU = InlineKeyboardButton("История покупок", callback_data="purchase_history")
MY_PURCHASE_HISTORY_EN = InlineKeyboardButton("Purchase history", callback_data="purchase_history")

MY_PREORDERS_BTN_RU = InlineKeyboardButton("Мои предзаказы", callback_data="my_preorders")
MY_PREORDERS_BTN_EN = InlineKeyboardButton("My preorders", callback_data="my_preorders")

PREORDER_BTN_RU = InlineKeyboardButton("Предзаказ", callback_data="preorder")
PREORDER_BTN_EN = InlineKeyboardButton("Preorder", callback_data="preorder")

PURCHASE_BTN_RU = InlineKeyboardButton("Покупка", callback_data="purchase")
PURCHASE_BTN_EN = InlineKeyboardButton("Purchase", callback_data="purchase")

RULES_BTN_RU = InlineKeyboardButton("Правила", callback_data="rules")
RULES_BTN_EN = InlineKeyboardButton("Rules", callback_data="rules")

HELP_BTN_RU = InlineKeyboardButton("Помощь", callback_data="help")
HELP_BTN_EN = InlineKeyboardButton("Help", callback_data="help")

LANGUAGE_BTN_RU = InlineKeyboardButton("🏴‍☠️=>🇺🇸", callback_data="language")
LANGUAGE_BTN_EN = InlineKeyboardButton("🇺🇸=>🏴‍☠️", callback_data="language")

MAIN_MENU_BTN_RU = InlineKeyboardButton("Главное меню", callback_data="menu")
MAIN_MENU_BTN_EN = InlineKeyboardButton("Main menu", callback_data="menu")

GREETING_MSG_BTN = InlineKeyboardButton("Greeting msg", callback_data="greeting_msg")
GREETING_MSG_EDIT_RU_BTN = InlineKeyboardButton("Edit greeting msg RU", callback_data="greeting_msg_edit_ru")
GREETING_MSG_EDIT_EN_BTN = InlineKeyboardButton("Edit greeting msg EN", callback_data="greeting_msg_edit_en")
GREETING_MSG_PREVIEW_RU_BTN = InlineKeyboardButton("Greeting msg preview RU", callback_data="greeting_msg_preview_ru")
GREETING_MSG_PREVIEW_EN_BTN = InlineKeyboardButton("Greeting msg preview EN", callback_data="greeting_msg_preview_en")

PURCHASE_GIF_CHANGE = InlineKeyboardButton("Change purchase gif", callback_data="purchase_gif_change")

MAILING_BTN = InlineKeyboardButton("Mailing", callback_data="mailing")
# await message.reply(text="No sound!", disable_notification=True)
MAILING_SOUND_BTN = InlineKeyboardButton("Sound on/off", callback_data="mailing_sound")
MAILING_PROTECT_CONTENT_BTN = InlineKeyboardButton("Protect content on/off", callback_data="mailing_protect_content")
MAILING_CHANGE_BUTTONS_BTN = InlineKeyboardButton("Change buttons (add/del)", callback_data="mailing_change_buttons")
MAILING_CHANGE_BUTTONS_ADD_BTN = InlineKeyboardButton("Add button", callback_data="mailing_change_buttons_add")
MAILING_CHANGE_BUTTONS_DEL_BTN = InlineKeyboardButton("Del button", callback_data="mailing_change_buttons_del")
MAILING_CHANGE_BUTTONS_BACK_BTN = InlineKeyboardButton("Back", callback_data="mailing_change_buttons_back")
MAILING_ADD_MEDIA_BTN = InlineKeyboardButton("Add media (photo/gif)", callback_data="mailing_add_media")
MAILING_CHANGE_TEXT_BTN = InlineKeyboardButton("Change text", callback_data="mailing_change_text")
MAILING_PREVIEW_BTN = InlineKeyboardButton("Preview", callback_data="mailing_preview")
MAILING_START_BTN = InlineKeyboardButton("Start mailing", callback_data="mailing_start")
MAILING_PRIORITY_BTN = InlineKeyboardButton("Priority", callback_data="mailing_priority")

STATISTIC_BTN = InlineKeyboardButton("Statistic", callback_data="statistic")

CHANGE_USER_DATA_BTN = InlineKeyboardButton("Change user data", callback_data="change_user")
CHANGE_USER_DATA_BAN_BTN = InlineKeyboardButton("Ban", callback_data="change_user_ban")
CHANGE_USER_DATA_BALANCE_BTN = InlineKeyboardButton("Change balance", callback_data="change_user_balance")

CATEGORY_ADD_BTN = InlineKeyboardButton("Add category", callback_data="category_add")
PRODUCT_ADD_BTN = InlineKeyboardButton("Add product", callback_data="product_add")
PRODUCT_REPLACE_BTN = InlineKeyboardButton("Change product category", callback_data="product_replace")

BACK_BTN = InlineKeyboardButton("Back", callback_data="back")

# keyboards

COINS_MENU = InlineKeyboardMarkup(row_width=2)
COINS_MENU.add(TRON_COIN_BTN, USDT_COIN_BTN)
COINS_MENU.add(ETHEREUM_COIN_BTN, BINANCE_COIN_BTN)
COINS_MENU.add(BITCOIN_COIN_BTN, LITECOIN_COIN_BTN)

MAIN_MENU_RU = InlineKeyboardMarkup(row_width=2)
MAIN_MENU_RU.add(MY_PROFILE_BTN_RU, ADD_BALANCE_BTN_RU)
MAIN_MENU_RU.add(MY_PREORDERS_BTN_RU, PREORDER_BTN_RU)
MAIN_MENU_RU.add(PURCHASE_BTN_RU).add(MY_PURCHASE_HISTORY_RU)
MAIN_MENU_RU.add(RULES_BTN_RU).add(HELP_BTN_RU, LANGUAGE_BTN_RU)

MAIN_MENU_EN = InlineKeyboardMarkup(row_width=2)
MAIN_MENU_EN.add(MY_PROFILE_BTN_EN, ADD_BALANCE_BTN_EN)
MAIN_MENU_EN.add(MY_PREORDERS_BTN_EN, PREORDER_BTN_EN)
MAIN_MENU_EN.add(PURCHASE_BTN_EN).add(MY_PURCHASE_HISTORY_EN)
MAIN_MENU_EN.add(RULES_BTN_EN).add(HELP_BTN_EN, LANGUAGE_BTN_EN)

ADMIN_MENU = InlineKeyboardMarkup(row_width=1)
ADMIN_MENU.add(GREETING_MSG_BTN, PURCHASE_GIF_CHANGE, MAILING_BTN)
ADMIN_MENU.add(CHANGE_USER_DATA_BTN, STATISTIC_BTN)
ADMIN_MENU.add(CATEGORY_ADD_BTN, PRODUCT_ADD_BTN)
ADMIN_MENU.add(PRODUCT_REPLACE_BTN)

GREETING_MSG_MENU = InlineKeyboardMarkup(row_width=1)
GREETING_MSG_MENU.add(GREETING_MSG_EDIT_RU_BTN, GREETING_MSG_EDIT_EN_BTN)
GREETING_MSG_MENU.add(GREETING_MSG_PREVIEW_RU_BTN, GREETING_MSG_PREVIEW_EN_BTN)
GREETING_MSG_MENU.add(BACK_BTN)
# GREETING_MSG_MENU.add(GRE)

MAILING_MENU = InlineKeyboardMarkup(row_width=1)
MAILING_MENU.add(MAILING_SOUND_BTN, MAILING_PROTECT_CONTENT_BTN)
MAILING_MENU.add(MAILING_CHANGE_TEXT_BTN, MAILING_ADD_MEDIA_BTN)
MAILING_MENU.add(MAILING_CHANGE_BUTTONS_BTN, MAILING_PRIORITY_BTN)
MAILING_MENU.add(MAILING_START_BTN, MAILING_PREVIEW_BTN)
MAILING_MENU.add(BACK_BTN)

MAILING_CHANGE_BUTTONS_MENU = InlineKeyboardMarkup(row_width=1)
MAILING_CHANGE_BUTTONS_MENU.add(MAILING_CHANGE_BUTTONS_ADD_BTN, MAILING_CHANGE_BUTTONS_DEL_BTN)
MAILING_CHANGE_BUTTONS_MENU.add(MAILING_CHANGE_BUTTONS_BACK_BTN)

CHANGE_USER_DATA_MENU = InlineKeyboardMarkup(row_width=2)
CHANGE_USER_DATA_MENU.add(CHANGE_USER_DATA_BAN_BTN, CHANGE_USER_DATA_BALANCE_BTN)
