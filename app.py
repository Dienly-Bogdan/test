# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import database as db
from models import Dish

db.create_tables()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = "pizza17secret"
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route("/")
def index():
    categories = db.get_categories()
    dishes = db.get_dishes()
    return render_template("index.html", categories=categories, dishes=dishes)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.login_user(email, password)
        if user:
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["is_admin"] = user.is_admin
            return redirect(url_for("index"))
        else:
            flash("Неверная почта или пароль!")
            return redirect(request.url)
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")
        if not (email and name and password):
            flash("Заполни все поля!")
            return redirect(request.url)
        if db.register_user(email, name, password):
            flash("Регистрация успешна, войди!")
            return redirect(url_for("login"))
        else:
            flash("Пользователь уже есть!")
            return redirect(request.url)
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/menu")
def menu():
    category_id = request.args.get("category_id")
    if category_id:
        dishes = db.get_dishes(category_id=int(category_id))
    else:
        dishes = db.get_dishes()
    categories = db.get_categories()
    return render_template("menu.html", dishes=dishes, categories=categories)

# Остальные руты (корзина, заказы, админка) добавь аналогично

if __name__ == "__main__":
    app.run(debug=True, port=8088)