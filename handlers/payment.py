import config
from handlers import *
from aiogram import types
from utils.database import UsersDB, ProductsDB, get_crypto_currency, payment
from aiogram.dispatcher import FSMContext

users = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")


@dp.callback_query_handler(lambda c: c.data.endswith("coin"))
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = users.get_language(userID=userID)

    min_pay = config.MIN_MONEY_PER_BUY[callback_query.data.split("_")[0]]
    await storage.update_data(user=callback_query.from_user.id, data={
        "coin": callback_query.data,
        "lang": lang,
        "min_pay": min_pay
    })
    if lang == "RU":
        await callback_query.message.answer(f"Сколько вы хотите закинуть (в USD) (мин. {min_pay}$, макс. {config.MAX_MONEY_PER_BUY}$)")
    else:
        await callback_query.message.answer(f"Enter amount (in USD) (min. {min_pay}$, max. {config.MAX_MONEY_PER_BUY}$)")
    await storage.set_state(user=userID, state="payment")


@dp.message_handler(state="payment")
async def process_amount(message: types.Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await state.set_state("payment")
        return
    userID = message.from_user.id
    amount = float(message.text)
    async with state.proxy() as data:
        lang = data["lang"]
        coin = data["coin"].split("_")[0]
        min_pay = data["min_pay"]

    # check for correct value
    if amount > config.MAX_MONEY_PER_BUY or amount < min_pay:
        if lang == "RU":
            await message.answer(f"От {min_pay} до {config.MAX_MONEY_PER_BUY}")
        else:
            await message.answer(f"From {min_pay} to {config.MAX_MONEY_PER_BUY}")
        await state.set_state("payment")
        return

    price = await get_crypto_currency(coin) if coin != "usdt" else 1
    amount = amount/price
    response = await payment.create_payment(amount, coin.upper())
    print(response)
    payment_id = response["result"]["id"]
    users.add_payment(payment_id, userID=userID)
    url = response["result"]["redirectUrl"]
    if lang == "RU":
        await bot.send_message(userID, f"Оплатите по ссылке:\n{url}\n"
                                        f"❗️ Вы должны пополнить счет в течении 20 минут\n"
                                        "⚠️Транзакция будет засчитана автоматически.")
        await bot.send_message(userID, "Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
    else:
        await bot.send_message(userID, f"Check details in the link below:\n{url}\n"
                                        f"❗️ Your must fund your account within 20 minutes\n"
                                        "⚠️The transaction will be credited automatically.")
        await bot.send_message(userID, "Main menu", reply_markup=keyboards.MAIN_MENU_EN)
    await state.finish()
