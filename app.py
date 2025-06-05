import os
import sqlite3
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = "pizza17secret"
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DB_PATH = "pasta_pizza.db"

# === DATABASE HELPERS ===
def connect():
    # Возвращает соединение, где можно обращаться к полям как к словарю
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_categories():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name FROM categories ORDER BY name")
    cats = [dict(row) for row in c.fetchall()]
    conn.close()
    return cats

def get_dishes(category_id=None):
    conn = connect()
    c = conn.cursor()
    if category_id:
        c.execute("SELECT * FROM dishes WHERE category_id=? ORDER BY id DESC", (category_id,))
    else:
        c.execute("SELECT * FROM dishes ORDER BY id DESC")
    dishes = [dict(row) for row in c.fetchall()]
    conn.close()
    return dishes

def get_dish_by_id(dish_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM dishes WHERE id=?", (dish_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def register_user(email, name, password):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO users (email, name, password, is_admin) VALUES (?, ?, ?, 0)", (email, name, password))
    conn.commit()
    conn.close()
    return True

def login_user(email, password):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name, is_admin FROM users WHERE email=? AND password=?", (email, password))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "name": row["name"], "is_admin": bool(row["is_admin"])}
    return None

def get_orders(user_id=None):
    conn = connect()
    c = conn.cursor()
    if user_id:
        c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    else:
        c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return orders

def place_order(user_id, items, address, phone, delivery_time, payment_method):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, address, phone, status, created_at, payment_method, delivery_time) VALUES (?, ?, ?, ?, datetime('now'), ?, ?)",
              (user_id, address, phone, "Принят", payment_method, delivery_time))
    order_id = c.lastrowid
    for dish_id, qty in items.items():
        c.execute("INSERT INTO order_items (order_id, dish_id, qty) VALUES (?, ?, ?)", (order_id, dish_id, qty))
    conn.commit()
    conn.close()
    return order_id

def add_review(user_id, dish_id, rating, text):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO reviews (user_id, dish_id, rating, text, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
              (user_id, dish_id, rating, text))
    conn.commit()
    conn.close()

def get_reviews_for_dish(dish_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT r.rating, r.text, u.name, r.created_at FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.dish_id=? ORDER BY r.created_at DESC", (dish_id,))
    reviews = [dict(row) for row in c.fetchall()]
    conn.close()
    return reviews

# === DECORATORS ===
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def admin_required(f):
    def wrap(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Только для админа!")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# === AUTH ===
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = login_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["is_admin"] = user["is_admin"]
            return redirect(url_for("index"))
        else:
            flash("Неверная почта или пароль!")
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
        if register_user(email, name, password):
            flash("Регистрация успешна, войди!")
            return redirect(url_for("login"))
        else:
            flash("Пользователь уже есть!")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# === MAIN PAGES ===
@app.route("/")
def index():
    categories = get_categories()
    dishes = get_dishes()
    return render_template("index.html", categories=categories, dishes=dishes)



@app.route("/menu", methods=["GET", "POST"])
def menu():
    category_id = request.args.get("category_id")
    if category_id:
        dishes = get_dishes(category_id=int(category_id))
    else:
        dishes = get_dishes()
    categories = get_categories()
    return render_template("menu.html", dishes=dishes, categories=categories)

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# === CART ===
def get_cart():
    return session.get("cart", {})

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "POST":
        dish_id = request.form.get("dish_id")
        qty = int(request.form.get("qty", 1))
        cart = session.get("cart", {})
        cart[dish_id] = cart.get(dish_id, 0) + qty
        session["cart"] = cart
        session.modified = True
        return redirect(url_for("cart"))
    cart = get_cart()
    dish_ids = [int(did) for did in cart.keys()]
    dishes = [get_dish_by_id(did) for did in dish_ids]
    cart_items = [(dish, cart[str(dish["id"])]) for dish in dishes if dish]
    total = sum(dish["price"] * cart[str(dish["id"])] for dish in dishes if dish)
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/cart/remove/<int:dish_id>", methods=["POST"])
@login_required
def cart_remove(dish_id):
    cart = session.get("cart", {})
    cart.pop(str(dish_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))

# === ORDER ===
@app.route("/order", methods=["GET", "POST"])
@login_required
def order():
    cart = get_cart()
    if not cart:
        flash("Корзина пуста!")
        return redirect(url_for("cart"))
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        address = request.form.get("address")
        delivery_time = request.form.get("delivery_time")
        payment_method = request.form.get("payment_method")
        items = {int(k): v for k, v in cart.items()}
        order_id = place_order(session["user_id"], items, address, phone, delivery_time, payment_method)
        session["cart"] = {}
        flash(f"Заказ оформлен! Номер заказа {order_id}")
        return redirect(url_for("order_status", order_id=order_id))
    return render_template("order.html")

@app.route("/order/status/<int:order_id>")
@login_required
def order_status(order_id):
    orders = get_orders(user_id=session["user_id"])
    status = None
    for o in orders:
        if o["id"] == order_id:
            status = o["status"]
            break
    return render_template("order_status.html", order_id=order_id, status=status)

# === REVIEWS ===
@app.route("/review/<int:dish_id>", methods=["POST"])
@login_required
def add_review_route(dish_id):
    rating = int(request.form.get("rating", 5))
    text = request.form.get("text", "")
    add_review(session["user_id"], dish_id, rating, text)
    flash("Спасибо за отзыв!")
    return redirect(url_for("dish_detail", dish_id=dish_id))

@app.route("/dish/<int:dish_id>")
def dish_detail(dish_id):
    dish = get_dish_by_id(dish_id)
    reviews = get_reviews_for_dish(dish_id)
    return render_template("dish_detail.html", dish=dish, reviews=reviews)

# === ADMIN PANEL ===
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/manage_menu')
@admin_required
def admin_manage_menu():
    dishes = get_dishes()
    categories = get_categories()
    return render_template('admin/manage_menu.html', dishes=dishes, categories=categories)

@app.route('/admin/add_dish', methods=['GET', 'POST'])
@admin_required
def admin_add_dish():
    categories = get_categories()
    if not categories:
        flash("Сначала создайте хотя бы одну категорию!")
        return redirect(url_for("admin_manage_categories"))
    if request.method == "POST":
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        category_id = int(request.form.get('category_id', 0))
        if not category_id:
            flash("Выберите категорию!")
            return redirect(request.url)
        image = request.files.get('image')
        is_veg = int(request.form.get('is_veg', 0))
        is_spicy = int(request.form.get('is_spicy', 0))
        image_filename = None
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
        conn = connect()
        c = conn.cursor()
        c.execute("INSERT INTO dishes (title, description, price, category_id, image, is_veg, is_spicy) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (title, description, price, category_id, image_filename, is_veg, is_spicy))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_manage_menu'))
    return render_template('admin/add_dish.html', categories=categories)

@app.route('/admin/edit_dish/<int:dish_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_dish(dish_id):
    dish = get_dish_by_id(dish_id)
    categories = get_categories()
    if not dish:
        return "Нет такого блюда"
    if request.method == "POST":
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        category_id = int(request.form.get('category_id', 0))
        if not category_id:
            flash("Выберите категорию!")
            return redirect(request.url)
        is_veg = int(request.form.get('is_veg', 0))
        is_spicy = int(request.form.get('is_spicy', 0))
        image = request.files.get('image')
        image_filename = dish["image"]
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
        conn = connect()
        c = conn.cursor()
        c.execute("""UPDATE dishes SET title=?, description=?, price=?, category_id=?, image=?, is_veg=?, is_spicy=?
                     WHERE id=?""",
                  (title, description, price, category_id, image_filename, is_veg, is_spicy, dish_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_manage_menu'))
    return render_template('admin/edit_dish.html', dish=dish, categories=categories)

@app.route('/admin/delete_dish/<int:dish_id>', methods=['POST'])
@admin_required
def admin_delete_dish(dish_id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM dishes WHERE id=?", (dish_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_manage_menu'))

@app.route('/admin/manage_orders')
@admin_required
def admin_manage_orders():
    orders = get_orders()
    return render_template('admin/manage_orders.html', orders=orders)

@app.route('/admin/order_status/<int:order_id>', methods=['POST'])
@admin_required
def admin_order_status(order_id):
    new_status = request.form.get("status")
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_manage_orders'))

# === CATEGORIES MANAGEMENT ===
@app.route('/admin/manage_categories')
@admin_required
def admin_manage_categories():
    categories = get_categories()
    return render_template('admin/manage_categories.html', categories=categories)

@app.route('/admin/add_category', methods=['POST'])
@admin_required
def admin_add_category():
    name = request.form.get("name")
    if name:
        conn = connect()
        c = conn.cursor()
        c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_manage_categories'))

@app.route('/admin/delete_category/<int:cat_id>', methods=['POST'])
@admin_required
def admin_delete_category(cat_id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_manage_categories'))

# === STATIC FOR JS ===
@app.route('/static/js/<path:filename>')
def static_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'js'), filename)

# === CREATE TABLES IF NOT EXISTS ===
def create_tables():
    conn = connect()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        password TEXT,
        is_admin INTEGER DEFAULT 0
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS dishes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        price REAL,
        category_id INTEGER,
        image TEXT,
        is_veg INTEGER DEFAULT 0,
        is_spicy INTEGER DEFAULT 0,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        address TEXT,
        phone TEXT,
        status TEXT,
        created_at TEXT,
        payment_method TEXT,
        delivery_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        dish_id INTEGER,
        qty INTEGER,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(dish_id) REFERENCES dishes(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        dish_id INTEGER,
        rating INTEGER,
        text TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(dish_id) REFERENCES dishes(id)
    )""")
    conn.commit()
    conn.close()

create_tables()

# === RUN APP ===
if __name__ == "__main__":
    app.run(debug=True, port=8088)