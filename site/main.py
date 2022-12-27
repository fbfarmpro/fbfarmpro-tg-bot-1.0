import os
import time
from zipfile import ZipFile
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
import asyncio
from secrets import choice
from string import ascii_letters, digits
import sys
import logging
from flask_socketio import SocketIO, emit
import threading
from flask import jsonify, copy_current_request_context

logging.basicConfig(filename="log.txt", level=logging.DEBUG, format="%(asctime)s %(message)s")
sys.path.append("/root/fbfarmpro-tg-bot-1.0")

from utils.database import UsersDB, ProductsDB, payment, get_crypto_currency, Tokens, create_random_filename_zip
from config import MIN_MONEY_PER_BUY
from secret import sender, password
tokens = Tokens("../DB/tokens.db")
users = UsersDB("site", "../DB/users.db")
products = ProductsDB("../DB/products.db")

def create_random_token():
    # choose from all lowercase letter
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(10))


app = Flask(__name__)
app.secret_key = 'hhhkhkhkkh'
# app.config['SECRET_KEY'] = 'D20fndvfMK27^313787-AQl131'
app.config['SECRET_KEY'] = 'lksdjflaskjdhkjshg'

from flask_socketio import SocketIO, emit


socketio = SocketIO(app)


name_space = '/abcd'


def send_file(file, receiver_email):
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
        if session['method'] == "site":
            payments = users.get_payments(email=session['email'])
        return render_template("index.html", sost=5, username=session['email'].split('@')[0], balance=users.get_balance(email=session['email']), logined = 1 if 'userLogged' in session else 0)
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
            "category": item,
            "desc": products.get_category_description(item),
            "cost": products.get_category_price(item)
        })

    return render_template("index.html", sost=6, items = items, logined = 1 if 'userLogged' in session else 0)

@app.route("/create", methods = ['POST'])
def reg():
    if request.method == "POST":
        email = request.form['r-email']
        passwd = request.form['r-password']
        username = request.form['r-username']


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
        if users.is_registered(email=email, password=passwd) != None:

            reqEmail = users.is_registered(email=email, password=passwd)
            reqPasswd = users.is_registered(email=email, password=passwd)
            print(reqPasswd)

            if email == reqEmail and passwd == reqPasswd:
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

@app.route('/waitingtg')
def wait():
    tokens.add(session['token'])

    @copy_current_request_context
    def check_token():
        while True:
            try:
                status = tokens.get(session['token'])[1]
                if 'already' in status:
                    id = status.split("|")[1]
                    data = users.get_by_id(id)

                    user = {
                        'name': data[1],
                        'balance': data[5]
                    }
                    session['method'] = 'tg'
                    session['user'] = user
                    session['userLogged'] = True
                    socketio.emit('loginedtg', {}, namespace=name_space)

                    break
                else:
                    id = int(status)
                    if id:
                        data = users.get_by_id(id)

                        user = {
                            'name': data[1],
                            'balance': data[5]
                        }
                        session['method'] = 'tg'
                        session['user'] = user
                        session['userLogged'] = True
                        socketio.emit('loginedtg', {}, namespace=name_space)
            except:
                time.sleep(0.5)

    threading.Thread(target=check_token).start()
    return render_template("index.html", sost=9, logined = 1 if 'userLogged' in session else 0)

@app.route("/pay<name>")
def shopp(name):
    count = products.get_count_of_products(name)
    cost = products.get_category_price(name)
    return render_template("index.html", sost=8, logined=1 if 'userLogged' in session else 0, cost=cost, max=count, name=name)


@app.route("/telegram")
def tg_login():
    session['token'] = create_random_token()

    # return f"<script>window.open('https://t.me/fbfarmprobot?start={session['token']}', '_blank'); window.location.href = '/tglogin'</script>"
    return f"<script>window.open('https://t.me/fbfarmprobot?start={session['token']}', '_blank'); window.open('/waitingtg'); window.close();</script>"


@app.route("/addmee")
def addd():
    users.add_balance(email=session['email'], amount=1000)
    return redirect(url_for("profile"))

@app.route("/payment", methods= ['POST'])
def buy():
    if request.method == 'POST':
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
            send_file(zip_filename, session['email'])
            flash("Product(s) was(were) sended to your email!", "error")
            users.add_purchase(category_name, int(float(request.form['amount'])), int(float(request.form['price'])) * int(float(request.form['amount'])), zip_filename, email=session['email'])
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


