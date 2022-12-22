import os
from zipfile import ZipFile
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import InputFile
from aiogram.utils.exceptions import ChatNotFound

import utils.database as database
import utils.keyboards as keyboards
from config import ADMIN_ID
from handlers import *
from loader import storage


@dp.callback_query_handler(lambda c: int(database.users.get_banned(userID=c.from_user.id)))
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == "my_profile")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = database.users.get_language(userID=userID)
    login = callback_query.from_user.mention if callback_query.from_user.username else callback_query.from_user.id
    balance = database.users.get_balance(userID=userID)
    if lang == "RU":
        await bot.send_message(userID, f"Ваш логин: {login}\nВаш баланс: `{balance} USD`",
                                   parse_mode="MarkdownV2")
    else:
        await bot.send_message(userID, f"Your login: {login}\nYour balance: `{balance} USD`",
                               parse_mode="MarkdownV2")


@dp.callback_query_handler(lambda c: c.data == "add_balance")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = database.users.get_language(userID=userID)
    if lang == "RU":
        await callback_query.message.answer("Выберите монету", reply_markup=keyboards.COINS_MENU)
    else:
        await callback_query.message.answer("Choose coin", reply_markup=keyboards.COINS_MENU)


@dp.callback_query_handler(lambda c: c.data == "my_preorders")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    lang = database.users.get_language(userID=userID)
    if lang == "RU":
        await bot.send_message(callback_query.from_user.id, "услуга находится на этапе разработки")
    else:
        await bot.send_message(callback_query.from_user.id, "Developing...")


@dp.callback_query_handler(lambda c: c.data == "preorder")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "услуга находится на этапе разработки")


@dp.callback_query_handler(lambda c: c.data == "purchase")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = database.users.get_language(userID=userID)
    await storage.update_data(user=callback_query.from_user.id, data={"lang": lang})
    kb = InlineKeyboardMarkup(row_width=1)
    for category in database.products.get_categories():
        cat_text = "✅" + category + "✅" if database.products.get_count_of_products(category) else category
        kb.add(InlineKeyboardButton(text=cat_text, callback_data="purchase_category " + category))
    if lang == "RU":
        await callback_query.message.edit_text("Выберите категорию", reply_markup=kb)
    else:
        await callback_query.message.edit_text("Choose category", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("purchase_category"))
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    category_name = callback_query.data.split()[-1]
    userData = await storage.get_data(user=userID)
    userLang = userData["lang"]
    userBalance = database.users.get_balance(userID=userID)
    category_price = database.products.get_category_price(category_name)
    count_of_products = database.products.get_count_of_products(category_name)
    if count_of_products == 0:
        if userLang == "RU":
            await callback_query.message.answer("В данной категории пока нет продуктов")
        else:
            await callback_query.message.answer("No products in this category")
        return
    await storage.update_data(user=userID, data={
        "count_of_products": count_of_products,
        "category_name": category_name,
        "category_price": category_price,
        "user_balance": userBalance
    })
    if userLang == "RU":
        await callback_query.message.answer(f"{category_name}\nДоступно {count_of_products} продуктов по {category_price}$ каждый\n"
                                            f"Ваш баланс: {userBalance}")
        await callback_query.message.answer("Введите количество продуктов")
    else:
        await callback_query.message.answer(f"{category_name}\nThere are {count_of_products} products, which costs {category_price}$\n"
                                            f"Your balance: {userBalance}")
        await callback_query.message.answer("Enter count of products")
    await storage.set_state(user=userID, state="purchase_category_amount")

@dp.message_handler(lambda msg: msg.text.isdigit() and int(msg.text) != 0, state="purchase_category_amount")
async def _(message: types.Message, state: FSMContext):
    amount = int(message.text)
    userData = await state.get_data()
    userLang = userData["lang"]
    category_price = userData["category_price"]
    if amount == 0:
        if userLang == "RU":
            await message.answer("Минимум 1")
        else:
            await message.answer("Min 1")
        await state.set_state("purchase_category_amount")
        return
    elif amount > int(userData["count_of_products"]):
        amount = int(userData["count_of_products"])
        if userLang == "RU":
            await message.answer(f"В этой категории всего {amount} продуктов. Ставлю такой лимит")
        else:
            await message.answer(f"There are only {amount} in this category. Limit changed")

    if userLang == "RU":
        await message.answer(f"Вы покупаете {amount} продуктов по {category_price}$ каждый.\n"
                             f"Итоговая стоимость: {amount*category_price}\nВы подтверждаете покупку?(да/нет)")
    else:
        await message.answer(f"You purchase {amount} products, which costs {category_price}$\n"
                             f"Final price: {amount*category_price}\nPurchase?(yes/no)")

    await state.update_data(data={"amount": amount})

    await state.set_state("purchase_accept")


@dp.message_handler(lambda msg: msg.text.lower() in ["да", "yes", "no", "нет"], state="purchase_accept")
async def _(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userData = await state.get_data()
    await state.finish()
    userLang = userData["lang"]
    userBalance = userData["user_balance"]
    amount = userData["amount"]
    category_price = userData["category_price"]
    category_name = userData["category_name"]
    if message.text.lower() in ["да", "yes"]:
        if userBalance >= amount * category_price:
            database.users.add_balance(-(category_price * amount), userID=userID)
            zip_filename = database.create_random_filename_zip()
            zip_path = os.path.join("DB", "bought", zip_filename)
            zipObj = ZipFile(zip_path, "w")
            for file in database.products.get_N_products(category_name, amount):
                path = os.path.join("DB", category_name, file[0])
                zipObj.write(path, os.path.basename(path))
                database.products.set_isBought(file[0], category_name)
            zipObj.close()
            await message.answer_document(InputFile(zip_path))
            database.users.add_purchase(category_name, amount, category_price*amount, zip_filename, userID=userID)
            if userLang == "RU":
                await message.answer("Спасибо за покупку!\n"
                                     "Время работы поддержки @fbfarmpro 09:00-19:00 gmt+3.",
                                     reply_markup=keyboards.MAIN_MENU_RU)
            else:
                await message.answer("Thank you for purchase!"
                                     "Support hours @fbfarmpro 09:00-19:00 gmt+3.",
                                     reply_markup=keyboards.MAIN_MENU_EN)
            await message.answer_animation(InputFile(config.PURCHASE_GIF_FILENAME))
            for admin in ADMIN_ID:
                try:
                    await bot.send_message(admin, text=f"{message.from_user.mention if message.from_user.username else userID} "
                                                       f"purchased {amount} files\n"
                                                       f"category: {category_name}\n"
                                                       f"price: {category_price*amount}$\n"
                                                       f"time: {datetime.now().isoformat()}")
                except ChatNotFound:
                    continue
        else:
            if userLang == "RU":
                await message.answer("Не хватает денег.", reply_markup=keyboards.MAIN_MENU_RU)
            else:
                await message.answer("Not enough money", reply_markup=keyboards.MAIN_MENU_EN)
    else:
        if userLang == "RU":
            await message.answer("Ок.", reply_markup=keyboards.MAIN_MENU_RU)
        else:
            await message.answer("Okay.", reply_markup=keyboards.MAIN_MENU_EN)


@dp.callback_query_handler(lambda c: c.data == "rules")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    lang = database.users.get_language(userID=callback_query.from_user.id)
    if lang == "RU":
        await callback_query.message.answer("""
        Гарантия:
1.1 Замена осуществляется лишь в том случае, если аккаунт не подвергался изменениям со стороны покупателя.
1.2. Аккаунты проверяются сразу после покупки. Время на проверку и запроса на замену товара ограничено — 3 дня после покупки. При возникновении проблем сразу же сообщайте в поддержку @fbfarmpro (09:00-19:00 gmt+3).
1.3 Для получения замены требуется предоставить :
- Причину замены.
- Скриншот.
- Исходный файл, предоставленный магазином.
1.4 Поддержка имеет полное право отказать в замене, в случае если покупатель:
-Сделал запрос на замену по истечению 3-х дней после покупки аккаунта.  
-Не придерживался пункта 1.3.
2. Не проверяйте купленные аккаунты паблик-чекером, паблик-проксями, иначе их могут заблокировать!
3. Принятый товар возврату не подлежит, замена только аккаунтами.
4. Приобретайте то количество, которое сможете использовать в ближайшее время.
5. Покупайте аккаунты только в том случае, если Вы умеете и знаете как ими пользоваться!
6. В случае, если Вас заблокировали во время фарма, это не является основанием для замены!
7. В случае, если почта в комплекте в блокировке - это не основание для замены аккаунта фейсбук.
8. В случае, если вы привязали карту в биллинге и получили блокировку, это не основание для замены аккаунта.
9. В случае, если после создание fanpage, business manager, ваш аккаунт заблокировали, это не основание для замены. (Часто это является триггером для аккаунта на новом железе).
10. Фармом аккаунта подразумевается любые действие на аккаунте.
11. В случае, если на аккаунте фейбсук не получается создать business manager - это не основание для замены аккаунта.
12. В случае, если вы привязали к аккаунту business manager и по каким либо причинам фейсбук не дает вам полноценно работать с business manager (привязывать туда рекламные кабинеты и прочее, пишите в техническую поддержку фейсбука) - это не основание для замены аккаунта.
""")
    else:
        await callback_query.message.answer("""
        Warranty:
1.1 Replacement is only if the account has not been altered by the buyer.
1.2 Accounts are checked immediately after purchase. The time for checking and requesting a replacement is limited to 3 days after purchase. If there are any problems immediately report to support @fbfarmpro (09:00-19:00 gmt+3).
1.3 In order to receive a replacement, you are required to provide :
- The reason for the replacement.
- Screenshot.
- The original file provided by the store.
1.4 Support has the full right to refuse a replacement if the buyer:
-Made a request for a replacement after 3 days after the purchase of the account.  
-Did not adhere to paragraph 1.3.
2. Do not check bought accounts public checker, public proxies, otherwise they can be blocked!
3. Accepted merchandise cannot be returned, replacement only with accounts.
4. Purchase the amount you can use in the near future.
5. Buy accounts only if you know how and know how to use them!
6. If you were blocked during farming, this is not grounds for replacement!
7. In the event that the mail is bundled in the blocking - this is not grounds for the replacement of the Facebook account.
8. In case you linked a card in billing and got blocked, this is not grounds for account replacement.
9. In case you got your account blocked after creating a fanpage, business manager, this is not grounds for replacement. (This is often a trigger for an account on new hardware).
10. Account farming refers to any action on the account.
11. If you can't create a business manager on the account, that's not grounds for account replacement.
12. If you have linked business manager to your account and for some reason Facebook does not allow you to fully work with business manager (linking advertising accounts there, etc., please contact Facebook technical support) - this is not grounds for account replacement.
""")


@dp.callback_query_handler(lambda c: c.data == "purchase_history")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = str(callback_query.from_user.id)
    lang = database.users.get_language(userID=userID)
    purchases = filter(lambda t: t[1] == userID, database.users.get_purchases())
    if purchases:
        if lang == "RU":
            result = f"\n\n".join(f"Дата: {t[1]}\nКатегория: {t[2]}\nКатегория: {t[3]}\nЦена: {t[4]}" for t in purchases)
            await callback_query.message.answer(result or "Ваша история покупой пуста")
        else:
            result = f"\n\n".join(f"Date: {t[1]}\nCategory: {t[2]}\nAmount: {t[3]}\nPrice: {t[4]}" for t in purchases)
            await callback_query.message.answer(result or "Your purchase history is empty")


@dp.callback_query_handler(lambda c: c.data == "help")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("@fbfarmpro")


@dp.callback_query_handler(lambda c: c.data == "language")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = database.users.get_language(userID=userID)
    if lang == "RU":
        await callback_query.message.edit_text("Main menu")
        await callback_query.message.edit_reply_markup(keyboards.MAIN_MENU_EN)
    else:
        await callback_query.message.edit_text("Главное меню")
        await callback_query.message.edit_reply_markup(keyboards.MAIN_MENU_RU)
    database.users.change_language(userID=userID)
