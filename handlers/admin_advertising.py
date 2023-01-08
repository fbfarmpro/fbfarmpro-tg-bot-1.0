import config
from handlers import *
from aiogram import types
import utils.keyboards as keyboards
from utils.database import UsersDB, ProductsDB
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from json import loads, dumps
from loader import storage
import os
import shutil
import datetime
from PIL import Image


users = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")


def get_themes():
    themes = os.listdir(config.AD_FOLDER)
    themes.remove("current")
    return themes


@dp.callback_query_handler(lambda c: c.data.startswith("advertising_"))
async def _(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    action = "_".join(call.data.split("_")[1::])
    if action == "menu":
        await call.message.edit_reply_markup(keyboards.ADVERTISING_MENU)
    elif action == "add_pack":
        await call.message.answer("Enter new pack name")
        await storage.set_state(user=call.from_user.id, state="add_pack_name")
    else:
        kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        for file in get_themes():
            kb.add(file)
        kb.add(keyboards.CANCEL_ADMIN_REPLY_TEXT)
        if action == "del_pack":
            await call.message.answer("Enter pack name", reply_markup=kb)
            await storage.set_state(user=call.from_user.id, state="del_pack_name")
        elif action == "upd_pack":
            await call.message.answer("Enter pack name", reply_markup=kb)
            await storage.set_state(user=call.from_user.id, state="upd_pack_name")


@dp.callback_query_handler(lambda c: c.data.startswith("ad_"))
async def _(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    action = call.data.split("_")[-1]
    if call.message.text not in get_themes():
        await call.message.answer("No such theme")
        return
    await storage.update_data(user=call.from_user.id, data={"theme": call.message.text})

    await call.message.answer("Send photo without compression")
    if action == "bg":
        await call.message.answer("Send photo with 1920x980 resolution", reply_markup=keyboards.CANCEL_ADMIN_REPLY)
        await storage.set_state(user=call.from_user.id, state="advertising_photo_bg")
    elif action == "mobile":
        await call.message.answer("Send photo with 340x70 resolution", reply_markup=keyboards.CANCEL_ADMIN_REPLY)
        await storage.set_state(user=call.from_user.id, state="advertising_photo_mobile")
    elif action == "top":
        await call.message.answer("Send photo", reply_markup=keyboards.CANCEL_ADMIN_REPLY)
        await storage.set_state(user=call.from_user.id, state="advertising_photo_top")
    elif action == "bottom":
        await call.message.answer("Send photo with 468x60 resolution", reply_markup=keyboards.CANCEL_ADMIN_REPLY)
        await storage.set_state(user=call.from_user.id, state="advertising_photo_bottom")
    elif action == "text":
        await call.message.answer("Send russian text", reply_markup=types.ReplyKeyboardRemove())
        await storage.set_state(user=call.from_user.id, state="advertising_text_ru")
    elif action == "time":
        await call.message.answer("When to remove ads? (in days)", reply_markup=types.ReplyKeyboardRemove())
        await storage.set_state(user=call.from_user.id, state="advertising_time")


@dp.message_handler(state="add_pack_name")
async def _(message: types.Message, state: FSMContext):
    # await state.update_data({"pack_name": message.text})
    if message.text in get_themes():
        await message.answer("this category already exists")
        await state.set_state("add_pack_name")
        return
    new_folder_path = os.path.join(config.AD_FOLDER, message.text)
    default_path = os.path.join(config.AD_FOLDER, "default")
    os.mkdir(new_folder_path)
    for filename in config.AD_FILES:
        shutil.copy(os.path.join(default_path, filename), os.path.join(new_folder_path, filename))
    await message.answer(message.text, reply_markup=keyboards.ADVERTISING_CHANGE_MENU)
    await state.finish()


@dp.message_handler(state="upd_pack_name")
async def _(message: types.Message, state: FSMContext):
    if message.text == keyboards.CANCEL_ADMIN_REPLY_TEXT:
        await message.answer("Ok", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("What do you want to do", reply_markup=keyboards.ADMIN_MENU)
        await state.reset_state(with_data=False)
        return
    elif message.text not in get_themes():
        await message.answer("No such theme", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("What do you want to do", reply_markup=keyboards.ADVERTISING_CHANGE_MENU)
        await state.set_state("upd_pack_name")
        return
    await message.answer("Update pack", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(message.text, reply_markup=keyboards.ADVERTISING_CHANGE_MENU)
    await state.finish()


@dp.message_handler(state="del_pack_name")
async def _(message: types.Message, state: FSMContext):
    if message.text == keyboards.CANCEL_ADMIN_REPLY_TEXT:
        await message.answer("Ok", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("What do you want to do", reply_markup=keyboards.ADMIN_MENU)
        await state.reset_state(with_data=False)
        return
    elif message.text not in get_themes():
        await message.answer("No such theme")
        await state.set_state("del_pack_name")
        return
    await message.answer("Success", reply_markup=types.ReplyKeyboardRemove())
    shutil.rmtree(os.path.join(config.AD_FOLDER, message.text))
    await state.finish()


@dp.message_handler(state="advertising_photo_bottom", content_types=["animation", "text"])
async def _(message: types.Message, state: FSMContext):
    if message.text == keyboards.CANCEL_ADMIN_REPLY_TEXT:
        await message.answer("ok", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("What do you want to do", reply_markup=keyboards.ADVERTISING_MENU)
        await state.reset_state(with_data=False)
        return
    data = await state.get_data()
    await message.animation.download(destination=os.path.join(
        config.AD_FOLDER, data["theme"], config.AD_DESKTOP_BOTTOM_FILENAME))
    await message.answer("Success")
    await state.reset_state(with_data=False)


@dp.message_handler(state="advertising_photo_top", content_types=["animation", "text"])
async def _(message: types.Message, state: FSMContext):
    if message.text == keyboards.CANCEL_ADMIN_REPLY_TEXT:
        await message.answer("ok", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("What do you want to do", reply_markup=keyboards.ADVERTISING_MENU)
        await state.reset_state(with_data=False)
        return
    data = await state.get_data()
    res = f"{message.animation.width}x{message.animation.height}"
    need_res = config.AD_DESKTOP_TOP_FILENAME.split("-")[-1].split(".")[0]
    if res != need_res:
        await message.answer(f"Wrong resolution. Resolution of your image is: {res} and i need {need_res}")
        await state.set_state("advertising_photo_top")
        return
    await message.animation.download(destination=os.path.join(
        config.AD_FOLDER, data["theme"], config.AD_DESKTOP_TOP_FILENAME))
    await message.answer("Success")
    await state.reset_state(with_data=False)


@dp.message_handler(state="advertising_photo_mobile", content_types=["animation", "text"])
async def _(message: types.Message, state: FSMContext):
    if message.text == keyboards.CANCEL_ADMIN_REPLY_TEXT:
        await message.answer("ok", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("What do you want to do", reply_markup=keyboards.ADVERTISING_MENU)
        await state.reset_state(with_data=False)
        return
    data = await state.get_data()
    await message.animation.download(destination=os.path.join(
        config.AD_FOLDER, data["theme"], config.AD_MOBILE_FILENAME))
    await message.answer("Success")
    await state.reset_state(with_data=False)


@dp.message_handler(state="advertising_photo_bg", content_types=["document", "text"])
async def _(message: types.Message, state: FSMContext):
    if message.text == keyboards.CANCEL_ADMIN_REPLY_TEXT:
        await message.answer("ok", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("What do you want to do", reply_markup=keyboards.ADVERTISING_MENU)
        await state.reset_state(with_data=False)
        return

    # I need to download this file to get resolution
    await message.document.download(destination_file="tmp.png")
    with Image.open("tmp.png") as file:
        width, height = file.size

    res = f"{width}x{height}"
    need_res = config.SITE_BACKGROUND_FILENAME.split("-")[-1].split(".")[0]
    os.remove("tmp.png")

    if res != need_res:
        await message.answer(f"Wrong resolution. Resolution of your image is: {res} and i need {need_res}")
        await state.set_state("advertising_photo_bg")
        return
    data = await state.get_data()
    await message.document.download(destination=os.path.join(
        config.AD_FOLDER, data["theme"], config.AD_MOBILE_FILENAME))
    await message.answer("Success", reply_markup=types.ReplyKeyboardRemove())
    await state.reset_state(with_data=False)


@dp.message_handler(state="advertising_text_ru")
async def _(message: types.Message, state: FSMContext):
    await state.update_data(data={"ru": message.text})
    await message.answer("Success. Now send me english text")
    await state.set_state("advertising_text_en")


@dp.message_handler(state="advertising_text_en")
async def _(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ru = data["ru"]
    en = message.text
    path = os.path.join(config.AD_FOLDER, data["theme"], config.AD_TEXT_FILENAME)
    with open(path, "r") as file:
        file_data = file.read()
        if not file_data:
            content = {"ru": None, "en": None, "time": None}
        else:
            content = loads(file_data)
    content["ru"] = ru
    content["en"] = en
    with open(path, "w") as file:
        file.write(dumps(content, ensure_ascii=False))
    await message.answer("Success")
    await state.reset_state(with_data=False)


@dp.message_handler(state="advertising_time")
async def _(message: types.Message, state: FSMContext):
    try:
        days = float(message.text)
    except ValueError:
        await message.answer("You should enter number")
        await state.set_state("advertising_time")
        return

    data = await state.get_data()

    with open(os.path.join(config.AD_FOLDER, data["theme"], config.AD_TEXT_FILENAME), "r") as file:
        file_data = file.read()
        if not file_data:
            current_text = {"ru": None, "en": None, "time": None}
        else:
            current_text = loads(file_data)

    current_text["time"] = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()

    with open(os.path.join(config.AD_FOLDER, data["theme"], config.AD_TEXT_FILENAME), "w") as file:
        file.write(dumps(current_text, ensure_ascii=False))

    await message.answer("Success")
    await state.reset_state(with_data=False)
