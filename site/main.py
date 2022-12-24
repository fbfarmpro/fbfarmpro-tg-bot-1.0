from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
from utils.database import UsersDB, ProductsDB, payment, get_crypto_currency, Tokens
import threading
import time
from secrets import choice
from string import ascii_letters, digits

tokens = Tokens("../DB/tokens.db")
users = UsersDB("site", "../DB/users.db")
products = ProductsDB("../DB/products.db")

def create_random_token():
    # choose from all lowercase letter
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(10))


app = Flask(__name__)
app.secret_key = 'asdasdas?'



def checker_token(session):
    while True:
        if tokens.get(session['token'])[1] == "registered":
            flash('Logined succesfully!')
            redirect('/profile')
            thread.join()
        time.sleep(3)
@app.route("/")
def index():
    if 'userLogged' in session:
        return render_template("index.html", sost=7, logined=1 if 'userLogged' in session else 0)
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
        payments = users.get_payments(email=session['email'])
        return render_template("index.html", sost=5, username=session['email'].split('@')[0], balance=users.get_balance(email=session['email']), logined = 1 if 'userLogged' in session else 0)
    else:
        return redirect(url_for("loginpage"))

@app.route("/shop/category<id>")
def category():
    x = products.get_categories()
    return render_template("index.html", sost=6, items= items, logined = 1 if 'userLogged' in session else 0)



@app.route("/shop")
def shop():
    x = products.get_categories()
    items = []
    for item in x:
        items.append({
            "category": item[0],
            "desc": item[1],
            "cost": item[2]
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

@app.route("/telegram")
def tg_login():
    session['token'] = create_random_token()
    tokens.add(session['token'])
    thread = threading.Thread(target=checker_token, args=(session))
    thread.start()
    return redirect(f"https://t.me/fbfarmprobot?start={session['token']}")


@app.route("/buy", methods= ['POST'])
async def pay():
    if request.method == "POST":
        currency = request.form['currency']
        amount = 99 / await get_crypto_currency("btc")
        x = await payment.create_payment(amount, "btc".upper())
        #print(x)
        z = await payment.get_payment('38e5bbf032364feda3a31b3aeef8af7e')
        return x

if __name__ == '__main__':
    app.run()