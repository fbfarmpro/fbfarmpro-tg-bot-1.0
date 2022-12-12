import config
from handlers import *
from aiogram import types
import utils.keyboards as keyboards
import utils.database as database
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from json import loads, dumps
from loader import storage


@dp.callback_query_handler(lambda c: c.data == "back")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.ADMIN_MENU)


@dp.callback_query_handler(lambda c: c.data == "greeting_msg")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.GREETING_MSG_MENU)


@dp.callback_query_handler(lambda c: c.data == "greeting_msg_edit_ru")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("send text for russian greeting message")
    await storage.set_state(user=callback_query.from_user.id, state="edit_msg_ru")


@dp.callback_query_handler(lambda c: c.data == "greeting_msg_edit_en")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("send text for english greeting message")
    await storage.set_state(user=callback_query.from_user.id, state="edit_msg_en")


@dp.message_handler(state="edit_msg_ru")
async def _(message: types.Message, state: FSMContext):
    try:
        with open(config.GREETING_MSG_FILENAME) as file:
            content = loads(file.read())
    except FileNotFoundError:
        content = {"ru": {"text": None}, "en": {"text": None}}
    content["ru"]["text"] = message.text
    with open(config.GREETING_MSG_FILENAME, "w") as file:
        file.write(dumps(content, indent=2))
    await message.answer("Success")
    await state.finish()


@dp.message_handler(state="edit_msg_en")
async def _(message: types.Message, state: FSMContext):
    try:
        with open(config.GREETING_MSG_FILENAME) as file:
            content = loads(file.read())
    except FileNotFoundError:
        content = {"ru": {"text": None}, "en": {"text": None}}
    content["en"]["text"] = message.text
    with open(config.GREETING_MSG_FILENAME, "w") as file:
        file.write(dumps(content, indent=2))
    await message.answer("Success")
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


@dp.callback_query_handler(lambda c: c.data == "mailing_change_buttons")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(keyboards.MAILING_CHANGE_BUTTONS_MENU)


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
            for user in database.users:
                await bot.send_animation(chat_id=user[0],
                                         caption=text,
                                         disable_notification=disable_notification,
                                         protect_content=protect_content,
                                         reply_markup=kb,
                                         animation=animation)
        elif data.get("photo", 0):
            photo = data["photo"]
            for user in database.users:
                await bot.send_photo(chat_id=user[0],
                                     caption=text,
                                     disable_notification=disable_notification,
                                     protect_content=protect_content,
                                     reply_markup=kb,
                                     photo=photo)
        else:
            for user in database.users:
                await bot.send_message(chat_id=user[0],
                                       text=text,
                                       disable_notification=data.get("disable_sound", False),
                                       protect_content=data.get("protect_content", False),
                                       reply_markup=kb)
    else:
        if data.get("animation", 0):
            animation = data["animation"]
            for user in database.users.get_regular_customers():
                await bot.send_animation(chat_id=user[0],
                                         caption=text,
                                         disable_notification=disable_notification,
                                         protect_content=protect_content,
                                         reply_markup=kb,
                                         animation=animation)
        elif data.get("photo", 0):
            photo = data["photo"]
            for user in database.users.get_regular_customers():
                await bot.send_photo(chat_id=user[0],
                                     caption=text,
                                     disable_notification=disable_notification,
                                     protect_content=protect_content,
                                     reply_markup=kb,
                                     photo=photo)
        else:
            for user in database.users.get_regular_customers():
                await bot.send_message(chat_id=user[0],
                                       text=text,
                                       disable_notification=data.get("disable_sound", False),
                                       protect_content=data.get("protect_content", False),
                                       reply_markup=kb)
    await callback_query.message.answer("Mailing done.")


@dp.callback_query_handler(lambda c: c.data == "statistic")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    count_of_users = database.users.get_count_of_users()
    count_of_regular_customers = database.users.get_regular_customers()
    banned_users = 0 # TODO

    await callback_query.message.answer(f"users:{count_of_users}\n"
                                        f"regular:{count_of_regular_customers}\n"
                                        f"banned: {banned_users}\n"
                                        f"")


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
            # await AdminPanel.change_user_userID.set()
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

    if not database.users.is_registered(userID):
        await message.answer(f"There is no {userID} in my database")
    else:
        await message.answer(f"userID: {userID}\nusername: {username}\nbalance: {database.users.get_balance(userID)}",
                             reply_markup=keyboards.CHANGE_USER_DATA_MENU)

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "change_user_ban")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    userID = callback_query.message.text.split("\n")[0].split()[-1]
    if int(userID) not in config.ADMIN_ID:
        database.users.change_banned(userID)
        status = database.users.get_banned(userID)
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


@dp.message_handler(lambda msg: msg.text.isdigit(), state="change_user_userID_balance")
async def _(message: types.Message, state: FSMContext):
    num = int(message.text)
    userData = await storage.get_data(user=message.from_user.id)
    userID = userData["balance_userID"]
    database.users.add_balance(userID, num)
    await message.answer(f"Success. Now this user has {database.users.get_balance(userID)}$")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "category_add")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("enter category name")
    await storage.set_state(user=callback_query.from_user.id, state="category")


@dp.message_handler(state="category")
async def _(message: types.Message, state: FSMContext):
    await state.update_data(data={"category_name": message.text})
    await message.answer("enter category description")
    await state.set_state("category_description")


@dp.message_handler(state="category_description")
async def _(message: types.Message, state: FSMContext):
    await state.update_data(data={"category_description": message.text})
    await message.answer("enter category price")
    await state.set_state("category_price")


@dp.message_handler(state="category_price")
async def _(message: types.Message, state: FSMContext):
    price = message.text
    data = await state.get_data()
    database.products.create_category(data["category_name"], data["category_description"], price)
    await message.answer("Success")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "product_add")
async def _(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("enter product category")
    await storage.set_state(user=callback_query.from_user.id, state="product_category")

@dp.message_handler(state="product_category")
async def _(message: types.Message, state: FSMContext):
    await state.update_data(data={"category_name": message.text})
    await message.answer("send file")
    await state.set_state("product_file")


@dp.message_handler(content_types=["document"], state="product_file")
async def _(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await database.products.add_product(data["category_name"], message.document)
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
    if not database.products.product_exists(product):
        await message.answer("No such product. Enter again")
        await state.set_state("product_replace_filename")
        return
    await state.update_data(data={"product_filename": message.text})
    await message.answer("enter product category")
    await state.set_state("product_replace_category")

@dp.message_handler(state="product_replace_category")
async def _(message: types.Message, state: FSMContext):
    category = message.text
    cats = database.products.get_categories()
    print(cats)
    if category not in database.products.get_categories():
        await message.answer("No such category. Enter again")
        await state.set_state("product_replace_category")
        return
    userData = await state.get_data()
    product = userData["product_filename"]
    database.products.change_product_category(product, category)
    await message.answer("Success")
    await state.finish()