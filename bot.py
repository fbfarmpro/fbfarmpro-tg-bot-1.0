import asyncio
import os
import filecmp
import random
import calendar

import config
from handlers import *
from index import send_email_attachment
from utils import keyboards
from datetime import datetime
import zipfile
from utils.database import UsersDB, ProductsDB, Tokens
import smtplib
import ssl
from secret import password, sender
from json import loads


users = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")
tokens = Tokens("DB/tokens.db")
users0 = UsersDB("site", "DB/users.db")


@dp.message_handler(commands=["start"])
async def _(message: types.Message):
    userID = message.from_user.id
    token = message.get_args()
    if token:
        if tokens.get_link(token):
            if users.is_registered(userID=userID):
                userLang = users.get_language(userID=userID)
                if userLang == "RU":
                    await message.answer("Вы уже загерестрированы")
                else:
                    await message.answer("You are already registered")
            else:
                if tokens.get_link_usages(token) < 5:
                    referral_user = tokens.get_link(token)
                    if referral_user[2]:
                        users.add_ref_balance(1, userID=referral_user[2])
                        users.add_balance(1, userID=referral_user[2])
                    else:
                        users0.add_ref_balance(1, email=referral_user[1])
                        users0.add_balance(1, userID=referral_user[2])
                    tokens.add_link_usages(token)
                    await message.answer("I'm here")
                else:
                    await message.answer("This referral link was used more than 5 times")
        elif tokens.get(token):
            status = tokens.get(token)[1]

            if 'link' in status:
                if users.is_registered(userID=userID):
                    email = status.split("|")[1]
                    users0.add_balance(users.get_balance(userID=userID), email=email)
                    for x in users.get_payments(userID=userID):
                        users0.add_payment(x, email=email)
                    users.remove_user(userID=userID)
                    users.link_tg(userID, email)
                    tokens.set_status(token, f"linked|{userID}|{email}")
                    await message.answer(f"Для завершения перейдите по ссылке <b><a href='https://fbfarm.pro/tgauth{token}'>Завершить</a></b>", parse_mode="HTML")
                    return
                else:
                    email = status.split("|")[1]
                    users.link_tg(userID, email)
                    tokens.set_status(token, f"linked|{userID}|{email}")
                    await message.answer(
                        f"Для завершения перейдите по ссылке <b><a href='https://fbfarm.pro/tgauth{token}'>Завершить</a></b>",
                        parse_mode="HTML")
                    return
            elif 'waiting' in status:
                if not users.is_registered(userID=userID):
                    users.register_site_via_tg(userID)
                    # users.register(userID=userID)
                    await message.answer(f"Для завершения перейдите по ссылке <a href='https://fbfarm.pro/tgauth{token}'>Завершить</a>", parse_mode="HTML")
                else:
                    await message.answer(f"Для завершения перейдите по ссылке <a href='https://fbfarm.pro/tgauth{token}'>Завершить</a>", parse_mode="HTML")
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
            except Exception as e:
                print(e)
                await message.answer_document(InputFile(greeting_msg["ru"]["gif"]))
            await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
        else:
            text = greeting_msg["en"]["text"]
            if text:
                await message.answer(text)
            try:
                await message.answer_animation(InputFile(greeting_msg["en"]["gif"]))
            except Exception as e:
                print(e)
                await message.answer_document(InputFile(greeting_msg["en"]["gif"]))
            await message.answer("Main menu", reply_markup=keyboards.MAIN_MENU_EN)
    else:
        users.register(userID=userID)
        text = greeting_msg["ru"]["text"]
        if text:
            await message.answer(text)
        try:
            await message.answer_animation(InputFile(greeting_msg["ru"]["gif"]))
        except Exception as e:
            print(e)
            await message.answer_document(InputFile(greeting_msg["ru"]["gif"]))
        await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)


@dp.message_handler(commands=["menu"])
async def _(message: types.Message):
    userID = message.from_user.id
    userLang = users.get_language(userID=userID)
    with open(os.path.join(config.AD_CURRENT_FOLDER, config.AD_TEXT_FILENAME), "r") as file:
        texts = loads(file.read())
    if userLang == "RU":
        await message.answer("Главное меню", reply_markup=keyboards.MAIN_MENU_RU)
        await message.answer(texts["ru"])
    else:
        await message.answer("Main menu", reply_markup=keyboards.MAIN_MENU_EN)
        await message.answer(texts["en"])


@dp.message_handler(lambda msg: msg.from_user.id in config.ADMIN_ID, commands=["admin"])
async def _(message: types.Message):
    await message.answer("What do you want to do", reply_markup=keyboards.ADMIN_MENU)


def send_mail(receiver, mail):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, mail)


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
                            await bot.send_message(userID, f"Ваш платеж {payment_id} просрочен/отменен")
                        else:
                            await bot.send_message(userID, f"You payment {payment_id}, declined/cancelled")
                        users.remove_payment(payment_id, userID=userID)
            elif email:
                payment_ids = users0.get_payments(email=email)
                for payment_id in payment_ids:
                    payment_data = await payment.get_payment(payment_id)
                    payment_data = payment_data.get("result", None)
                    if not payment_data:
                        users0.remove_payment(payment_id, email=email)
                        continue
                    status = payment_data["state"]
                    if status == "COMPLETED":
                        amount = payment_data["amount"]
                        users0.add_balance(amount, email=email)
                        users0.remove_payment(payment_id, email=email)
                        send_mail(email, f"{amount}$ added to your balance")
                    elif status == "DECLINED" or status == "CANCELLED":
                        send_mail(email, f"You payment {payment_id}, declined/cancelled")
                        users.remove_payment(payment_id, email=email)
        for guest in tokens:
            payment_id = guest[0]
            email = guest[1]
            zipname = guest[2]
            payment_data = await payment.get_payment(payment_id)
            payment_data = payment_data.get("result", None)
            if not payment_data:
                continue
            status = payment_data["state"]
            if status == "COMPLETED":
                send_email_attachment(zipname, email)
            elif status == "DECLINED" or status == "CANCELLED":
                send_mail(email, f"You payment {payment_id}, declined/cancelled")
        await asyncio.sleep(30)


async def check_for_bought_products():
    while True:
        for product in users.get_purchases():
            difference = datetime.now() - datetime.fromisoformat(product[2])
            zip_filename = product[6]
            if not zip_filename:
                continue
            zip_path = os.path.join("DB", "bought", zip_filename)
            category_name = product[3]
            if difference.days >= 3 and zip_filename:
                # remove files from our DB
                with zipfile.ZipFile(zip_path, "r") as file:
                    for product_name in file.namelist():
                        os.remove(os.path.join("DB", category_name, product_name))
                        products.remove_product(category_name, product_name)
                users.remove_purchase_archive(zip_filename)
                os.remove(zip_path)

        # every 5 minutes
        await asyncio.sleep(300)


async def change_advertisement():
    while True:
        themes = get_themes()
        # there are any themes and not only default
        print("here")
        if len(themes) != 1:
            print("there")
            ok = False
            # search for next theme
            while not ok:
                next_theme = random.choice(themes)
                # TODO fix cmp files
                for filename in config.AD_FILES:
                    """
                    if filecmp.cmp(os.path.join(config.AD_FOLDER, next_theme, filename),
                                   os.path.join(config.AD_IMG_FOLDER, filename)) != 0:
                    """

                    file1 = open(os.path.join(config.AD_FOLDER, next_theme, filename), "rb")
                    file2 = open(os.path.join(config.AD_IMG_FOLDER, filename), "rb")
                    if file1.read() != file2.read():  # cmp 2 files
                        need_to_copy = open(os.path.join(config.AD_FOLDER, next_theme, filename), "rb")
                        where_to_copy = open(os.path.join(config.AD_IMG_FOLDER, filename), "wb")
                        where_to_copy.write(need_to_copy.read())
                        need_to_copy.close()
                        where_to_copy.close()
                        ok = True
                    file1.close()
                    file2.close()
                if ok:
                    print("copy config")
                    with open(os.path.join(config.AD_FOLDER, next_theme, config.AD_TEXT_FILENAME), "r") as file:
                        with open(os.path.join(config.AD_CURRENT_FOLDER, config.AD_TEXT_FILENAME), "w") as file2:
                            file2.write(file.read())

            await asyncio.sleep(random.randint(10, 60))  # sleep 'till next change
        else:
            # if there are only default theme and current theme is not default -> change theme
            ok = True
            for filename in config.AD_FILES:
                print("cmp0")
                """
                if not filecmp.cmp(os.path.join(config.AD_DEFAULT_FOLDER, filename),
                                   os.path.join(config.AD_IMG_FOLDER, filename)):
               """
                file1 = open(os.path.join(config.AD_DEFAULT_FOLDER, filename), "rb")
                file2 = open(os.path.join(config.AD_IMG_FOLDER, filename), "rb")
                if file1.read() != file2.read():  # cmp 2 files
                    need_to_copy = open(os.path.join(config.AD_DEFAULT_FOLDER, filename), "rb")
                    where_to_copy = open(os.path.join(config.AD_IMG_FOLDER, filename), "wb")
                    where_to_copy.write(need_to_copy.read())
                    need_to_copy.close()
                    where_to_copy.close()
                    ok = False
            if ok:
                await asyncio.sleep(60)  # wait for updates


async def check_advertisement():
    while True:
        themes = get_themes()
        for theme in themes:
            with open(os.path.join(config.AD_FOLDER, theme, config.AD_TEXT_FILENAME)) as file:
                print(os.path.join(config.AD_FOLDER, theme, config.AD_TEXT_FILENAME))
                data = loads(file.read())
                if data["time"]:
                    difference = (datetime.fromisoformat(data["time"]) - datetime.now()).days
                    if difference < 0:
                        shutil.rmtree(os.path.join(config.AD_FOLDER, theme))

        # every 10 minutes
        await asyncio.sleep(600)


async def check_refs():
    while True:
        now = datetime.now()
        # if it is not a last day in month
        if now.day < calendar.monthrange(now.year, now.month)[1]:
            await asyncio.sleep(2160000)  # sleep 10 hours
        else:
            if now.hour >= 20:  # if it is the last 4 hours -> clear referrals
                for referral in tokens.get_all_links():
                    if referral[1]:  # email
                        money = users0.get_ref_balance(email=referral[1])
                        users0.add_ref_balance(-money, email=referral[1])  # remove ref money
                        users0.add_balance(-money, email=referral[1])      # remove from balance N ref money
                    elif referral[2]:  # userID
                        money = users.get_ref_balance(userID=referral[2])
                        users.add_ref_balance(-money, userID=referral[2])  # remove ref money
                        users.add_balance(-money, userID=referral[2])
                tokens.clear_links()
            else:
                await asyncio.sleep(216000)  # sleep 1 hour


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.create_task(check_for_payments())
    loop.create_task(check_for_bought_products())
    loop.create_task(check_refs())
    loop.create_task(change_advertisement())
    loop.create_task(check_advertisement())
    loop.run_forever()
