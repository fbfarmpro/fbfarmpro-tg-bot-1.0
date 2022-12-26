from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
import asyncio
from secrets import choice
from string import ascii_letters, digits
import sys
import logging
from flask_socketio import SocketIO, emit
import threading

from flask import request, jsonify, copy_current_request_context

logging.basicConfig(filename="log.txt", level=logging.DEBUG, format="%(asctime)s %(message)s")
sys.path.append("/root/fbfarmpro-tg-bot-1.0")

from utils.database import UsersDB, ProductsDB, payment, get_crypto_currency, Tokens


tokens = Tokens("../DB/tokens.db")
users = UsersDB("site", "../DB/users.db")
products = ProductsDB("../DB/products.db")

def create_random_token():
    # choose from all lowercase letter
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(10))


app = Flask(__name__)
app.secret_key = 'asdasdas?'
app.config['SECRET_KEY'] = 'D20fndvfMK27^313787-AQl131'

from flask_socketio import SocketIO, emit


socketio = SocketIO(app)


name_space = '/abcd'






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

@app.route("/order<name>")
def order(name):
    count = products.get_count_of_products(name)
    cost = products.get_category_price(name)
    return render_template("index.html", sost=7, logined=1 if 'userLogged' in session else 0, cost=cost, max=count, name=name)

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

@app.route("/test")
def test():
    products.create_category("name", "desc", 2 )
    return redirect(url_for("shop"))

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
            except:
                # asyncio.sleep(2)
                tokens.db.close()
                tokens.db.connect("../DB/products.db")

    threading.Thread(target=check_token).start()
    return render_template("index.html", sost=60, logined = 1 if 'userLogged' in session else 0)

@app.route("/telegram")
def tg_login():
    session['token'] = create_random_token()

    # return f"<script>window.open('https://t.me/fbfarmprobot?start={session['token']}', '_blank'); window.location.href = '/tglogin'</script>"
    return f"<script>window.open('https://t.me/fbfarmprobot?start={session['token']}', '_blank'); window.open('/waitingtg')</script>"



@app.route("/buy", methods= ['POST'])
async def pay():
    if request.method == "POST":
        currency = request.form['currency']
        amount = (int(request.form['cost'])*int(request.form['amount'])) / await get_crypto_currency(currency)
        x = await payment.create_payment(amount, "btc".upper())
        return x

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
<<<<<<< HEAD
    socketio.run(app, host='0.0.0.0')
=======
    socketio.run(app, host="0.0.0.0")
>>>>>>> a9a2a1686b6e63716e053c33fc329c3c62d1fa26
