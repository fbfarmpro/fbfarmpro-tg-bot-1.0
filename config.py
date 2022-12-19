import logging


ADMIN_ID = [1787686208,730161327]

GREETING_MSG_FILENAME = "greeting_msg.json"
GREETING_MSG_GIF_RU_FILENAME = "greeting_msg_gif_ru.gif"
GREETING_MSG_GIF_EN_FILENAME = "greeting_msg_gif_en.gif"
FINAL_ZIP_NAME_LEN = 20
MAX_MONEY_PER_BUY = 1488
MIN_MONEY_PER_BUY = {
    "tron": 1,
    "usdt": 10,
    "bnb": 10,
    "ltc": 10,
    "eth": 10,
    "btc": 50,
}

logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s %(message)s")

