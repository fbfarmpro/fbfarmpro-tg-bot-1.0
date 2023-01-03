import config
from handlers import *
from aiogram import types
import utils.keyboards as keyboards
from utils.database import UsersDB, ProductsDB
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from json import loads, dumps
from loader import storage
from aiogram.utils.exceptions import BotBlocked, FileIsTooBig
import os


users = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")


@dp.callback_query_handler(lambda c: c.data == "back")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.ADMIN_MENU)


@dp.callback_query_handler(lambda c: c.data == "purchase_gif_change")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Send me gif")
    await storage.set_state(user=callback_query.from_user.id, state="purchase_gif_data")


@dp.message_handler(state="purchase_gif_data", content_types=["animation"])
async def _(message: types.Message, state: FSMContext):
    await message.animation.download(destination="purchase_gif.gif")
    await message.answer("Success.")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "greeting_msg")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.GREETING_MSG_MENU)


@dp.callback_query_handler(lambda c: c.data == "greeting_msg_edit_ru")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer(f"send text for russian greeting message "
                                        f"(send {config.GREETING_NO_TEXT} to disable)")
    await storage.set_state(user=callback_query.from_user.id, state="edit_msg_ru")


@dp.callback_query_handler(lambda c: c.data == "greeting_msg_edit_en")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer(f"send text for english greeting message "
                                        f"(send {config.GREETING_NO_TEXT} to disable)")
    await storage.set_state(user=callback_query.from_user.id, state="edit_msg_en")


@dp.message_handler(state="edit_msg_ru")
async def _(message: types.Message, state: FSMContext):
    try:
        with open(config.GREETING_MSG_FILENAME) as file:
            content = loads(file.read())
    except FileNotFoundError:
        content = {"ru": {"text": None, "gif": None}, "en": {"text": None, "gif": None}}
    content["ru"]["text"] = message.text if message.text.lower() != config.GREETING_NO_TEXT else None
    with open(config.GREETING_MSG_FILENAME, "w") as file:
        file.write(dumps(content, indent=2))
    await message.answer("Success. Now send me please gif")
    await storage.set_state(user=message.from_user.id, state="edit_msg_gif_ru")


@dp.message_handler(state="edit_msg_en")
async def _(message: types.Message, state: FSMContext):
    try:
        with open(config.GREETING_MSG_FILENAME) as file:
            content = loads(file.read())
    except FileNotFoundError:
        content = {"ru": {"text": None, "gif": None}, "en": {"text": None, "gif": None}}
    content["en"]["text"] = message.text if message.text.lower() != config.GREETING_NO_TEXT else None
    with open(config.GREETING_MSG_FILENAME, "w") as file:
        file.write(dumps(content, indent=2))
    await message.answer("Success. now send me gif")
    await storage.set_state(user=message.from_user.id, state="edit_msg_gif_en")


@dp.message_handler(state="edit_msg_gif_ru", content_types=["animation", "document"])
async def _(message: types.Message, state: FSMContext):
    if message.content_type == "animation":
        await message.animation.download(destination=config.GREETING_MSG_GIF_RU_FILENAME)
    else:
        try:
            await message.document.download(destination=config.GREETING_MSG_GIF_RU_FILENAME)
        except FileIsTooBig:
            await message.answer("File is too big")
            await state.set_state("edit_msg_gif_ru")
            return
    with open(config.GREETING_MSG_FILENAME) as file:
        content = loads(file.read())
    content["ru"]["gif"] = config.GREETING_MSG_GIF_RU_FILENAME
    with open(config.GREETING_MSG_FILENAME, "w") as file:
        file.write(dumps(content, indent=2))
    await message.answer("Success.")
    await state.finish()


@dp.message_handler(state="edit_msg_gif_en", content_types=["animation", "document", "photo", "video"])
async def _(message: types.Message, state: FSMContext):
    if message.content_type == "animation":
        await message.animation.download(destination=config.GREETING_MSG_GIF_EN_FILENAME)
    else:
        try:
            await message.document.download(destination=config.GREETING_MSG_GIF_EN_FILENAME)
        except FileIsTooBig:
            await message.answer("File is too big")
            await state.set_state("edit_msg_gif_ru")
            return
    with open(config.GREETING_MSG_FILENAME) as file:
        content = loads(file.read())
    content["en"]["gif"] = config.GREETING_MSG_GIF_EN_FILENAME
    with open(config.GREETING_MSG_FILENAME, "w") as file:
        file.write(dumps(content, indent=2))
    await message.answer("Success.")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "greeting_msg_preview_ru")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    try:
        with open(config.GREETING_MSG_FILENAME) as file:
            content = loads(file.read())
        await callback_query.message.answer("preview of russian greeting message:")
        await callback_query.message.answer(content["ru"]["text"])
    except FileNotFoundError:
        await callback_query.message.answer("you didn't add greeting_ru msg")


@dp.callback_query_handler(lambda c: c.data == "greeting_msg_preview_en")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    try:
        with open(config.GREETING_MSG_FILENAME) as file:
            content = loads(file.read())
        await callback_query.message.answer("preview of english greeting message:")
        await callback_query.message.answer(content["en"]["text"])
    except FileNotFoundError:
        await callback_query.message.answer("you didn't add greeting_ru msg")


@dp.callback_query_handler(lambda c: c.data == "mailing")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.MAILING_MENU)


async def show_mailing(message: types.Message):
    userID = message.from_user.id
    data = await storage.get_data(user=userID)

    if data.get("keyboard", 0):
        kb = InlineKeyboardMarkup()
        for button in data["keyboard"]:
            kb.add(InlineKeyboardButton(button["text"], url=button["url"]))
    else:
        kb = None
    text = f"""text:\n{data.get('text', 'You did not specify text')}
disable notification: {data.get('disable_sound', False)}
protect content: {data.get('protect_content', False)}
priority: {data.get('priority', 'user')}
"""
    await message.answer("Preview:")
    if data.get("animation", 0):
        await message.answer_animation(caption=text,
                                       disable_notification=data.get("disable_sound", False),
                                       protect_content=data.get("protect_content", False),
                                       reply_markup=kb,
                                       animation=data["animation"])
    elif data.get("photo", 0):
        await message.answer_photo(caption=text,
                                   disable_notification=data.get("disable_sound", False),
                                   protect_content=data.get("protect_content", False),
                                   reply_markup=kb,
                                   photo=data["photo"])
    else:
        await message.answer(text=text,
                             disable_notification=data.get("disable_sound", False),
                             protect_content=data.get("protect_content", False),
                             reply_markup=kb)
    await message.answer("What do you want to do next", reply_markup=keyboards.MAILING_MENU)


@dp.callback_query_handler(lambda c: c.data == "mailing_sound")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    data = await storage.get_data(user=userID)
    if not data.get("disable_sound", 0):
        await storage.update_data(user=callback_query.from_user.id, data={"disable_sound": True})
        await callback_query.message.answer("sound successfully disabled")
    else:
        await storage.update_data(user=callback_query.from_user.id, data={"disable_sound": False})
        await callback_query.message.answer("sound successfully enabled")
    await show_mailing(callback_query.message, )


@dp.callback_query_handler(lambda c: c.data == "mailing_protect_content")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    data = await storage.get_data(user=userID)
    if not data.get("protect_content", 0):
        await storage.update_data(user=userID, data={"protect_content": True})
        await callback_query.message.answer("protect content enabled")
    else:
        await storage.update_data(user=userID, data={"protect_content": False})
        await callback_query.message.answer("protect content disabled")
    await show_mailing(callback_query.message)


@dp.callback_query_handler(lambda c: c.data == "mailing_change_buttons")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.MAILING_CHANGE_BUTTONS_MENU)
    await show_mailing(callback_query.message)


@dp.callback_query_handler(lambda c: c.data == "mailing_change_buttons_add")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("send some text")
    await storage.set_state(user=callback_query.from_user.id, state="mailing_btn_add_text")


@dp.message_handler(state="mailing_btn_add_text")
async def _(message: types.Message, state: FSMContext):
    await storage.update_data(user=message.from_user.id, data={"btn_text": message.text})
    await message.answer("send url for button")
    await state.set_state("mailing_btn_add_url")


@dp.message_handler(state="mailing_btn_add_url")
async def _(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    data = await storage.get_data(user=userID)
    btn = dict(text=data["btn_text"], url=message.text)
    if data.get("keyboard", 0):
        data["keyboard"].append(btn)
    else:
        data["keyboard"] = [btn]
    data["btn_text"] = None
    # crutch
    await state.finish()
    await storage.update_data(user=userID, data=data)
    await message.answer(f"Button successfully added")
    await show_mailing(message)


@dp.callback_query_handler(lambda c: c.data == "mailing_change_buttons_del")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("send text in button")
    await storage.set_state(user=callback_query.from_user.id, state="mailing_btn_del")


@dp.message_handler(state="mailing_btn_del")
async def _(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data.get("keyboard", 0):
            for i, btn in enumerate(data["keyboard"]):
                if btn["text"] == message.text:
                    # data["keyboard"].pop(btn)
                    del data["keyboard"][i]
                    break
    userID = message.from_user.id
    data = await storage.get_data(user=userID)
    await state.finish()
    await storage.update_data(user=userID, data=data)
    await message.answer("successfully deleted button")
    await show_mailing(message)


@dp.callback_query_handler(lambda c: c.data == "mailing_change_buttons_back")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.MAILING_MENU)


@dp.callback_query_handler(lambda c: c.data == "mailing_change_text")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("send some text")
    await storage.set_state(user=callback_query.from_user.id, state="mailing_text")


@dp.message_handler(state="mailing_text")
async def _(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    await storage.update_data(user=userID, data={"text": message.text})
    await message.answer("Successfully changed text")

    # crutch. After state.finish all user data clears. I should rewrite it again
    data = await storage.get_data(user=userID)
    # I should do state.finish because I want to give user ability to press inline keyboard buttons
    await state.finish()
    await storage.update_data(user=userID, data=data)
    await show_mailing(message)


@dp.callback_query_handler(lambda c: c.data == "mailing_add_media")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("send photo/gif")
    await storage.set_state(user=callback_query.from_user.id, state="mailing_add_media")


@dp.message_handler(content_types=["photo", "animation"], state="mailing_add_media")
async def _(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    data = await storage.get_data(user=userID)
    await state.finish()
    if message.content_type == "animation":
        data["animation"] = message.animation.file_id
        data["photo"] = None
    else:
        data["photo"] = message.photo[0].file_id
        data["animation"] = None
    await storage.update_data(user=userID, data=data)
    await message.answer("successfully added media")
    await show_mailing(message)


@dp.callback_query_handler(lambda c: c.data == "mailing_preview")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    data = await storage.get_data(user=userID)
    if not data.get("text", 0):
        await callback_query.message.answer("You must specify message content")
        return
    if data.get("keyboard", 0):
        kb = InlineKeyboardMarkup()
        for button in data["keyboard"]:
            kb.add(InlineKeyboardButton(button["text"], url=button["url"]))
    else:
        kb = None
    await callback_query.message.answer("Preview:")
    if data.get("animation", 0):
        await callback_query.message.answer_animation(caption=data["text"],
                                                      disable_notification=data.get("disable_sound", False),
                                                      protect_content=data.get("protect_content", False),
                                                      reply_markup=kb,
                                                      animation=data["animation"])
    elif data.get("photo", 0):
        await callback_query.message.answer_photo(caption=data["text"],
                                                  disable_notification=data.get("disable_sound", False),
                                                  protect_content=data.get("protect_content", False),
                                                  reply_markup=kb,
                                                  photo=data["photo"])
    else:
        await callback_query.message.answer(data["text"],
                                            disable_notification=data.get("disable_sound", False),
                                            protect_content=data.get("protect_content", False),
                                            reply_markup=kb)
    text = f"""
disable notification: {data.get('disable_sound', False)}
protect content: {data.get('protect_content', False)}
priority: {data.get('priority', 'user')}
"""
    await callback_query.message.answer(f"Properties:\n{text}")


@dp.callback_query_handler(lambda c: c.data == "mailing_priority")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.from_user.id
    data = await storage.get_data(user=userID)
    if data.get("priority", "user") == "user":
        await storage.update_data(user=userID, data={"priority": "regular customer"})
        await callback_query.message.answer("priority: regular customer")
    else:
        await storage.update_data(user=userID, data={"priority": "user"})
        await callback_query.message.answer("priority: user")
    await show_mailing(callback_query.message)


@dp.callback_query_handler(lambda c: c.data == "mailing_start")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    data = await storage.get_data(user=callback_query.from_user.id)

    if not data.get("text", 0):
        await callback_query.message.answer("You must specify message content")
        return

    if data.get("keyboard", 0):
        kb = InlineKeyboardMarkup()
        for button in data["keyboard"]:
            kb.add(InlineKeyboardButton(button["text"], url=button["url"]))
    else:
        kb = None

    await callback_query.message.answer("starting mailing...")
    disable_notification = data.get("disable_sound", False)
    protect_content = data.get("protect_content", False)
    text = data["text"]
    if data.get("priority", "user") == "user":
        if data.get("animation", 0):
            animation = data["animation"]
            for user in users:
                await bot.send_animation(chat_id=user[1],
                                         caption=text,
                                         disable_notification=disable_notification,
                                         protect_content=protect_content,
                                         reply_markup=kb,
                                         animation=animation)
        elif data.get("photo", 0):
            photo = data["photo"]
            for user in users:
                await bot.send_photo(chat_id=user[0],
                                     caption=text,
                                     disable_notification=disable_notification,
                                     protect_content=protect_content,
                                     reply_markup=kb,
                                     photo=photo)
        else:
            for user in users:
                await bot.send_message(chat_id=user[0],
                                       text=text,
                                       disable_notification=data.get("disable_sound", False),
                                       protect_content=data.get("protect_content", False),
                                       reply_markup=kb)
    else:
        if data.get("animation", 0):
            animation = data["animation"]
            for user in users.get_regular_customers():
                await bot.send_animation(chat_id=user[0],
                                         caption=text,
                                         disable_notification=disable_notification,
                                         protect_content=protect_content,
                                         reply_markup=kb,
                                         animation=animation)
        elif data.get("photo", 0):
            photo = data["photo"]
            for user in users.get_regular_customers():
                await bot.send_photo(chat_id=user[0],
                                     caption=text,
                                     disable_notification=disable_notification,
                                     protect_content=protect_content,
                                     reply_markup=kb,
                                     photo=photo)
        else:
            for user in users.get_regular_customers():
                await bot.send_message(chat_id=user[0],
                                       text=text,
                                       disable_notification=data.get("disable_sound", False),
                                       protect_content=data.get("protect_content", False),
                                       reply_markup=kb)
    await callback_query.message.answer("Mailing done.")


@dp.callback_query_handler(lambda c: c.data == "statistic")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    count_of_users = users.get_count_of_users()
    count_of_regular_customers = users.get_count_of_regular_customers()
    banned_by_admins_users = users.get_count_of_banned()
    total_cost_of_products = products.get_total_cost_of_products()
    total_products = len(products.get_all_products())
    purchases_sum = sum(int(data[4]) for data in users.get_purchases())
    purchases_count = len(users.get_purchases())
    users_who_ban_bot = 0
    """
    purchases_sum = 0
    for purchase in users.get_purchases():
        purchases_sum += int(purchase[4])
    """
    for user in users:
        try:
            await bot.send_message(user[0], "Проводим тестирование кто забанил бота."
                                            "Если вы получили это сообщение, то вы молодец")
        except (BotBlocked, ChatNotFound) as _:
            users_who_ban_bot += 1

    who_ban_bot_count = (users_who_ban_bot/count_of_users)*100

    await callback_query.message.answer(f"users: {count_of_users}\n"
                                        f"who ban bot: {users_who_ban_bot} ({who_ban_bot_count}%)\n"
                                        f"who not ban bot: {count_of_users-users_who_ban_bot} ({100-who_ban_bot_count}%)\n"
                                        f"banned by admins: {banned_by_admins_users}\n"
                                        f"total count of products: {total_products}\n"
                                        f"total cost of products: {total_cost_of_products}\n"
                                        f"regular: {count_of_regular_customers}\n"
                                        f"purchases count: {purchases_count}\n"
                                        f"purchases sum: {purchases_sum}"
                                        )


@dp.callback_query_handler(lambda c: c.data == "change_user")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("send message from user")
    await storage.set_state(user=callback_query.from_user.id, state="change_user_userID")


@dp.message_handler(state="change_user_userID")
async def _(message: types.Message, state: FSMContext):
    if message.is_forward():
        msg = message.forward_from
        if not msg:
            await message.answer("I can't get user. Please, send userID")
            await state.set_state("change_user_userID")
            return
        userID = msg.id
        username = msg.username
    else:
        if not message.text.isdigit():
            await message.answer("You should forward me message from that user or send me his userID")
            await state.set_state("change_user_userID")
            return
        userID = message.text
        username = "not found"

    if not users.is_registered(userID=userID):
        await message.answer(f"There is no {userID} in my database")
    else:
        await message.answer(f"userID: {userID}\nusername: {username}\nbalance: {users.get_balance(userID=userID)}",
                             reply_markup=keyboards.CHANGE_USER_DATA_MENU)

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "change_user_ban")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.message.text.split("\n")[0].split()[-1]
    if int(userID) not in config.ADMIN_ID:
        users.change_banned(userID=userID)
        status = users.get_banned(userID=userID)
        await callback_query.message.answer(f"Success. Now user {userID} {'banned' if status else 'unbanned'}")
    else:
        await callback_query.message.answer("You can't ban admins")


@dp.callback_query_handler(lambda c: c.data == "change_user_balance")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.message.text.split("\n")[0].split()[-1]
    await storage.update_data(user=callback_query.from_user.id, data={"balance_userID": userID})
    await callback_query.message.answer("Enter number")
    await storage.set_state(user=callback_query.from_user.id, state="change_user_userID_balance")


@dp.message_handler(state="change_user_userID_balance")
async def _(message: types.Message, state: FSMContext):
    try:
        num = float(message.text)
    except ValueError:
        await state.set_state("change_user_userID_balance")
        await message.answer("Send me number, please")
        return
    userData = await storage.get_data(user=message.from_user.id)
    userID = userData["balance_userID"]
    users.add_balance(num, userID=userID)
    await message.answer(f"Success. Now this user has {users.get_balance(userID=userID)}$")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "category_add")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("enter category name (russian)")
    await storage.set_state(user=callback_query.from_user.id, state="category_add_ru")


@dp.message_handler(state="category_add_ru")
async def _(message: types.Message, state: FSMContext):
    await state.update_data(data={"category_name": message.text})
    await message.answer("enter category name (english)")
    await state.set_state("category_add_en")


@dp.message_handler(state="category_add_en")
async def _(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category_name = data["category_name"] + "|" + message.text
    await state.update_data(data={"category_name": category_name})
    await message.answer("enter category description (russian)", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state("category_description_ru")


@dp.message_handler(state="category_description_ru")
async def _(message: types.Message, state: FSMContext):
    await state.update_data(data={"category_description": message.text})
    await message.answer("enter category description (english)")
    await state.set_state("category_description_en")


@dp.message_handler(state="category_description_en")
async def _(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category_description = data["category_description"] + "|" + message.text
    await state.update_data(data={"category_description": category_description})
    await message.answer("enter category price")
    await state.set_state("category_price")


@dp.message_handler(state="category_price")
async def _(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("You should enter number")
        await state.set_state("category_price")
        return
    data = await state.get_data()
    products.create_category(data["category_name"], data["category_description"], price)
    await message.answer("Success")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "product_add")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for category in products.get_categories():
        kb.add(category)
    await callback_query.message.answer("enter product category", reply_markup=kb)
    await storage.set_state(user=callback_query.from_user.id, state="product_category")


@dp.message_handler(state="product_category")
async def _(message: types.Message, state: FSMContext):
    if message.text not in products.get_categories():
        await message.answer("No such category")
        await state.set_state("product_category")
        return
    await state.update_data(data={"category_name": message.text})
    await message.answer("send file", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state("product_file")


@dp.message_handler(content_types=["document"], state="product_file")
async def _(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await products.add_product(data["category_name"], message.document)
    await message.answer("Successfully added product to category")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "product_replace")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("enter product name")
    await storage.set_state(user=callback_query.from_user.id, state="product_replace_filename")


@dp.message_handler(state="product_replace_filename")
async def _(message: types.Message, state: FSMContext):
    product = message.text
    if not products.product_exists(product):
        await message.answer("No such product. Enter again")
        await state.set_state("product_replace_filename")
        return
    await state.update_data(data={"product_filename": message.text})
    kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for category in products.get_categories():
        kb.add(category)
    await message.answer("enter product category", reply_markup=kb)
    await state.set_state("product_replace_category")


@dp.message_handler(state="product_replace_category")
async def _(message: types.Message, state: FSMContext):
    category = message.text
    if category not in products.get_categories():
        await message.answer("No such category. Enter again")
        await state.set_state("product_replace_category")
        return
    userData = await state.get_data()
    product = userData["product_filename"]
    old_category = products.get_product_category(product)
    products.change_product_category(product, category)
    os.rename(os.path.join("DB", old_category, product), os.path.join("DB", category, product))
    await message.answer("Success")
    await state.finish()
