import os
from zipfile import ZipFile
from datetime import datetime
from json import loads

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import InputFile
from aiogram.utils.exceptions import ChatNotFound

from utils.database import UsersDB, ProductsDB, create_random_filename_zip, Tokens
import utils.keyboards as keyboards
from config import ADMIN_ID, PURCHASE_GIF_FILENAME, AD_CURRENT_FOLDER, AD_TEXT_FILENAME
from handlers import *
from loader import storage


users = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")
tokens = Tokens("DB/tokens.db")


@dp.callback_query_handler(lambda c: int(users.get_banned(userID=c.from_user.id)))
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == "my_profile")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = users.get_language(userID=userID)
    login = callback_query.from_user.mention if callback_query.from_user.username else callback_query.from_user.id
    balance = users.get_balance(userID=userID)
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
    lang = users.get_language(userID=userID)
    if lang == "RU":
        await callback_query.message.answer("Выберите монету", reply_markup=keyboards.COINS_MENU)
    else:
        await callback_query.message.answer("Choose coin", reply_markup=keyboards.COINS_MENU)


@dp.callback_query_handler(lambda c: c.data == "my_preorders")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = users.get_language(userID=userID)
    if lang == "RU":
        await callback_query.message.answer("услуга находится на этапе разработки")
    else:
        await callback_query.message.answer("Developing...")


@dp.callback_query_handler(lambda c: c.data == "preorder")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    lang = users.get_language(userID=callback_query.from_user.id)
    if lang == "RU":
        await bot.send_message(callback_query.from_user.id, "услуга находится на этапе разработки")
    else:
        await bot.send_message(callback_query.from_user.id, "Developing...")



@dp.callback_query_handler(lambda c: c.data == "back_category")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    lang = users.get_language(userID=callback_query.from_user.id)
    if lang == "RU":
        await callback_query.message.edit_text(text="Главное меню")
        await callback_query.message.edit_reply_markup(reply_markup=keyboards.MAIN_MENU_RU)
    else:
        await callback_query.message.edit_text(text="Main menu")
        await callback_query.message.edit_reply_markup(reply_markup=keyboards.MAIN_MENU_EN)


@dp.callback_query_handler(lambda c: c.data == "purchase")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = users.get_language(userID=userID)
    await storage.update_data(user=callback_query.from_user.id, data={"lang": lang})
    kb = InlineKeyboardMarkup(row_width=1)
    if lang == "RU":
        for category in products.get_categories():
            full_category_name = category
            category = category.split("|")[0]
            cat_text = "✅" + category + "✅" if products.get_count_of_products(full_category_name) else category
            kb.add(InlineKeyboardButton(text=cat_text, callback_data="category " + category))
        kb.add(InlineKeyboardButton(text="Назад", callback_data="back_category"))
    else:
        for category in products.get_categories():
            full_category_name = category
            category_en = category.split("|")[1]
            category_ru = category.split("|")[0]
            cat_text = "✅" + category_en + "✅" if products.get_count_of_products(full_category_name) else category_en
            kb.add(InlineKeyboardButton(text=cat_text, callback_data="category " + category_ru))
        kb.add(InlineKeyboardButton(text="Back", callback_data="back_category"))
    if lang == "RU":
        await callback_query.message.edit_text("Выберите категорию", reply_markup=kb)
    else:
        await callback_query.message.edit_text("Choose category", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("category "))
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    category_name = " ".join(callback_query.data.split()[1::])
    full_category_name = None
    for category in products.get_categories():
        if category_name in category:
            full_category_name = category
            break
    userData = await storage.get_data(user=userID)
    userLang = users.get_language(userID=userID)
    userBalance = users.get_balance(userID=userID)
    category_name = full_category_name.split("|")[0] if userLang == "RU" else full_category_name.split("|")[1]
    category_price = products.get_category_price(full_category_name)
    category_desc = products.get_category_description(full_category_name)
    count_of_products = products.get_count_of_products(full_category_name)
    if count_of_products == 0:
        if userLang == "RU":
            await callback_query.message.answer("В данной категории пока нет продуктов")
        else:
            await callback_query.message.answer("No products in this category")
        return
    await storage.update_data(user=userID, data={
        "count_of_products": count_of_products,
        "category_name": full_category_name,
        "category_price": category_price,
        "user_balance": userBalance
    })
    formatted_category_desc = category_desc.replace("+", "\+").replace("-", "\-").replace(".", "\.").replace(",", "\,")
    if userLang == "RU":
        await callback_query.message.answer(f"""
💥{category_name}
*Описание:*
{category_desc.split('|')[0]}
--
*Доступно {count_of_products} товара по {category_price}$ каждый*
*Ваш баланс: {userBalance}$*""".replace("+", "\+").replace("-", "\-").replace(".", "\.").replace(",", "\,"),
                                            parse_mode="MarkdownV2")
        await callback_query.message.answer("Введите количество продуктов")
    else:
        await callback_query.message.answer(f"""
💥{category_name}
*Description:*
{category_desc.split('|')[1]}
--
*Avaliable: {count_of_products} items at {category_price}$ each*
*Your balance: {userBalance}$*""".replace("+", "\+").replace("-", "\-").replace(".", "\.").replace(",", "\,"),
                                            parse_mode="MarkdownV2")
        await callback_query.message.answer("Enter count of products")
    await storage.set_state(user=userID, state="purchase_category_amount")

@dp.message_handler(lambda msg: msg.text.isdigit(), state="purchase_category_amount")
async def _(message: types.Message, state: FSMContext):
    amount = int(message.text)
    userData = await state.get_data()
    userLang = userData["lang"]
    category_price = userData["category_price"]
    if amount <= 0:
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

    kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if userLang == "RU":
        kb.add("Пропустить")
        await message.answer("Введите промокод чтобы воспользоваться промокодом или нажмите кнопку Пропустить",
                             reply_markup=kb)
    else:
        kb.add("Skip")
        await message.answer("Enter promocode or press Skip button",
                             reply_markup=kb)

    await state.update_data(data={"amount": amount})
    await state.set_state("purchase_promocode")


@dp.message_handler(state="purchase_promocode")
async def _(msg: types.Message, state: FSMContext):
    userData = await state.get_data()
    userLang = userData["lang"]
    category_price = userData["category_price"]
    amount = userData["amount"]

    if msg.text.lower() in ["skip", "пропустить"]:
        await state.update_data(data={"coupon": None})
        if userLang == "RU":
            await msg.answer(f"Вы покупаете {amount} продуктов по {category_price}$ каждый.\n"
                                 f"Итоговая стоимость: {amount*category_price}\nВы подтверждаете покупку?(да/нет)",
                                 reply_markup=types.ReplyKeyboardRemove())
        else:
            await msg.answer(f"You purchase {amount} products, which costs {category_price}$\n"
                                 f"Final price: {amount*category_price}\nPurchase?(yes/no)",
                                 reply_markup=types.ReplyKeyboardRemove())
        await state.set_state("purchase_accept")
    else:
        coupon_name = msg.text
        coupon = products.get_coupon(coupon_name)
        if coupon:
            discount = f"%{coupon[2]}" if coupon[1] == "percent" else f"${coupon[2]}"
            await state.update_data(data={"coupon": coupon})
            await state.set_state("purchase_accept")
            if coupon[1] == "percent":
                discount = f"%{coupon[2]}"
                if userLang == "RU":
                    await msg.answer(f"Вы ввели промокод на {discount}")
                    await msg.answer(f"Вы покупаете {amount} продуктов по {category_price}$ каждый.\n"
                                         f"Итоговая стоимость: {(category_price * amount) - (category_price * amount * coupon[2]/100)}\nВы подтверждаете покупку?(да/нет)",
                                         reply_markup=types.ReplyKeyboardRemove())
                else:
                    await msg.answer(f"You entered promocode to {discount}")
                    await msg.answer(f"You purchase {amount} products, which costs {category_price}$\n"
                                         f"Final price: {(category_price * amount) - (category_price * amount * coupon[2]/100)}\nPurchase?(yes/no)",
                                         reply_markup=types.ReplyKeyboardRemove())
            else:
                discount = f"${coupon[2]}"
                if userLang == "RU":
                    await msg.answer(f"Вы ввели промокод на {discount}")
                    await msg.answer(f"Вы покупаете {amount} продуктов по {category_price}$ каждый.\n"
                                     f"Итоговая стоимость: {(category_price * amount) - coupon[2]}\nВы подтверждаете покупку?(да/нет)",
                                     reply_markup=types.ReplyKeyboardRemove())
                else:
                    await msg.answer(f"You entered promocode to {discount}")
                    await msg.answer(f"You purchase {amount} products, which costs {category_price}$\n"
                                     f"Final price: {(category_price * amount) - coupon[2]}\nPurchase?(yes/no)",
                                     reply_markup=types.ReplyKeyboardRemove())
        else:
            if userLang =="RU":
                await msg.answer("Такого промокода нет. Повторите попытку или пропустите этот шаг")
                await state.set_state("purchase_promocode")
            else:
                await msg.answer("No such promocode. Try again or skip this step")
                await state.set_state("purchase_promocode")


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
        coupon = userData["coupon"]
        if userBalance >= amount * category_price:
            if coupon:
                if coupon[1] == "sum":
                    users.add_balance(coupon[2], userID=userID)
                    price = category_price * amount
                elif coupon[1] == "percent":
                    # price - discount
                    price = (category_price * amount) - (category_price * amount * coupon[2]/100)
                products.remove_coupon(coupon[0])
            users.add_balance(-price, userID=userID)
            zip_filename = create_random_filename_zip()
            zip_path = os.path.join("DB", "bought", zip_filename)
            zipObj = ZipFile(zip_path, "w")
            for file in products.get_N_products(category_name, amount):
                path = os.path.join("DB", category_name, file[0])
                zipObj.write(path, os.path.basename(path))
                products.set_isBought(file[0], category_name)
            zipObj.close()
            await message.answer_document(InputFile(zip_path))
            users.add_purchase(category_name, amount, category_price*amount, zip_filename, userID=userID)
            with open(os.path.join(AD_CURRENT_FOLDER, AD_TEXT_FILENAME), "r") as file:
                texts = loads(file.read())
            if userLang == "RU":
                await message.answer("Спасибо за покупку!\n"
                                     "Время работы поддержки @fbfarmpro 09:00-19:00 gmt+3.",
                                     reply_markup=keyboards.MAIN_MENU_RU)
                await message.answer(texts["ru"])
            else:
                await message.answer("Thank you for purchase!"
                                     "Support hours @fbfarmpro 09:00-19:00 gmt+3.",
                                     reply_markup=keyboards.MAIN_MENU_EN)
                await message.answer(texts["en"])
            await message.answer_animation(InputFile(PURCHASE_GIF_FILENAME))
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
    lang = users.get_language(userID=callback_query.from_user.id)
    if lang == "RU":
        await callback_query.message.answer("""
❗️Гарантия❗️

🛑 Замена осуществляется лишь в том случае, если аккаунт не подвергался изменениям со стороны покупателя. 🛑
🕐 Аккаунты проверяются сразу после покупки. Время на проверку и запроса на замену товара ограничено — 3 дня после покупки. При возникновении проблем сразу же сообщайте в поддержку @fbfarmpro (09:00-19:00 gmt+3). 🕐
🔴 Для получения замены требуется предоставить :
- Причину замены.
- Скриншот.
- Исходный файл, предоставленный магазином.
💬 Поддержка имеет полное право отказать в замене, в случае если покупатель:
- Сделал запрос на замену по истечению 3-х дней после покупки аккаунта.  
⛔️ Не проверяйте купленные аккаунты паблик-чекером, паблик-проксями, иначе их могут заблокировать! ⛔️
❌ Принятый товар возврату не подлежит, замена только аккаунтами.
❗️ Приобретайте то количество, которое сможете использовать в ближайшее время.
❗️ Покупайте аккаунты только в том случае, если Вы умеете и знаете как ими пользоваться!
🚫 В случае, если Вас заблокировали во время фарма, это не является основанием для замены!
⚠️ В случае, если почта в комплекте в блокировке - это не основание для замены аккаунта фейсбук.
⚠️ В случае, если вы привязали карту в биллинге и получили блокировку, это не основание для замены аккаунта.
⚠️ В случае, если после создания fanpage, business manager, ваш аккаунт заблокировали, это не основание для замены. (Часто это является триггером для аккаунта на новом железе).
❗️ Фармом аккаунта подразумевается любые действие на аккаунте.
⚠️ В случае, если на аккаунте фейсбук не получается создать business manager - это не основание для замены аккаунта.
🔞 В случае, если вы привязали к аккаунту business manager и по каким либо причинам фейсбук не дает вам полноценно работать с business manager (привязывать туда рекламные кабинеты и прочее, пишите в техническую поддержку фейсбука) - это не основание для замены аккаунта.
""")
    else:
        await callback_query.message.answer("""
❗️Warranty❗️

🛑 Replacement only if the account has not been modified by the buyer. 🛑
🕐 Accounts are checked immediately after purchase. The time to check and request a replacement is limited to 3 days after purchase. Report to support @fbfarmpro (09:00-19:00 gmt+3) immediately if you have any problems. 🕐
🔴 A replacement is required to provide :
- Reason for Substitution.
- Screenshot.
- Original file provided by the store.
💬 Support has the full right to refuse a replacement if the customer:
- Made a request for a replacement after 3 days after purchasing the account.  
⛔️ Do not check purchased accounts with public checker, public proxies, otherwise they can be blocked! ⛔️
❌ Received merchandise cannot be returned, replacement only with accounts.
❗️ Purchase as much as you can use in the near future.
❗️ Buy accounts only if you know how to use them!
🚫 In case you get blocked while farming, this is not grounds for replacement!
⚠️ In the event that your mail is bundled in a blocked account, this is not grounds for a replacement Facebook account.
⚠️ In case you linked a card in billing and got a lock, that's not grounds for replacing the account.
⚠️ If your account is blocked after creating a fanpage, business manager, this is not grounds for replacement. (This is often a trigger for an account on new iron).
❗️ Farming an account means any action on the account.
⚠️ If you can't create a business manager on a Facebook account, that's not a reason to replace the account.
If you have linked business manager to your account and for some reason Facebook does not let you fully work with business manager (link advertising accounts there, etc., write to Facebook technical support) - this is not the reason for account replacement.
""")


@dp.callback_query_handler(lambda c: c.data == "referral")
async def _(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    userID = call.from_user.id
    userLang = users.get_language(userID=userID)
    link = tokens.get_link_by_user(userID=userID)
    link = link[0] if link else None
    if not link:
        link = tokens.add_link(userID=userID)
    usages = tokens.get_link_usages(link)
    if userLang == "RU":
        await call.message.answer(f"Ваша реферальная ссылка:\nhttps://t.me/fbfarmprobot?start={link}\n{'АКТИВНАЯ' if usages < 5 else 'ИСТЕКШАЯ'} ({usages}/5)")
    else:
        await call.message.answer(f"Your referral link is:\nhttps://t.me/fbfarmprobot?start={link}\n{'ACTIVE' if usages < 5 else 'EXPIRED'} ({usages}/5)")


@dp.callback_query_handler(lambda c: c.data == "purchase_history")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = str(callback_query.from_user.id)
    lang = users.get_language(userID=userID)
    purchases = users.get_purchase_history(userID=userID)
    if purchases:
        if lang == "RU":
            result = f"\n\n".join(f"Дата: {t[2]}\nКатегория: {t[3].split('|')[0]}\nКоличество: {t[4]}\nЦена: {t[5]}" for t in purchases)
        else:
            result = f"\n\n".join(f"Date: {t[2]}\nCategory: {t[3].split('|')[-1]}\nAmount: {t[4]}\nPrice: {t[5]}" for t in purchases)
        await callback_query.message.answer(result)
    else:
        if lang == "RU":
            await callback_query.message.answer("Ваша история покупок пуста")
        else:
            await callback_query.message.answer("Your purchase history is empty")



@dp.callback_query_handler(lambda c: c.data == "language")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    lang = users.get_language(userID=userID)
    if lang == "RU":
        await callback_query.message.edit_text("Main menu")
        await callback_query.message.edit_reply_markup(keyboards.MAIN_MENU_EN)
    else:
        await callback_query.message.edit_text("Главное меню")
        await callback_query.message.edit_reply_markup(keyboards.MAIN_MENU_RU)
    users.change_language(userID=userID)
