import os
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, g
)
from werkzeug.utils import secure_filename

from database import get_db, close_db, init_db, query_db, execute_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "pizza17secret"
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.before_request
def before_request():
    get_db()

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

@app.cli.command("init-db")
def initdb_command():
    """Инициализация базы данных из schema.sql"""
    init_db()
    print("База данных инициализирована.")

def get_categories():
    cats = query_db("SELECT id, name FROM categories ORDER BY name")
    return [dict(row) for row in cats]

def get_dishes(category_id=None):
    if category_id:
        dishes = query_db("SELECT * FROM dishes WHERE category_id=? ORDER BY id DESC", (category_id,))
    else:
        dishes = query_db("SELECT * FROM dishes ORDER BY id DESC")
    return [dict(row) for row in dishes]

def get_dish_by_id(dish_id):
    row = query_db("SELECT * FROM dishes WHERE id=?", (dish_id,), one=True)
    return dict(row) if row else None

def register_user(email, name, password):
    if query_db("SELECT id FROM users WHERE email=?", (email,), one=True):
        return False
    execute_db("INSERT INTO users (email, name, password, is_admin) VALUES (?, ?, ?, 0)", (email, name, password))
    return True

def login_user(email, password):
    row = query_db("SELECT id, name, is_admin FROM users WHERE email=? AND password=?", (email, password), one=True)
    if row:
        return {"id": row["id"], "name": row["name"], "is_admin": bool(row["is_admin"])}
    return None

def get_orders(user_id=None):
    if user_id:
        orders = query_db("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    else:
        orders = query_db("SELECT * FROM orders ORDER BY created_at DESC")
    return [dict(row) for row in orders]

def place_order(user_id, items, address, phone, delivery_time, payment_method):
    order_id = execute_db(
        "INSERT INTO orders (user_id, address, phone, status, created_at, payment_method, delivery_time) VALUES (?, ?, ?, ?, datetime('now'), ?, ?)",
        (user_id, address, phone, "Принят", payment_method, delivery_time))
    for dish_id, qty in items.items():
        execute_db("INSERT INTO order_items (order_id, dish_id, qty) VALUES (?, ?, ?)", (order_id, dish_id, qty))
    return order_id

def add_review(user_id, dish_id, rating, text):
    execute_db("INSERT INTO reviews (user_id, dish_id, rating, text, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
              (user_id, dish_id, rating, text))

def get_reviews_for_dish(dish_id):
    reviews = query_db(
        "SELECT r.rating, r.text, u.name, r.created_at FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.dish_id=? ORDER BY r.created_at DESC",
        (dish_id,))
    return [dict(row) for row in reviews]

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

# --- Routes (оставь без изменений, только вызывай функции выше) ---

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

@app.route("/")
def index():
    categories = get_categories()
    dishes = get_dishes()
    return render_template("index.html", categories=categories, dishes=dishes)

@app.route("/menu")
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

# --- Админка: категории, блюда, заказы ---
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
        execute_db("INSERT INTO dishes (title, description, price, category_id, image, is_veg, is_spicy) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (title, description, price, category_id, image_filename, is_veg, is_spicy))
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
        execute_db("""UPDATE dishes SET title=?, description=?, price=?, category_id=?, image=?, is_veg=?, is_spicy=?
                     WHERE id=?""",
                  (title, description, price, category_id, image_filename, is_veg, is_spicy, dish_id))
        return redirect(url_for('admin_manage_menu'))
    return render_template('admin/edit_dish.html', dish=dish, categories=categories)

@app.route('/admin/delete_dish/<int:dish_id>', methods=['POST'])
@admin_required
def admin_delete_dish(dish_id):
    execute_db("DELETE FROM dishes WHERE id=?", (dish_id,))
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
    execute_db("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    return redirect(url_for('admin_manage_orders'))

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
        execute_db("INSERT INTO categories (name) VALUES (?)", (name,))
    return redirect(url_for('admin_manage_categories'))

@app.route('/admin/delete_category/<int:cat_id>', methods=['POST'])
@admin_required
def admin_delete_category(cat_id):
    execute_db("DELETE FROM categories WHERE id=?", (cat_id,))
    return redirect(url_for('admin_manage_categories'))

if __name__ == "__main__":
    app.run(debug=True, port=8088)