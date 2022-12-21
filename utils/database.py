from aiogram import types

import config
from handlers import *
from config import *
import sqlite3
import aiohttp
from secret import APIKEY
from json import loads
from secrets import choice
from string import ascii_letters, digits
from datetime import datetime
import os


def create_random_filename_zip():
    # choose from all lowercase letter
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(config.FINAL_ZIP_NAME_LEN))+".zip"


async def get_crypto_currency(coin_name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin_name.upper()}USDT") as req:
            text = await req.json()
            return float(text["price"])


class UsersDB:
    def __init__(self):
        self.db = sqlite3.connect("DB/users.db")
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (userID TEXT NOT NULL,
                                                              language TEXT NOT NULL,
                                                              balance INT NOT NULL,
                                                              payment_ids TEXT,
                                                              isBanned INT NOT NULL)""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS purchaseHistory (userID TEXT NOT NULL,
                                                                        time TEXT NOT NULL,
                                                                        category TEXT NOT NULL,
                                                                        amount INT NOT NULL,
                                                                        price INT NOT NULL,
                                                                        filename TEXT)""")
        self.db.commit()

    def get_payments(self, userID):
        data = self.cur.execute("SELECT payment_ids from users where userID = ?", (userID,)).fetchone()[0]
        return data.split(",") if data else list()

    def add_payment(self, userID, paymentID):
        payments = self.get_payments(userID)
        payments.append(paymentID)
        self.cur.execute("UPDATE users SET payment_ids = ? WHERE userID = ?", (",".join(payments), userID))
        self.db.commit()

    def remove_payment(self, userID, paymentID):
        payments = self.get_payments(userID)
        payments.remove(paymentID)
        self.cur.execute("UPDATE users SET payment_ids = ? WHERE userID = ?", (",".join(payments), userID))
        self.db.commit()

    def register(self, userID):
        self.cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (userID, "RU", 0, None, "0"))
        self.db.commit()

    def is_registered(self, userID):
        return self.cur.execute("SELECT * from users WHERE userID = ?", (userID,)).fetchone()

    def get_language(self, userID):
        return self.cur.execute("SELECT language FROM users WHERE userID = ?", (userID,)).fetchone()[0]

    def get_banned(self, userID):
        data = self.cur.execute("SELECT isBanned FROM users WHERE userID = ?", (userID,)).fetchone()
        return int(data[0]) if data else list()

    def change_language(self, userID):
        lang = self.get_language(userID)
        self.cur.execute("UPDATE users SET language = ? WHERE userID = ?", ("RU" if lang == "EN" else "EN", userID))
        self.db.commit()

    def change_banned(self, userID):
        status = self.get_banned(userID)
        self.cur.execute("UPDATE users SET isBanned = ? WHERE userID = ?", (1 if status == 0 else 0, userID))
        self.db.commit()

    def get_balance(self, userID):
        return float(self.cur.execute("SELECT balance FROM users WHERE userID = ?", (userID,)).fetchone()[0])

    def add_balance(self, userID, amount):
        balance = self.get_balance(userID)
        result = balance + amount
        self.cur.execute("UPDATE users SET balance = ? WHERE userID = ?", (result if result > 0 else 0, userID))
        self.db.commit()

    def get_count_of_users(self):
        return int(self.cur.execute("SELECT COUNT(DISTINCT userID) FROM users").fetchone()[0])

    def get_count_of_banned(self):
        return int(self.cur.execute("SELECT COUNT(DISTINCT userID) FROM users WHERE isBanned = 1").fetchone()[0])

    def get_count_of_regular_customers(self):
        return int(self.cur.execute("SELECT COUNT(DISTINCT userID) FROM users WHERE balance > 0").fetchone()[0])

    def get_purchases(self):
        return self.cur.execute("SELECT * FROM purchaseHistory").fetchall()

    def add_purchase(self, userID, category_name, amount, price, filename):
        self.cur.execute("INSERT INTO purchaseHistory VALUES (?, ?, ?, ?, ?, ?)", (
            userID, datetime.isoformat(datetime.now()), category_name, amount, price, filename))
        self.db.commit()

    def remove_purchase_archive(self, filename):
        self.cur.execute("UPDATE purchaseHistory SET filename = ? WHERE filename = ?", (None, filename))
        self.db.commit()

    def __iter__(self):
        """[0] element is userID, [1] element is language, [2] is balance, [3] is payment_ids"""
        return iter(self.cur.execute("SELECT * FROM USERS").fetchall())

class ProductsDB:
    def __init__(self):
        self.db = sqlite3.connect("DB/products.db")
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS categories (name TEXT NOT NULL,
                                                                   description TEXT NOT NULL,
                                                                   price INTEGER NOT NULL)""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS products (name TEXT NOT NULL,
                                                                 category TEXT NOT NULL,
                                                                 boughtAt TEXT)""")
        self.db.commit()

    def create_category(self, name, desc, price):
        os.mkdir(os.path.join("DB", name))
        self.cur.execute("INSERT INTO categories VALUES (?, ?, ?)", (name, desc, price))
        self.db.commit()

    async def add_product(self, category_name, file: types.Document):
        product_name = file.file_name
        await file.download(os.path.join("DB", category_name, product_name))
        self.cur.execute("INSERT INTO products VALUES (?, ?, ?)", (product_name, category_name, None))
        self.db.commit()

    def remove_product(self, category_name, product_name):
        self.cur.execute("DELETE FROM products WHERE name = ? AND category = ?", (product_name, category_name))
        self.db.commit()

    def product_exists(self, product_name):
        return bool(self.cur.execute("SELECT * FROM products WHERE name = ?", (product_name,)).fetchone()[0])

    def get_product_category(self, product_name):
        return self.cur.execute("SELECT category FROM products WHERE name = ?", (product_name,)).fetchone()[0]

    def change_product_category(self, product_name, category_name):
        self.cur.execute("UPDATE products SET category = ? WHERE name = ?", (category_name, product_name))
        self.db.commit()

    def get_count_of_products(self, category_name):
        return int(self.cur.execute("SELECT COUNT(DISTINCT name) name FROM products WHERE category = ? AND boughtAt IS NULL", (category_name,)).fetchone()[0])

    def set_isBought(self, product_name, category_name):
        self.cur.execute("UPDATE products SET boughtAt = ? WHERE name = ? and category = ?", (datetime.now().isoformat(), product_name, category_name))
        self.db.commit()

    def get_categories(self):
        data = self.cur.execute("SELECT name FROM categories").fetchall()
        return [item for t in data for item in t]


    def get_N_products(self, category_name, amount):
        return self.cur.execute("SELECT name FROM products WHERE category = ? AND boughtAt IS NULL LIMIT ?", (category_name, amount)).fetchall()

    def get_category_price(self, category_name):
        return int(self.cur.execute("SELECT price FROM categories WHERE name = ?", (category_name,)).fetchone()[0])

    def get_all_products(self):
        return self.cur.execute("SELECT * FROM products WHERE boughtAt IS NULL").fetchall()

    def get_total_cost_of_products(self):
        return sum(self.get_category_price(i[1]) for i in self.get_all_products())

    def __iter__(self):
        return iter(self.cur.execute("SELECT * FROM products").fetchall())


class AsyncPayment:
    def __init__(self, api_key):
        # self.url = "https://app-demo.payadmit.com/api/v1/payments/" # test
        self.url = "https://app.payadmit.com/api/v1/payments/" # prod
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def create_payment(self, amount, currency):
        async with aiohttp.ClientSession() as session:
            json = { "amount": amount,
                     "paymentType": "DEPOSIT",
                     "paymentMethod": "CRYPTO",
                     "currency": currency
                     }

            async with session.post(self.url, json=json, headers=self.headers) as req:
                resp = await req.json()
                return resp

    async def get_payment(self, paymentID):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url+f"{paymentID}", json={"id": paymentID}, headers=self.headers) as req:
                data = await req.text()
                return loads(data)

    async def get_all_payments(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=self.headers) as req:
                resp = await req.text()
                return loads(resp)["result"]


users = UsersDB()
products = ProductsDB()
payment = AsyncPayment(APIKEY)
