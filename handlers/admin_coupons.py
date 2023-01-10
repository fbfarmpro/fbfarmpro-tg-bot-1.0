import string

import config
from handlers import *
from aiogram import types
import utils.keyboards as keyboards
from utils.database import ProductsDB
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loader import storage
import datetime
import random


products = ProductsDB("DB/products.db")


def create_coupon():
    return "".join(random.choice(string.ascii_uppercase+string.digits) for _ in range(config.COUPON_LEN))


@dp.callback_query_handler(lambda c: c.data.startswith("coupon"))
async def _(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    action = call.data.split("_")[-1]

    name = call.message.text.split()[0]
    if action == "menu":
        await call.message.edit_reply_markup(reply_markup=keyboards.COUPON_EDIT_MENU)
    elif action == "create":
        await call.message.answer("Choose sum/percent")
        await storage.set_state(user=call.from_user.id, state="coupon_create")
    elif action == "delete":
        # if there are coupon with this name
        if products.get_coupon(name):
            products.remove_coupon(name)
            await call.message.answer(f"Coupon {name} was successfully deleted")
            await call.message.delete()
        else:
            await call.message.answer("Send coupon name")
            await storage.set_state(user=call.from_user.id, state="coupon_delete")
    elif action == "date":
        # if there are coupon with this name
        if products.get_coupon(name):
            await storage.update_data(user=call.from_user.id, data={"name": name})
            await call.message.answer("Send date in format DD.MM.YYYY or \"NO\" to make this coupon one-time")
            await storage.set_state(user=call.from_user.id, state="coupon_edit_date")
        else:
            await call.message.answer("Send coupon name")
            await storage.set_state(user=call.from_user.id, state="coupon_edit_date_name")
    elif action == "all":
        for coupon in products.get_all_coupons():
            await call.message.answer(f"{coupon[0]} {coupon[3] if coupon[3] else 'one-time coupon'}",
                                      reply_markup=keyboards.COUPON_CHANGE_MENU)
    elif action == "send":
        await call.message.answer("Send message from person or userID")
        await storage.update_data(user=call.from_user.id, data={"name": name})
        await storage.set_state(user=call.from_user.id, state="coupon_send")


@dp.message_handler(state="coupon_delete")
async def _(msg: types.Message, state: FSMContext):
    name = msg.text
    if products.get_coupon(name):
        products.remove_coupon(name)
        await msg.answer(f"Coupon {name} was successfully deleted")
    else:
        await msg.answer("No such coupon")
    await state.finish()


@dp.message_handler(state="coupon_create")
async def _(msg: types.Message, state: FSMContext):
    if msg.text in ["percent", "sum"]:
        await state.update_data(data={"type": msg.text})
    else:
        await msg.answer("You should choose between sum and percent")
        await state.set_state("coupon_create")
        return

    await msg.answer("Send value of coupon")
    await state.set_state("coupon_create_value")


@dp.message_handler(state="coupon_create_value")
async def _(msg: types.Message, state: FSMContext):
    try:
        value = float(msg.text)
    except ValueError:
        await msg.answer("You should enter digit value")
        await state.set_state("coupon_create_value")
        return

    await state.update_data(data={"value": value})

    await msg.answer("Send date in format DD.MM.YYYY or \"NO\" to make this coupon one-time")
    await state.set_state("coupon_create_date")


@dp.message_handler(state="coupon_create_date")
async def _(msg: types.Message, state: FSMContext):
    try:
        expires = datetime.datetime.strptime(msg.text, "%d.%m.%Y")
    except ValueError:
        expires = None

    data = await state.get_data()

    coupon_name = create_coupon()
    expires = expires.strftime("%d.%m.%Y") if expires else expires
    products.add_coupon(coupon_name, data["type"], expires, data["value"])
    await msg.answer(f"{coupon_name} {expires if expires else 'one-time coupon'}", reply_markup=keyboards.COUPON_CHANGE_MENU)
    await state.finish()


@dp.message_handler(state="coupon_edit_date")
async def _(msg: types.Message, state: FSMContext):
    try:
        expires = datetime.datetime.strptime(msg.text, "%d.%m.%Y")
    except ValueError:
        expires = None

    data = await state.get_data()

    coupon_name = data["name"]
    expires = expires.strftime("%d.%m.%Y") if expires else expires
    products.change_coupon_expires(coupon_name, expires)
    await msg.answer("Success")
    await state.finish()


@dp.message_handler(state="coupon_send")
async def _(msg: types.Message, state: FSMContext):
    if msg.is_forward():
        forward = msg.forward_from
        if not forward:
            await msg.answer("I can't get user. Please, send userID")
            await state.set_state("coupon_send")
            return
        userID = forward.id
    else:
        if not msg.text.isdigit():
            await msg.answer("You should forward me message from that user or send me his userID")
            await state.set_state("coupon_send")
            return
        userID = msg.text

    if not users.is_registered(userID=userID):
        await msg.answer(f"There is no {userID} in my database")
    else:
        data = await state.get_data()
        name = data["name"]
        coupon = products.get_coupon(name)
        coupon_value = f"%{coupon[2]}" if coupon[1] == "percent" else f"{coupon[2]}$"
        await bot.send_message(userID, fr"""
Success\! You have been assigned promo code, coupon by {msg.from_user.mention} for *{coupon_value}*\.
Your unique combination *{coupon[0]}*\.""", parse_mode="MarkdownV2")
        await msg.answer("Coupon was successfully sent")

    await state.finish()
