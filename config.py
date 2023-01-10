import logging
from os import path


ADMIN_ID = [1787686208, 730161327, 5639593336, 948640825]

ASSETS_GREETING_DIRECTORY = "assets"
GREETING_MSG_FILENAME = path.join(ASSETS_GREETING_DIRECTORY, "greeting_msg.json")
GREETING_MSG_GIF_RU_FILENAME = path.join(ASSETS_GREETING_DIRECTORY, "greeting_msg_gif_ru.gif")
GREETING_MSG_GIF_EN_FILENAME = path.join(ASSETS_GREETING_DIRECTORY, "greeting_msg_gif_en.gif")
PURCHASE_GIF_FILENAME = path.join(ASSETS_GREETING_DIRECTORY, "purchase_gif.gif")
AD_FOLDER = path.join("static", "obj")
AD_CURRENT_FOLDER = path.join(AD_FOLDER, "current")
AD_DEFAULT_FOLDER = path.join(AD_FOLDER, "default")
# width x height
AD_MOBILE_FILENAME = "obj-340x70.gif"
AD_DESKTOP_TOP_FILENAME = "obj-88x30.gif"
AD_DESKTOP_BOTTOM_FILENAME = "obj-468x60.gif"
AD_TEXT_FILENAME = "config.json"
AD_LINK = "https://t.me/fbfarmpro"
SITE_BACKGROUND_FILENAME = "site_background-1920x980.png"
AD_FILES = [AD_MOBILE_FILENAME,
            AD_DESKTOP_BOTTOM_FILENAME,
            AD_DESKTOP_TOP_FILENAME,
            SITE_BACKGROUND_FILENAME,
            AD_TEXT_FILENAME]
GREETING_NO_TEXT = "text is off"
FINAL_ZIP_NAME_LEN = 20
COUPON_LEN = 10
MAX_MONEY_PER_BUY = 1488
MIN_MONEY_PER_BUY = {
    "trx": 1,
    "usdt": 10,
    "bnb": 10,
    "ltc": 10,
    "eth": 10,
    "btc": 50,
}

logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s %(message)s")

