import logging


ADMIN_ID = [730161327, 1787686208, 5709888754, 5639593336]

GREETING_MSG_FILENAME = "greeting_msg.json"
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

