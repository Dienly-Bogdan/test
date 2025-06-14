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
    print(f"Попытка входа: email={email}, password={password}")
    row = query_db("SELECT id, name, is_admin FROM users WHERE email=? AND password=?", (email, password), one=True)
    if row:
        print(f"Пользователь найден: {row['name']}")
        return {"id": row["id"], "name": row["name"], "is_admin": bool(row["is_admin"])}
    print("Пользователь не найден или пароль неверный")
    return None


def get_orders(user_id=None):
    if user_id:
        orders = query_db("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    else:
        orders = query_db("SELECT * FROM orders ORDER BY created_at DESC")
    return [dict(row) for row in orders]

def get_orders_manage_orders(user_id=None):
    if user_id:
        orders = query_db("""
        SELECT orders.*, users.name AS user_name
        FROM orders
        JOIN users ON orders.user_id = users.id
        WHERE user_id=?
        ORDER BY orders.created_at DESC
    """, (user_id,))
    else:
        orders = query_db("""
        SELECT orders.*, users.name AS user_name
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
    """)
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

@app.route("/login", methods=["GET", "POST"])
def login_register_combined():
    if request.method == "POST":
        action = request.form.get("form_type")
        email = request.form.get("email")
        password = request.form.get("password")

        if action == "login":
            user = login_user(email, password)
            if user:
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["is_admin"] = user["is_admin"]
                return redirect(url_for("index"))
            else:
                flash("Неверная почта или пароль!")
                return redirect(url_for("login_register_combined"))

        elif action == "register":
            name = request.form.get("name")
            if not (email and name and password):
                flash("Заполните все поля для регистрации!")
                return redirect(url_for("login_register_combined"))
            elif register_user(email, name, password):
                flash("Регистрация успешна, войдите!")
                return redirect(url_for("login_register_combined"))
            else:
                flash("Пользователь с такой почтой уже есть!")
                return redirect(url_for("login_register_combined"))

    return render_template("login.html")

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

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']

    orders_data = query_db("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))

    orders = []
    for order_row in orders_data:
        order_id = order_row['id']
        items_data = query_db("""
            SELECT dishes.title, dishes.price, order_items.qty
            FROM order_items 
            JOIN dishes ON order_items.dish_id = dishes.id
            WHERE order_items.order_id = ?
        """, (order_id,))

        items = []
        total = 0
        for item in items_data:
            items.append({
                'dish_title': item['title'],
                'price': item['price'],
                'qty': item['qty']
            })
            total += item['price'] * item['qty']

        orders.append({
            'id': order_id,
            'address': order_row['address'],
            'phone': order_row['phone'],
            'status': order_row['status'],
            'payment_method': order_row['payment_method'],
            'delivery_time': order_row['delivery_time'],
            'created_at': order_row['created_at'],
            'items': items,
            'total': total,
        })

    return render_template('orders.html', orders=orders)


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "POST":
        # Добавление в корзину
        dish_id = request.form.get("dish_id")
        qty = int(request.form.get("qty", 1))
        cart = session.get("cart", {})
        cart[dish_id] = cart.get(dish_id, 0) + qty
        session["cart"] = cart
        session.modified = True
        return '', 204

    # Получаем корзину из сессии
    cart = get_cart()

    # Получаем блюда из базы
    full_items = []
    total_price = 0

    for dish_id_str, qty in cart.items():
        dish = get_dish_by_id(int(dish_id_str))
        if dish:
            subtotal = dish["price"] * qty
            total_price += subtotal
            full_items.append({
                "id": dish["id"],
                "title": dish["title"],
                "price": dish["price"],
                "image": dish["image"],
                "quantity": qty,
                "subtotal": subtotal
            })

    return render_template("cart.html", cart_items=full_items, total=total_price)

@app.route("/cart/remove/<int:dish_id>", methods=["POST"])
@login_required
def cart_remove(dish_id):
    cart = session.get("cart", {})
    cart.pop(str(dish_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))

@app.route("/cart/update/<int:dish_id>", methods=["POST"])
@login_required
def cart_update_quantity(dish_id):
    qty = request.form.get("quantity", type=int)
    if not qty or qty < 1:
        qty = 1
    cart = session.get("cart", {})
    cart[str(dish_id)] = qty
    session["cart"] = cart
    session.modified = True
    return '', 204  # пустой успешный ответ


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

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not (name and phone and address):
            flash("Пожалуйста, заполните все поля", "error")
            return redirect(url_for("checkout"))

        cart = session.get("cart", {})
        if not cart:
            flash("Корзина пуста", "error")
            return redirect(url_for("cart"))

        # Тут логика сохранения заказа, например, в БД (можно доработать)
        # Для примера просто очистим корзину и покажем успех
        session.pop("cart", None)
        flash("Заказ успешно оформлен! Спасибо!", "success")
        return redirect(url_for("cart"))

    # GET — просто показать форму
    return render_template("checkout.html")

# --- Админка: категории, блюда, заказы ---
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price')
        category_id = request.form.get('category')
        image = ''  # Пока без загрузки файла, можно добавить потом

        if not (title and description and price and category_id):
            flash("Заполните все поля!", "error")
        else:
            cur.execute("""
                INSERT INTO dishes (title, description, price, category_id, image)
                VALUES (?, ?, ?, ?, ?)
            """, (title, description, float(price), int(category_id), image))
            conn.commit()
            flash("Блюдо добавлено!", "success")
            return redirect(url_for('dashboard'))

    cur.execute("SELECT id, name FROM categories")
    categories = cur.fetchall()

    cur.execute("""
        SELECT o.id, u.name, o.address, o.phone, o.status,
               GROUP_CONCAT(d.title || ' (x' || oi.qty || ')', ', ') AS items
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN order_items oi ON oi.order_id = o.id
        JOIN dishes d ON oi.dish_id = d.id
        WHERE o.status != 'Доставлен'
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """)
    orders = cur.fetchall()

    conn.close()

    return render_template('admin/dashboard.html', categories=categories, orders=orders)


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
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price_raw = request.form.get('price', '').strip()
        category_id_raw = request.form.get('category', '').strip()  # Обрати внимание, name="category"
        image = request.files.get('image')

        # Валидация
        if not title or not description or not price_raw or not category_id_raw:
            flash("Пожалуйста, заполните все обязательные поля!")
            return redirect(request.url)

        try:
            price = float(price_raw)
        except ValueError:
            flash("Цена должна быть числом!")
            return redirect(request.url)

        try:
            category_id = int(category_id_raw)
        except ValueError:
            flash("Выберите корректную категорию!")
            return redirect(request.url)

        image_filename = None
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        # Опционально — is_veg и is_spicy можно добавить, если есть в форме
        is_veg = int(request.form.get('is_veg', 0))
        is_spicy = int(request.form.get('is_spicy', 0))

        execute_db(
            "INSERT INTO dishes (title, description, price, category_id, image, is_veg, is_spicy) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, description, price, category_id, image_filename, is_veg, is_spicy)
        )

        flash("Блюдо успешно добавлено!")
        return '', 204  # пустой успешный ответ

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
    orders = get_orders_manage_orders()  # Должен возвращать и user_name!
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