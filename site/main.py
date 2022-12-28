import os
import time
from zipfile import ZipFile
import email, smtplib, ssl
from markupsafe import Markup
import hashlib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, session, redirect, url_for, escape, request, render_template, flash, send_file
import asyncio
from secrets import choice
from string import ascii_letters, digits
import sys
import logging
from flask_socketio import SocketIO, emit
import threading
from flask import jsonify, copy_current_request_context

logging.basicConfig(filename="logsite.txt", level=logging.DEBUG, format="%(asctime)s %(message)s")
sys.path.append("/root/fbfarmpro-tg-bot-1.0")

from utils.database import UsersDB, ProductsDB, payment, get_crypto_currency, Tokens, create_random_filename_zip
from config import MIN_MONEY_PER_BUY
from secret import sender, password
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from secret import TOKEN
from flask_socketio import SocketIO, emit
from aiogram.types import InputFile
from loader import bot
tokens = Tokens("DB/tokens.db")
users = UsersDB("site", "DB/users.db")
usersTG = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")

def create_random_token():
    # choose from all lowercase letter
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(10))


app = Flask(__name__)
app.secret_key = 'nnnnnnnnnnnkjlkj'
# app.config['SECRET_KEY'] = 'D20fndvfMK27^313787-AQl131'
app.config['SECRET_KEY'] = '80h908h908ijh0ij'


socketio = SocketIO(app)


name_space = '/abcd'

async def send_zip(id, file):
    await bot.send_document(id, InputFile(file))

def sendfile(file, receiver_email):
    subject = "Your order"
    body = "Here is your purchase"
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    filename = f"../DB/bought/{file}"  # In same directory as script

    # Open PDF file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver_email, text)


async def check_token():
    while True:
        try:

            status = tokens.get(session['token'])[1]
            if "done" in status:

                id = status.split("|")[1]
                data = users.get_by_id(id)

                userID = data[1]
                purchases = usersTG.get_purchase_history(userID=userID)
                purchase_history = [f"Date: {t[2]}\nCategory: {t[3].split('|')[-1]}\nAmount: {t[4]}\nPrice: {t[5]}" for t in purchases]
                user = {
                    'id': id,
                    'balance': data[5],
                    'payment_ids': data[6],
                    'purchase_history': purchase_history
                }
                session['method'] = 'tg'
                session['user'] = user
                session['userLogged'] = True
                flash("logined succefully!", "error")
                await get_crypto_currency("btc")
                break
        except:
            await get_crypto_currency("btc")
            time.sleep(0.5)


@app.route('/download<file>')
def downloadFile(file):

    path = os.path.join("..", "DB", "bought", file)
    try:
        return send_file(path, as_attachment=True)
    except:
        flash("File download link expired!", "error")
        return redirect(url_for("profile"))

@app.route("/")
def index():
    if 'userLogged' in session:
        return render_template("index.html", sost=1, logined=1 if 'userLogged' in session else 0)
    else:
        return redirect(url_for("profile"))

@app.route("/login")
def loginpage():
    if 'userLogged' in session:
        return redirect(url_for("profile"))
    else:
        return render_template("index.html", sost=3, logined = 1 if 'userLogged' in session else 0)

@app.route("/register")
def sign_up():
    return render_template("index.html", sost=4, logined = 1 if 'userLogged' in session else 0)

@app.route("/rules")
def rules():
    return render_template("index.html", sost=2, logined = 1 if 'userLogged' in session else 0)

@app.route("/profile")
def profile():
    if 'userLogged' in session:
        if session['method'] == "tg":
            purchases = usersTG.get_purchase_history(userID=session['user']['id'])
            purchase_history = [Markup(f"Date: {t[2]}<br>Category: {t[3].split('|')[-1]}<br>Amount: {t[4]}<br>Price: {t[5]}<br>File: <a href='/download{t[6]}'>Download</a>") for t in purchases]
            return render_template("index.html", sost=5, username=session['user']['id'],
                                   balance=usersTG.get_balance(userID=session['user']['id']),
                                   logined=1 if 'userLogged' in session else 0, history = purchase_history)
        else:
            purchases = users.get_purchase_history(email=session['email'])
            purchase_history = [Markup(f"Date: {t[2]}<br>Category: {t[3].split('|')[-1]}<br>Amount: {t[4]}<br>Price: {t[5]}<br>File: <a href='/download{t[6]}>Download</a>'") for t in purchases]
        return render_template("index.html", sost=5, username=session['email'].split('@')[0], balance=users.get_balance(email=session['email']), logined = 1 if 'userLogged' in session else 0, history = purchase_history)
    else:
        return redirect(url_for("loginpage"))

@app.route("/order")
def order():
    return render_template("index.html", sost=7, logined=1 if 'userLogged' in session else 0)

@app.route("/shop")
def shop():
    x = products.get_categories()
    items = []
    for item in x:
        items.append({
            "category": item.split("|")[-1],
            "desc": products.get_category_description(item).split("|")[-1],
            "cost": products.get_category_price(item)
        })

    return render_template("index.html", sost=6, items = items, logined = 1 if 'userLogged' in session else 0)

@app.route("/create", methods = ['POST'])
def reg():
    if request.method == "POST":
        email = request.form['r-email']
        passwd = request.form['r-password']


        if users.is_registered(email=email):
            flash("User is already exists!", "error")

            return redirect(url_for("sign_up"))

        else:
            users.register(email=email, password=passwd)
            session['userLogged'] = True
            session['email'] = email
            session['method'] = "site"
            return redirect(url_for("profile"))


@app.route("/auth", methods = ['POST'])
def auth():
    if request.method == "POST":
        email = request.form['a-email']
        passwd = request.form['a-password']
        if users.is_registered(email=email):
            reqEmail = users.is_registered(email=email)[2]
            reqPasswd = users.is_registered(email=email)[3]

            if email == reqEmail and hashlib.sha256(passwd.encode()).hexdigest() == reqPasswd:
                session['userLogged'] = True
                session['email'] = email
                session['method'] = "site"
                return redirect(url_for("profile"))
            else:

                flash("Invalid password!", "error")
                return redirect(url_for("loginpage"))
        else:
            flash("User is not exists!", "error")
            return redirect(url_for("loginpage"))

@app.route("/logout")
def logout():
    session.pop("userLogged", None)
    return redirect(url_for("index"))

@app.route("/tglogin")
def tg():

    tokens.add(session['token'])
    loop = asyncio.new_event_loop()
    loop.run_until_complete(check_token())
    return redirect('/profile')

@app.route("/telegram")
def tg_login():
    session['token'] = create_random_token()
    # return f"<script>window.open('https://t.me/fbfarmprobot?start={session['token']}', '_blank'); window.location.href = '/tglogin'</script>"
    return f"<script>window.open('https://t.me/fbfarmprobot?start={session['token']}', '_blank'); window.open('/tglogin'); window.close();</script>"
@app.route("/pay<name>")
def shopp(name):
    for category in products.get_categories():
        if name in category:
            name = category
            break
    count = products.get_count_of_products(name)
    cost = products.get_category_price(name)
    return render_template("index.html", sost=8, logined=1 if 'userLogged' in session else 0, cost=cost, max=count, name=name)



@app.route("/addmee")
def addd():
    if session['method'] == 'site':
        users.add_balance(email=session['email'], amount=100)
    else:
        users.add_balance(userID=session['user']['id'], amount=100)
    return redirect(url_for("profile"))

@app.route("/payment", methods= ['POST'])
async def buy():
    if request.method == 'POST':
        if session['method'] == "tg":

            print(session['user']['id'])
            category_name = request.form['name']
            balance = usersTG.get_balance(userID=session['user']['id'])
            cost = int(float(request.form['price'])) * int(float(request.form['amount']))
            if cost <= balance:
                usersTG.add_balance(-(cost), userID = session['user']['id'])
                zip_filename = create_random_filename_zip()
                zip_path = os.path.join("DB", "bought", zip_filename)
                print(zip_path)
                zipObj = ZipFile(zip_path, "w")
                for file in products.get_N_products(category_name, int(float(request.form['amount']))):
                    path = os.path.join("DB", category_name, file[0])
                    zipObj.write(path, os.path.basename(path))
                    products.set_isBought(file[0], category_name)
                zipObj.close()
                await send_zip(session['user']['id'], zip_path)
                flash("Product(s) was(were) sended to your Telegram!", "error")
                usersTG.add_purchase(category_name, int(float(request.form['amount'])),
                                   int(float(request.form['price'])) * int(float(request.form['amount'])), zip_filename,
                                   userID=session['user']['id'])
                return redirect(url_for('profile'))
            else:
                flash("Please replenish the balance!", "error")
                return redirect(url_for('profile'))
        else:
            category_name = request.form['name']
            balance = users.get_balance(email=session['email'])
            cost = int(float(request.form['price'])) * int(float(request.form['amount']))
            if cost <= balance:
                users.add_balance(-(cost), email=session['email'])
                zip_filename = create_random_filename_zip()
                zip_path = os.path.join("..", "DB", "bought", zip_filename)
                zipObj = ZipFile(zip_path, "w")
                for file in products.get_N_products(category_name, int(float(request.form['amount']))):
                    path = os.path.join("..", "DB", category_name, file[0])
                    zipObj.write(path, os.path.basename(path))
                    products.set_isBought(file[0], category_name)
                zipObj.close()
                sendfile(zip_path, session['email'])
                flash("Product(s) was(were) sended to your email!", "error")
                await get_crypto_currency("btc")

                users.add_purchase(category_name, int(float(request.form['amount'])), int(float(request.form['price'])) * int(float(request.form['amount'])), zip_filename, email=session['email'])
                return redirect(url_for('profile'))
            else:
                flash("Please replenish the balance!", "error")
                return redirect(url_for('profile'))

    else:
        return redirect(url_for('profile'))
@app.route("/buy", methods= ['POST'])
async def pay():
    if request.method == "POST":
        currency = request.form['currency']
        amount = int(float(request.form['amount']))
        if currency in MIN_MONEY_PER_BUY and amount >= MIN_MONEY_PER_BUY[currency]:
            amount = int(float(request.form['amount'])) / await get_crypto_currency(currency)

            x = await payment.create_payment(amount, currency.upper())
            return f"<script>window.open('{x['result']['redirectUrl']}', '_blank'); window.open('/profile'); window.close();</script>"
        else:
            flash(f'Minimum amount for {currency} is {MIN_MONEY_PER_BUY[currency]}$', 'error')
            return redirect(url_for("order"))

async def check_for_payments():
    while True:
        payment_ids = users.get_payments(email=session['email'])
        for payment_id in payment_ids:
            payment_data = await payment.get_payment(payment_id)
            payment_data = payment_data.get("result", None)
            if not payment_data:
                users.remove_payment(payment_id, email=session['email'])
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
                users.add_balance(amount, email=session['email'])
                users.remove_payment(payment_id, email=session['email'])
                await socketio.emit('purchaseexpired', {}, namespace=name_space)
            elif status == "DECLINED" or status == "CANCELLED":
                await socketio.emit('purchaseexpired', {}, namespace=name_space)

                users.remove_payment(id, email=session['email'])

        await asyncio.sleep(30)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')


