import asyncio
import os

from handlers import *
from utils import keyboards
from datetime import datetime
import zipfile
from utils.database import UsersDB, ProductsDB, Tokens
import smtplib, ssl
from secret import password, sender


users = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")
tokens = Tokens("DB/tokens.db")
users0 = UsersDB("site", "DB/users.db")

@dp.message_handler(commands=["start"])
async def _(message: types.Message):
    userID = message.from_user.id
    token = message.get_args()
    if token:
        if not users.is_registered(userID=userID):
            users.register_site_via_tg(userID)
            # users.register(userID=userID)
            await message.answer("Вы успешно зарегестрировались на сайте с помощью telegram")
        else:
            await message.answer("Вы успешно авторизировались на сайте с помощью telegram")
        tokens.set_status(token, f"done|{userID}")
        return

    with open(config.GREETING_MSG_FILENAME) as file:
        greeting_msg = loads(file.read())
    if users.is_registered(userID=userID):
        if users.get_language(userID=userID) == "RU":
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
        users.register(userID=userID)
        text = greeting_msg["ru"]["text"]
        if text:
            await message.answer(text)
        try:
            await message.answer_animation(InputFile(greeting_msg["ru"]["gif"]))
        except:
            await message.answer_document(InputFile(greeting_msg["ru"]["gif"]))
        await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)


@dp.message_handler(commands=["menu"])
async def _(message: types.Message):
    userID = message.from_user.id
    userLang = users.get_language(userID=userID)
    if userLang == "RU":
        await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
    else:
        await message.answer("Main menu", reply_markup=keyboards.MAIN_MENU_EN)


@dp.message_handler(lambda msg: msg.from_user.id in config.ADMIN_ID, commands=["admin"])
async def _(message: types.Message):
    await message.answer("What do you want to do", reply_markup=keyboards.ADMIN_MENU)



async def send_mail(receiver, mail):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender, password)
        await server.sendmail(sender, receiver, mail)

async def check_for_payments():
    while True:
        for user in users:
            userID = user[1]
            email = user[2]
            if userID:
                userLang = user[4]
                payment_ids = users.get_payments(userID=userID)
                for payment_id in payment_ids:
                    payment_data = await payment.get_payment(payment_id)
                    payment_data = payment_data.get("result", None)
                    if not payment_data:
                        users.remove_payment(payment_id, userID=userID)
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
                        users.add_balance(amount, userID=userID)
                        users.remove_payment(payment_id, userID=userID)
                        if userLang == "RU":
                            await bot.send_message(userID, f"Ваш счет успешно пополнено на {amount}$")
                        else:
                            await bot.send_message(userID, f"{amount}$ added to your balance")
                    elif status == "DECLINED" or status == "CANCELLED":
                        if userLang == "RU":
                            await bot.send_message(userID, f"Ваш платеж {id} просрочен/отменен")
                        else:
                            await bot.send_message(userID, f"You payment {id}, declined/cancelled")
                        users.remove_payment(id, userID=userID)
            elif email:
                payment_ids = users0.get_payments(email=email)
                for payment_id in payment_ids:
                    payment_data = await payment.get_payment(payment_id)
                    payment_data = payment_data.get("result", None)
                    if not payment_data:
                        users0.remove_payment(payment_id, email=email)
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
                        users0.add_balance(amount, email=email)
                        users0.remove_payment(payment_id, email=email)
                        await send_mail(email, f"{amount}$ added to your balance")
                    elif status == "DECLINED" or status == "CANCELLED":
                        await send_mail(email, f"You payment {id}, declined/cancelled")
                        users.remove_payment(id, email=email)
        await asyncio.sleep(30)


async def check_for_bought_products():
    while True:
        for product in users.get_purchases():
            difference = datetime.now() - datetime.fromisoformat(product[2])
            zip_filename = product[6]
            if not zip_filename:
                continue
            zip_path = os.path.join("DB", "bought", zip_filename)
            category_name = product[2]
            if difference.days >= 3 and zip_filename:
                # remove files from our DB
                with zipfile.ZipFile(zip_path, "r") as file:
                    for product_name in file.namelist():
                        os.remove(os.path.join("DB", category_name, product_name))
                        products.remove_product(category_name, product_name)
                users.remove_purchase_archive(zip_filename)
                os.remove(zip_path)

        # every 5 minutes
        await asyncio.sleep(5*60)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.create_task(check_for_payments())
    loop.create_task(check_for_bought_products())
    loop.run_forever()