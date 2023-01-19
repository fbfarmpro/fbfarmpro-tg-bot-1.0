import os
import random
import time
import logging
import smtplib
import ssl
import hashlib
import asyncio
from zipfile import ZipFile
from markupsafe import Markup
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from flask import Flask, session, redirect, url_for, request, render_template, flash, send_file
# from flask import escape
from json import loads, dumps
from secrets import choice
from string import ascii_letters, digits

import config
from utils.database import UsersDB, ProductsDB, payment, get_crypto_currency, Tokens, create_random_filename_zip
from config import MIN_MONEY_PER_BUY
from secret import sender, password
from aiogram.types import InputFile
from loader import bot

UPLOAD_FOLDER = config.AD_FOLDER
ALLOWED_EXTENSIONS = {'gif', 'png'}


# from flask import jsonify, copy_current_request_context

logging.basicConfig(filename="logsite.txt", level=logging.DEBUG, format="%(asctime)s %(message)s")


tokens = Tokens("DB/tokens.db")
users = UsersDB("site", "DB/users.db")
usersTG = UsersDB("tg", "DB/users.db")
products = ProductsDB("DB/products.db")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS\

def create_random_token():
    # choose from all lowercase letter
    letters = ascii_letters + digits
    return "".join(choice(letters) for _ in range(10))


app = Flask(__name__)
app.secret_key = 'hhasdhkhkhkkh'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# app.config['SECRET_KEY'] = 'D20fndvfMK27^313787-AQl131'


async def send_zip(document_id, file):
    await bot.send_document(document_id, InputFile(file))


def send_email_attachment(file, receiver_email):
    subject = "Your order"
    body = "Here is your purchase"
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    filename = f"DB/bought/{file}"  # In same directory as script

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

@app.route("/ref<ref>")
def ref(ref):
    link = tokens.get_link(ref)
    if link:
        session['ref'] = link
    else:
        flash("Invalid referal link!", "error")
    return redirect(url_for('sign_up'))
def send_mail(receiver, mail):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, mail)

@app.route('/ad<token>')
def ad(token):
    if token:
        token = tokens.get(token)
        if token:
            return render_template('index.html', sost = 15)

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part

        dtop = request.files.get('dtop', None)
        dbottom = request.files.get('dbottom', None)
        mbottom = request.files.get('mbottom', None)
        bg = request.files.get('bg', None)

        bottextru = request.form['bottextru']
        bottexten = request.form['bottexten']
        link = request.form['link']
        pack = request.form['packname']
        new_folder_path = os.path.join(config.AD_FOLDER, pack)
        os.mkdir(new_folder_path)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.

        if allowed_file(dtop.filename) and allowed_file(dbottom.filename) and allowed_file(mbottom.filename):
            path = os.path.join(config.AD_FOLDER, pack, config.AD_TEXT_FILENAME)
            content = {"ru": None, "en": None, "time": None, 'link': None}
            content["ru"] = bottextru
            content["en"] = bottexten
            content['link'] = link
            with open(path, "w") as file:
                file.write(dumps(content, ensure_ascii=False))
            dtp = secure_filename(config.AD_DESKTOP_TOP_FILENAME)
            dbttm = secure_filename(config.AD_DESKTOP_BOTTOM_FILENAME)
            mbttm = secure_filename(config.AD_MOBILE_FILENAME)
            b = secure_filename(config.SITE_BACKGROUND_FILENAME)
            dtop.save(os.path.join(app.config['UPLOAD_FOLDER'], pack, dtp))
            dbottom.save(os.path.join(app.config['UPLOAD_FOLDER'], pack, dbttm))
            mbottom.save(os.path.join(app.config['UPLOAD_FOLDER'], pack, mbttm))
            bg.save(os.path.join(app.config['UPLOAD_FOLDER'], pack, b))
            return redirect(url_for('index'))


@app.route("/tgauth<token>")
def telegauth(token):
    if token:
        status = tokens.get(token)[1]
        if 'done' in status:
            user_id = status.split("|")[1]
            data = users.get_by_id(user_id)

            userID = data[1]
            purchases = usersTG.get_purchase_history(userID=userID)
            purchase_history = [f"Date: {t[2]}\nCategory: {t[3].split('|')[-1]}\nAmount: {t[4]}\nPrice: {t[5]}" for
                                t in purchases]
            user = {
                'id': user_id,
                'balance': data[5],
                'payment_ids': data[6],
                'purchase_history': purchase_history
            }
            session['method'] = 'tg'
            session['user'] = user
            session['userLogged'] = True
            flash("Logged successfully!", "error")
            return redirect(url_for('profile'))
        elif "linked" in status:
            user_id = status.split("|")[1]
            email = status.split("|")[2]
            data = users.get_by_id(user_id)

            user = {
                'id': user_id,
                'email': email,
                'balance': data[5],
                'payment_ids': data[6]
            }
            session['method'] = 'all'
            session['user'] = user
            session['userLogged'] = True
            flash("Linked successfully!", "error")
            return redirect(url_for('profile'))
    else:
        redirect(url_for('profile'))

@app.route('/download<file>')
def download_file(file):
    path = os.path.join("DB", "bought", file)
    try:
        return send_file(path, as_attachment=True)
    except FileNotFoundError:
        flash("File download link expired!", "error")
        return redirect(url_for("profile"))

def readLink():
    with open(os.path.join(config.AD_FOLDER, config.AD_CURRENT_FOLDER, config.AD_TEXT_FILENAME), "r") as file:
        file_data = file.read()
        content = loads(file_data)
        link = content['link']
        return link
@app.route("/")
def index():

    return render_template("index.html", sost=1, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)


@app.route("/login")
def loginpage():
    if 'userLogged' in session:
        return redirect(url_for("profile"))
    else:
        return render_template("index.html", sost=3, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)


@app.route("/register")
def sign_up():
    if 'userLogged' in session:
        return redirect(url_for("profile"))
    else:
        return render_template("index.html", sost=4, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)


@app.route("/rules")
def rules():
    return render_template("index.html", sost=2, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)



@app.route("/profile")
def profile():
    if 'userLogged' in session:
        if session['method'] == "tg":
            purchases = usersTG.get_purchase_history(userID=session['user']['id'])
            purchase_history = [Markup(
                f"Date: {t[2]}<br>Category: {t[3].split('|')[-1]}<br>Amount: {t[4]}<br>Price: {t[5]}<br>File: <a href='/download{t[6]}'>Download</a>")
                for t in purchases]
            return render_template("index.html", sost=5, username=session['user']['id'],
                                   balance=usersTG.get_balance(userID=session['user']['id']),
                                   logined=1 if 'userLogged' in session else 0, history=purchase_history, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)
        elif session['method'] == 'all':
            purchases = users.get_purchase_history(email=session['user']['email'])
            purchase_history = [Markup(
                f"Date: {t[2]}<br>Category: {t[3].split('|')[-1]}<br>Amount: {t[4]}<br>Price: {t[5]}<br>File: <a href='/download{t[6]}'>Download</a>")
                for t in purchases]
            return render_template("index.html", sost=5, username=f"{session['user']['id']}|{session['user']['email']}",
                                   balance=users.get_balance(email=session['user']['email']),
                                   logined=1 if 'userLogged' in session else 0, history=purchase_history, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)
        else:
            purchases = users.get_purchase_history(email=session['email'])
            purchase_history = [Markup(
                f"Date: {t[2]}<br>Category: {t[3].split('|')[-1]}<br>Amount: {t[4]}<br>Price: {t[5]}<br>File: <a href='/download{t[6]}'>Download</a>")
                for t in purchases]
            return render_template("index.html", sost=5, username=session['email'].split('@')[0],
                                   balance=users.get_balance(email=session['email']),
                                   logined=1 if 'userLogged' in session else 0, history=purchase_history, tg = 1, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)
    else:
        return redirect(url_for("loginpage"))


@app.route("/order")
def order():
    return render_template("index.html", sost=7, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)


@app.route("/shop")
def shop():

    x = products.get_categories()
    items = []
    for item in x:
        items.append(
            {"category": item.split("|")[-1], "desc": products.get_category_description(item).split("|")[-1], "cost": products.get_category_price(item)})
    return render_template("index.html", sost=6, items=items, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME, guest=1 if 'isguest' in session else 0)



@app.route("/newpasswd", methods=['POST'])
def new():
    passw0 = request.form['password']
    passw1 = request.form['password0']
    email = tokens.get_email(token=session['resettoken'])[1]
    if passw0 == passw1:
        users.change_password(email=email, password=passw0)
        flash("Password changed successfully!", "error")
        return redirect(url_for("loginpage"))
    else:
        flash("Passwords do not match", "error")
        return redirect(request.url)


@app.route("/change<token>")
def changepage(token):
    if tokens.get_email(token=token):
        session['resettoken'] = token
        return render_template("index.html", sost=11, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)
    else:
        flash("Invalid url!", "error")
        return redirect(url_for("loginpage"))


@app.route("/sendpasswd", methods=['POST'])
def sendpass():
    email = request.form['email']
    if users.is_registered(email=email):
        token = create_random_token()
        tokens.add_email(token=token, email=email)
        msg = MIMEText(f'Your link for change: <a href="{request.url_root}change{token}">Change</a>', 'html')
        msg['Subject'] = 'Reset password'
        msg['From'] = 'fb-farm.pro'
        msg['To'] = email

        send_mail(email, msg.as_string())
        flash("Link sended to your email!", "error")
        return redirect(url_for("loginpage"))
    else:
        flash("User is not exists!", "error")
        return redirect(url_for("loginpage"))


@app.route("/sendcode", methods=['POST'])
def code():
    if request.method == "POST":
        email = request.form['r-email']
        passwd = request.form['r-password']
        session['mEmail'] = email
        session['mPasswd'] = passwd
        code = random.randint(10000, 99999)
        send_mail(email, f"Your code for verification: {code}")
        session['mCode'] = code
        flash("Code was sended to your email!", "error")
        return redirect(url_for('verify'))
@app.route("/verify")
def verify():
    return render_template('index.html', sost = 12, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)


@app.route("/forgot")
def forgot():
    return render_template("index.html", sost=10, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)


@app.route("/create", methods=['POST'])
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
            send_mail(email, "Thanks for registration!")
            return redirect(url_for("profile"))


@app.route("/auth", methods=['POST'])
def auth():
    if request.method == "POST":
        email = request.form['a-email']
        passwd = request.form['a-password']
        if users.is_registered(email=email):
            user = users.is_registered(email=email)
            reqEmail = user[2]
            reqPasswd = user[3]
            id = user[1]
            if id:
                if email == reqEmail and hashlib.sha256(passwd.encode()).hexdigest() == reqPasswd:
                    data = users.get_by_id(id)

                    user = {
                        'id': id,
                        'email': email,
                        'balance': data[5],
                        'payment_ids': data[6]
                    }
                    session['method'] = 'all'
                    session['user'] = user
                    session['userLogged'] = True
                    return redirect(url_for("profile"))
                else:
                    flash("Invalid password!", "error")
                    return redirect(url_for("loginpage"))
            else:

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


@app.route("/link")
def link_tg():
    session['token'] = create_random_token()
    tokens.add(session['token'])
    tokens.set_status(session['token'], f"link|{session['email']}")
    return redirect(f"https://t.me/fbfarmprobot?start={session['token']}")




@app.route("/telegram")
def tg_login():
    session['token'] = create_random_token()
    tokens.add(session['token'])

    # return f"<script>window.open('https://t.me/fbfarmprobot?start={session['token']}', '_blank'); window.location.href = '/tglogin'</script>"
    return redirect(f"https://t.me/fbfarmprobot?start={session['token']}")

@app.route("/pay<name>")
def shopp(name):

    for category in products.get_categories():
        if name in category:
            name = category
            break
    count = products.get_count_of_products(name)
    cost = products.get_category_price(name)
    return render_template("index.html", sost=8, logined=1 if 'userLogged' in session else 0, cost=cost, max=count,
                               name=name.split("|")[-1], mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)


@app.route("/balance")
def balance():
    if 'userLogged' in session:
        return render_template("index.html", sost=7, logined=1 if 'userLogged' in session else 0, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)
    else:
        return redirect(url_for("loginpage"))
@app.route("/setguest")
def setguest():
    session['isguest'] = True
    return render_template('index.html', sost = 13, mobile = config.AD_MOBILE_FILENAME, ad_link = readLink(), pc_top = config.AD_DESKTOP_TOP_FILENAME, pc_bottom = config.AD_DESKTOP_BOTTOM_FILENAME, bg = config.SITE_BACKGROUND_FILENAME)

@app.route("/setmail", methods = ['POST'])
def setguestmail():
    session['email'] = request.form['email']
    return redirect(url_for('shop'))

@app.route("/addmee")
def addd():
    if session['method'] == 'site':
        users.add_balance(email=session['email'], amount=100)
    else:
        users.add_balance(userID=session['user']['id'], amount=100)
    return redirect(url_for("profile"))


@app.route("/payment", methods=['POST'])
async def buy():
    if 'userLogged' in session:
        if request.method == 'POST':
            category_name = request.form['name']
            coupon = request.form['coupon']
            if coupon:
                promo = products.get_coupon(coupon)
                if promo:
                    for category in products.get_categories():
                        if category_name in category:
                            category_name = category
                            break
                    if session['method'] == "tg":


                        cost = int(float(request.form['price'])) * int(float(request.form['amount']))
                        if promo[1] == 'percent':
                            cost = cost - (cost * promo[2] / 100)
                            flash(f'You used a promo code for -{promo[2]}% off!', 'error')
                        elif promo[1] == 'summ':
                            usersTG.add_balance(promo[2], userID=session['user']['id'])
                            flash(f'{promo[2]} was added to your balance!', 'error')
                        products.remove_coupon(promo[0])
                        balance = usersTG.get_balance(userID=session['user']['id'])
                        if cost <= balance:
                            usersTG.add_balance(-cost, userID=session['user']['id'])
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
                                                 int(float(request.form['price'])) * int(float(request.form['amount'])),
                                                 zip_filename,
                                                 userID=session['user']['id'])
                            return redirect(url_for('profile'))
                        else:
                            flash("Please replenish the balance!", "error")
                            return redirect(url_for('profile'))
                    else:
                        # category_name = request.form['name']

                        cost = int(float(request.form['price'])) * int(float(request.form['amount']))
                        if promo[1] == 'percent':
                            cost = cost - (cost * promo[2] / 100)
                            flash(f'You used a promo code for -{promo[2]}% off!', 'error')
                        elif promo[1] == 'summ':
                            users.add_balance(promo[2], email=session['email'])
                            flash(f'{promo[2]} was added to your balance!', 'error')
                        products.remove_coupon(promo[0])
                        balance = users.get_balance(email=session['email'])
                        if cost <= balance:
                            users.add_balance(-cost, email=session['email'])
                            zip_filename = create_random_filename_zip()
                            zip_path = os.path.join("DB", "bought", zip_filename)
                            zipObj = ZipFile(zip_path, "w")
                            for file in products.get_N_products(category_name, int(float(request.form['amount']))):
                                path = os.path.join("DB", category_name, file[0])
                                zipObj.write(path, os.path.basename(path))
                                products.set_isBought(file[0], category_name)
                            zipObj.close()
                            send_email_attachment(zip_filename, session['email'])
                            flash("Product(s) was(were) sended to your email!", "error")
                            # await get_crypto_currency("btc")

                            users.add_purchase(category_name, int(float(request.form['amount'])),
                                               int(float(request.form['price'])) * int(float(request.form['amount'])),
                                               zip_filename,
                                               email=session['email'])
                            return redirect(url_for('profile'))
                        else:
                            flash("Please replenish the balance!", "error")
                            return redirect(url_for('profile'))
                else:
                    flash('Coupon/Promocode not exists!', 'error')
                    return redirect(url_for('profile'))
            else:
                for category in products.get_categories():
                    if category_name in category:
                        category_name = category
                        break
                if session['method'] == "tg":
                    balance = usersTG.get_balance(userID=session['user']['id'])
                    cost = int(float(request.form['price'])) * int(float(request.form['amount']))
                    if cost <= balance:
                        usersTG.add_balance(-cost, userID=session['user']['id'])
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
                                             int(float(request.form['price'])) * int(float(request.form['amount'])),
                                             zip_filename,
                                             userID=session['user']['id'])
                        return redirect(url_for('profile'))
                    else:
                        flash("Please replenish the balance!", "error")
                        return redirect(url_for('profile'))
                else:
                    # category_name = request.form['name']
                    balance = users.get_balance(email=session['email'])
                    cost = int(float(request.form['price'])) * int(float(request.form['amount']))
                    if cost <= balance:
                        users.add_balance(-cost, email=session['email'])
                        zip_filename = create_random_filename_zip()
                        zip_path = os.path.join("DB", "bought", zip_filename)
                        zipObj = ZipFile(zip_path, "w")
                        for file in products.get_N_products(category_name, int(float(request.form['amount']))):
                            path = os.path.join("DB", category_name, file[0])
                            zipObj.write(path, os.path.basename(path))
                            products.set_isBought(file[0], category_name)
                        zipObj.close()
                        send_email_attachment(zip_filename, session['email'])
                        flash("Product(s) was(were) sended to your email!", "error")
                        # await get_crypto_currency("btc")

                        users.add_purchase(category_name, int(float(request.form['amount'])),
                                           int(float(request.form['price'])) * int(float(request.form['amount'])),
                                           zip_filename,
                                           email=session['email'])
                        return redirect(url_for('profile'))
                    else:
                        flash("Please replenish the balance!", "error")
                        return redirect(url_for('profile'))


        else:
            return redirect(url_for('profile'))
    else:
        category_name = request.form['name']
        for category in products.get_categories():
            if category_name in category:
                category_name = category
                break
        cost = int(float(request.form['price'])) * int(float(request.form['amount']))

        zip_filename = create_random_filename_zip()
        zip_path = os.path.join("DB", "bought", zip_filename)
        zipObj = ZipFile(zip_path, "w")
        for file in products.get_N_products(category_name, int(float(request.form['amount']))):
            path = os.path.join("DB", category_name, file[0])
            zipObj.write(path, os.path.basename(path))
            products.set_isBought(file[0], category_name)
        zipObj.close()
        price = await get_crypto_currency('trx'.upper())
        x = await payment.create_payment((cost/price), "trx".upper())

        tokens.add_payment(payment_id=x['result']['id'], email=session['email'], zipname=zip_filename)
        return redirect(f"{x['result']['redirectUrl']}'")



@app.route("/buy", methods=['POST'])
async def pay():
    if request.method == "POST":
        currency = request.form['currency']
        amount = int(float(request.form['amount']))
        if currency in MIN_MONEY_PER_BUY and amount >= MIN_MONEY_PER_BUY[currency]:
            price = await get_crypto_currency(currency) if currency != "usdt" else 1
            amount = amount / price
            x = await payment.create_payment(amount, currency.upper())
            return redirect(f"{x['result']['redirectUrl']}'")
        else:
            flash(f'Minimum amount for {currency} is {MIN_MONEY_PER_BUY[currency]}$', 'error')
            return redirect(url_for("order"))


if __name__ == '__main__':
    # from waitress import serve
    # socketio.run(app, host='0.0.0.0', port=5000)
    app.run(host="0.0.0.0", port=5000)
