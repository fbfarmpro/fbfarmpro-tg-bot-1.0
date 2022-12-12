# start date: 02.12.2022, 02:19PM
# deadline: 16.12.2022

from aiogram import types
import asyncio
from config import *
from utils.database import *
from handlers import *
from utils import keyboards


@dp.message_handler(commands=["start"])
async def _(message: types.Message):
    userID = message.from_user.id
    with open(config.GREETING_MSG_FILENAME) as file:
        greeting_msg = loads(file.read())
    if users.is_registered(userID):
        if get_user_lang(userID) == "RU":
            await message.answer(greeting_msg["ru"]["text"])
            await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
        else:
            await message.answer(greeting_msg["en"]["text"])
            await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
    else:
        users.register(userID)
        await message.answer(greeting_msg["ru"]["text"])
        await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)


@dp.message_handler(lambda msg: msg.from_user.id in ADMIN_ID, commands=["admin"])
async def _(message: types.Message):
    userID = message.from_user.id
    await message.answer("What do you want to do", reply_markup=keyboards.ADMIN_MENU)


async def check_for_payments():
    while True:
        for user in users:
            userID = user[0]
            userLang = user[1]
            payment_ids = database.users.get_payments(userID)
            for payment_id in payment_ids:
                payment_data = await database.payment.get_payment(payment_id)
                payment_data = payment_data["result"]
                id = payment_data["id"]
                if id not in payment_ids:
                    continue
                status = payment_data["state"]
                """
                string (PaymentState)
                Enum: "CHECKOUT" "PENDING" "CANCELLED" "DECLINED" "COMPLETED"
                Payment State
                """
                if status == "COMPLETED":
                    amount = payment_data["amount"]
                    database.users.add_balance(userID, amount)
                    database.users.remove_payment(userID, payment_id)
                    if userLang == "RU":
                        await bot.send_message(userID, f"Ваш счет успешно пополнено на {amount}$")
                    else:
                        await bot.send_message(userID, f"{amount}$ added to your balance")
                elif status == "DECLINED" or status == "CANCELLED":
                    await bot.send_message(userID, "cancelled")
                    database.users.remove_payment(userID, id)

        await asyncio.sleep(30)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.create_task(check_for_payments())
    loop.run_forever()
