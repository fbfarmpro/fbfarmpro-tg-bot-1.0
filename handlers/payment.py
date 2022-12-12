from handlers import *
from aiogram import types
import utils.database as database
from aiogram.dispatcher import FSMContext


@dp.callback_query_handler(lambda c: c.data.startswith("add_balance_"))
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = database.users.get_language(userID)

    if callback_query.data.endswith("card"):
        await storage.update_data(user=userID, data={"paymentMethod": "BASIC_CARD", "lang": lang})
    else:
        await storage.update_data(user=userID, data={"paymentMethod": "CRYPTO", "lang": lang})

    if lang == "RU":
        await callback_query.message.answer("Сколько вы хотите закинуть (в USD)")
    else:
        await callback_query.message.answer("Enter amount (in USD)")
    await storage.set_state(user=userID, state="payment")


@dp.message_handler(lambda msg: msg.text.isdigit(), state="payment")
async def process_amount(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    async with state.proxy() as data:
        lang = data["lang"]
        paymentMethod = data["paymentMethod"]
        assert paymentMethod in ["BASIC_CARD", "CRYPTO"]

    response = await database.payment.create_payment(int(message.text), paymentMethod)
    payment_id = response_card["result"]["id"]
    database.users.add_payment(userID, payment_id)
    url = response_card["result"]["redirectUrl"]
    if lang == "RU":
        await bot.send_message(userID, f"Оплатите по ссылке:\n{url}\n"
                                        f"❗️ Вы должны пополнить счет в течении 20 минут\n"
                                        "⚠️Транзакция будет засчитана автоматически.")
    else:
        await bot.send_message(userID, f"Check details in the link below:\n{url}\n"
                                        f"❗️ Your must fund your account within 20 minutes\n"
                                        "⚠️The transaction will be credited automatically.")
    await state.finish()
