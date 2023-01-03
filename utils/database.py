import os
import sqlite3
from datetime import datetime
from json import loads
from secrets import choice
from string import ascii_letters, digits

import aiohttp
from aiogram import types
import hashlib

from secret import APIKEY
import config


def create_random_filename_zip():
    # choose from all lowercase letter
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(config.FINAL_ZIP_NAME_LEN))+".zip"


async def get_crypto_currency(coin_name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin_name.upper()}USDT") as r:
            data = await r.json()
            return float(data["price"])


class UsersDB:
    def __init__(self, method, path):
        if method not in ["tg", "site"]:
            raise ValueError("Method should be 'tg' or 'site'")
        self.method = method
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (method TEXT NOT NULL,
                                                              userID TEXT,
                                                              email TEXT,
                                                              password TEXT,
                                                              language TEXT NOT NULL,
                                                              balance REAL NOT NULL,
                                                              payment_ids TEXT,
                                                              isBanned INT NOT NULL)""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS purchaseHistory (userID TEXT,
                                                                        email TEXT,
                                                                        time TEXT NOT NULL,
                                                                        category TEXT NOT NULL,
                                                                        amount REAL NOT NULL,
                                                                        price REAL NOT NULL,
                                                                        filename TEXT)""")
        self.db.commit()

    def get_payments(self, *, userID=None, email=None):
        if self.method == "tg":
            assert userID is not None
            data = self.cur.execute("SELECT payment_ids from users where userID = ?", (userID,)).fetchone()[0]
        else:
            assert email is not None
            data = self.cur.execute("SELECT payment_ids from users where email = ?", (email,)).fetchone()[0]
        return data.split(",") if data else list()

    def add_payment(self, paymentID, *, userID=None, email=None):
        payments = self.get_payments(userID=userID, email=email)
        payments.append(paymentID)
        if self.method == "tg":
            self.cur.execute("UPDATE users SET payment_ids = ? WHERE userID = ?", (",".join(payments), userID))
        else:
            self.cur.execute("UPDATE users SET payment_ids = ? WHERE email = ?", (",".join(payments), email))
        self.db.commit()

    def remove_payment(self, paymentID, *, userID=None, email=None):
        payments = self.get_payments(userID=userID, email=email)
        payments.remove(paymentID)
        if self.method == "tg":
            self.cur.execute("UPDATE users SET payment_ids = ? WHERE userID = ?", (",".join(payments), userID))
        else:
            self.cur.execute("UPDATE users SET payment_ids = ? WHERE email = ?", (",".join(payments), email))
        self.db.commit()

    def register(self, *, userID=None, email=None, password=None):
        """If you pass email and password, this function will calculate hash for this password and store it to db"""
        if self.method == "tg":
            assert userID is not None
            self.cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("tg", userID, None,
                                                                                   None, "RU", 0,
                                                                                   None, 0))
        else:
            assert password is not None and email is not None
            self.cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("site", None, email,
                                                                                   hashlib.sha256(password.encode()).hexdigest(), "EN", 0,
                                                                                   None, 0))
        self.db.commit()

    def register_site_via_tg(self, userID):
        self.cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("site", userID, None,
                                                                               None, "RU", 0,
                                                                               None, 0))
        self.db.commit()

    def get_by_id(self, userID):
        return self.cur.execute("SELECT * FROM users WHERE userID = ?", (userID,)).fetchone()

    def is_registered(self, *, userID=None, email=None):
        if self.method == "tg" or userID:
            assert userID is not None
            return self.cur.execute("SELECT * FROM users WHERE userID = ?", (userID,)).fetchone()
        else:
            assert email is not None
            return self.cur.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    def link_tg(self, userID, email):
        self.cur.execute("UPDATE users SET userID = ?, language = ? WHERE email = ?", (userID, "RU", email))
        self.db.commit()

    def get_language(self, *, userID=None, email=None):
        if self.method == "tg":
            assert userID is not None
            # if db was deleted and languages were lost, default lang would be EN
            lang = self.cur.execute("SELECT language FROM users WHERE userID = ?", (userID,)).fetchone()
            if not lang:
                return "EN"
            else:
                return lang[0]
        else:
            assert email is not None
            return self.cur.execute("SELECT language FROM users WHERE email = ?", (email,)).fetchone()[0]

    def get_banned(self, *, userID=None, email=None):
        if self.method == "tg":
            assert userID is not None
            data = self.cur.execute("SELECT isBanned FROM users WHERE userID = ?", (userID,)).fetchone()
        else:
            assert email is not None
            data = self.cur.execute("SELECT isBanned FROM users WHERE email = ?", (email,)).fetchone()
        return int(data[0]) if data else 0

    def get_purchase_history(self, *, userID=None, email=None):
        if self.method == "tg":
            assert userID is not None
            return [i for i in filter(lambda t: str(t[0]) == str(userID), self.get_purchases())]
        else:
            assert email is not None
            return [i for i in filter(lambda t: str(t[1]) == str(email), self.get_purchases())]

    def change_password(self, email, password):
        # hashlib.sha256(password.encode()).hexdigest(), "EN", 0,
        self.cur.execute("UPDATE users SET password = ? where email = ?", (hashlib.sha256(password.encode()).hexdigest(), email))
        self.db.commit()

    def change_language(self, *, userID=None, email=None):
        lang = self.get_language(userID=userID, email=email) or "RU"
        if self.method == "tg":
            self.cur.execute("UPDATE users SET language = ? WHERE userID = ?", ("RU" if lang == "EN" else "EN", userID))
        else:
            self.cur.execute("UPDATE users SET language = ? WHERE email = ?", ("RU" if lang == "EN" else "EN", email))
        self.db.commit()

    def change_banned(self, *, userID=None, email=None):
        status = self.get_banned(userID=userID, email=email)
        if self.method == "tg":
            self.cur.execute("UPDATE users SET isBanned = ? WHERE userID = ?", (1 if status == 0 else 0, userID))
        else:
            self.cur.execute("UPDATE users SET isBanned = ? WHERE email = ?", (1 if status == 0 else 0, email))
        self.db.commit()

    def get_balance(self, *, userID=None, email=None):
        if self.method == "tg":
            assert userID is not None
            return float(self.cur.execute("SELECT balance FROM users WHERE userID = ?", (userID,)).fetchone()[0])
        else:
            assert email is not None
            return float(self.cur.execute("SELECT balance FROM users WHERE email = ?", (email,)).fetchone()[0])

    def add_balance(self, amount, *, userID=None, email=None):
        balance = self.get_balance(userID=userID, email=email)
        result = balance + amount
        if self.method == "tg":
            self.cur.execute("UPDATE users SET balance = ? WHERE userID = ?", (result if result > 0 else 0, userID))
        else:
            self.cur.execute("UPDATE users SET balance = ? WHERE email = ?", (result if result > 0 else 0, email))
        self.db.commit()

    def get_count_of_users(self):
        return int(self.cur.execute("SELECT COUNT(DISTINCT userID) FROM users").fetchone()[0])

    def get_count_of_banned(self):
        return int(self.cur.execute("SELECT COUNT(DISTINCT userID) FROM users WHERE isBanned = 1").fetchone()[0])

    def get_count_of_regular_customers(self):
        return int(self.cur.execute("SELECT COUNT(DISTINCT userID) FROM users WHERE balance > 0").fetchone()[0])

    def get_purchases(self):
        return self.cur.execute("SELECT * FROM purchaseHistory").fetchall()

    def add_purchase(self, category_name, amount, price, filename, *, userID=None, email=None):
        assert userID is not None or email is not None
        self.cur.execute("INSERT INTO purchaseHistory VALUES (?, ?, ?, ?, ?, ?, ?)", (
            userID, email, datetime.isoformat(datetime.now()), category_name, amount, price, filename))
        self.db.commit()

    def remove_purchase_archive(self, filename):
        self.cur.execute("UPDATE purchaseHistory SET filename = ? WHERE filename = ?", (None, filename))
        self.db.commit()

    def get_regular_customers(self):
        return iter(self.cur.execute("SELECT * FROM users WHERE balance > 0"))

    def __iter__(self):
        """[0] element is userID, [1] element is language, [2] is balance, [3] is payment_ids"""
        return iter(self.cur.execute("SELECT * FROM users").fetchall())


class Tokens:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS tokens (token TEXT NOT NULL,
                                                               status TEXT NOT NULL)""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS resetEmail (token TEXT NOT NULL,
                                                               email TEXT NOT NULL)""")
        self.db.commit()

    def get(self, token):
        return self.cur.execute("SELECT * FROM tokens WHERE token = ?", (token,)).fetchone()

    def add(self, token):
        self.cur.execute("INSERT INTO tokens VALUES (?, ?)", (token, "waiting",))
        self.db.commit()

    def set_status(self, token, status):
        self.cur.execute("UPDATE tokens SET status = ? WHERE token = ?", (status, token,))
        self.db.commit()

    def remove(self, token):
        self.cur.execute("DELETE FROM tokens WHERE token = ?", (token,))
        self.db.commit()

    def get_email(self, token):
        return self.cur.execute("SELECT * FROM resetEmail WHERE token = ?", (token,)).fetchone()

    def add_email(self, token, email):
        self.cur.execute("INSERT INTO resetEmail VALUES (?, ?)", (token, email,))
        self.db.commit()

    def remove_email(self, token):
        self.cur.execute("DELETE FROM resetEmail WHERE token = ?", (token,))
        self.db.commit()


class ProductsDB:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS categories (name TEXT NOT NULL,
                                                                   description TEXT NOT NULL,
                                                                   price REAL NOT NULL)""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS products (name TEXT NOT NULL,
                                                                 category TEXT NOT NULL,
                                                                 boughtAt TEXT)""")
        self.db.commit()

    def create_category(self, name, desc, price):
        os.mkdir(os.path.join("DB", name))
        self.cur.execute("INSERT INTO categories VALUES (?, ?, ?)", (name, desc, float(price)))
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
        return float(self.cur.execute("SELECT price FROM categories WHERE name = ?", (category_name,)).fetchone()[0])

    def get_category_description(self, category_name):
        return self.cur.execute("SELECT description FROM categories WHERE name = ?", (category_name,)).fetchone()[0]

    def get_all_products(self):
        return self.cur.execute("SELECT * FROM products WHERE boughtAt IS NULL").fetchall()

    def get_total_cost_of_products(self):
        return sum(self.get_category_price(i[1]) for i in self.get_all_products())

    def __iter__(self):
        return iter(self.cur.execute("SELECT * FROM products").fetchall())


class AsyncPayment:
    def __init__(self, api_key):
        # self.url = "https://app-demo.payadmit.com/api/v1/payments/"  # test
        self.url = "https://app.payadmit.com/api/v1/payments/"  # prod
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def create_payment(self, amount, currency):
        async with aiohttp.ClientSession() as session:
            json = {"amount": amount,
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


payment = AsyncPayment(APIKEY)
