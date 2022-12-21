import asyncio
import os

from handlers import *
from utils import keyboards
from datetime import datetime
import zipfile


@dp.message_handler(commands=["start"])
async def _(message: types.Message):
    userID = message.from_user.id
    with open(config.GREETING_MSG_FILENAME) as file:
        greeting_msg = loads(file.read())
    if database.users.is_registered(userID):
        if database.users.get_language(userID) == "RU":
            text = greeting_msg["ru"]["text"]
            if text:
                await message.answer(text)
            try:
                await message.answer_animation(InputFile(greeting_msg["ru"]["gif"]))
            except:
                await message.answer_document(InputFile(greeting_msg["ru"]["gif"]))
            await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
        else:
            text = greeting_msg["en"]["text"]
            if text:
                await message.answer(text)
            try:
                await message.answer_animation(InputFile(greeting_msg["en"]["gif"]))
            except:
                await message.answer_document(InputFile(greeting_msg["en"]["gif"]))
            await message.answer("Main menu", reply_markup=keyboards.MAIN_MENU_EN)
    else:
        database.users.register(userID)
        # await message.answer(greeting_msg["ru"]["text"])
        await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)


@dp.message_handler(commands=["menu"])
async def _(message: types.Message):
    userID = message.from_user.id
    userLang = database.users.get_language(userID)
    if userLang == "RU":
        await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
    else:
        await message.answer("Main menu", reply_markup=keyboards.MAIN_MENU_EN)


@dp.message_handler(lambda msg: msg.from_user.id in config.ADMIN_ID, commands=["admin"])
async def _(message: types.Message):
    await message.answer("What do you want to do", reply_markup=keyboards.ADMIN_MENU)


async def check_for_payments():
    while True:
        for user in database.users:
            userID = user[0]
            userLang = user[1]
            payment_ids = database.users.get_payments(userID)
            for payment_id in payment_ids:
                payment_data = await database.payment.get_payment(payment_id)
                payment_data = payment_data.get("result", None)
                if not payment_data:
                    database.users.remove_payment(userID, payment_id)
                    continue
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
                    if userLang == "RU":
                        await bot.send_message(userID, f"Ваш платеж {id} просрочен/отменен")
                    else:
                        await bot.send_message(userID, f"You payment {id}, declined/cancelled")
                    database.users.remove_payment(userID, id)

        await asyncio.sleep(30)


async def check_for_bought_products():
    while True:
        for product in database.users.get_purchases():
            difference = datetime.now() - datetime.fromisoformat(product[1])
            zip_filename = product[5]
            if not zip_filename:
                continue
            zip_path = os.path.join("DB", "bought", zip_filename)
            category_name = product[2]
            if difference.days >= 3 and zip_filename:
                # remove files from our DB
                with zipfile.ZipFile(zip_path, "r") as file:
                    for product_name in file.namelist():
                        os.remove(os.path.join("DB", category_name, product_name))
                        database.products.remove_product(category_name, product_name)
                database.users.remove_purchase_archive(zip_filename)
                os.remove(zip_path)

        # every 5 minutes
        await asyncio.sleep(5*60)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.create_task(check_for_payments())
    loop.create_task(check_for_bought_products())
    loop.run_forever()
