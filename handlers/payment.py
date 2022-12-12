from handlers import *
from aiogram import types
import utils.database as database
from aiogram.dispatcher import FSMContext


@dp.message_handler(lambda msg: msg.text.isdigit(), state="payment")
async def process_amount(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    async with state.proxy() as data:
        lang = data["lang"]

    response_card = await database.payment.create_payment(int(message.text), "BASIC_CARD")
    response_crypto = await database.payment.create_payment(int(message.text), "CRYPTO")
    payment_id_card = response_card["result"]["id"]
    payment_id_crypto = response_crypto["result"]["id"]
    database.users.add_payment(userID, payment_id_card)
    database.users.add_payment(userID, payment_id_crypto)
    url_card = response_card["result"]["redirectUrl"]
    url_crypto = response_crypto["result"]["redirectUrl"]
    if lang == "RU":
        await bot.send_message(userID, f"Вы можете оплатить криптой\n{url_crypto}\n"
                                       f"Или картой \n{url_card}\n"
                                        f"❗️ Вы должны пополнить счет в течении 20 минут\n"
                                        "⚠️Транзакция будет засчитана автоматически.")
    else:
        await bot.send_message(userID, f"You can pay using crypto\n{url_crypto}\n"
                                       f"or using card\n{url_card}\n"
                                        f"❗️ Your must fund your account within 20 minutes\n"
                                        "⚠️The transaction will be credited automatically.")
    await state.finish()
