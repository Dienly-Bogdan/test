import os
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
)
from werkzeug.utils import secure_filename
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

def admin_required(f):
    def wrap(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Только для админа!")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# ------ AUTH ------
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

# ------ MAIN ------
@app.route("/")
def index():
    categories = db.get_categories()
    dishes = db.get_dishes()
    return render_template("index.html", categories=categories, dishes=dishes)

@app.route("/menu")
def menu():
    category_id = request.args.get("category_id")
    if category_id:
        dishes = db.get_dishes(category_id=int(category_id))
    else:
        dishes = db.get_dishes()
    categories = db.get_categories()
    return render_template("menu.html", dishes=dishes, categories=categories)

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ------ CART ------
def get_cart():
    return session.get("cart", {})

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    # Добавление блюда
    if request.method == "POST":
        dish_id = request.form.get("dish_id")
        qty = int(request.form.get("qty", 1))
        cart = session.get("cart", {})
        cart[dish_id] = cart.get(dish_id, 0) + qty
        session["cart"] = cart
        session.modified = True
        return redirect(url_for("cart"))
    # Отображение корзины
    cart = get_cart()
    dish_ids = [int(did) for did in cart.keys()]
    dishes = [db.get_dish_by_id(did) for did in dish_ids]
    cart_items = [(dish, cart[str(dish.id)]) for dish in dishes if dish]
    total = sum(dish.price * cart[str(dish.id)] for dish in dishes if dish)
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/cart/remove/<int:dish_id>", methods=["POST"])
@login_required
def cart_remove(dish_id):
    cart = session.get("cart", {})
    cart.pop(str(dish_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))

# ------ ORDER ------
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
        order_id = db.place_order(session["user_id"], items, address, phone, delivery_time, payment_method)
        session["cart"] = {}
        flash(f"Заказ оформлен! Номер заказа {order_id}")
        return redirect(url_for("order_status", order_id=order_id))
    return render_template("order.html")

@app.route("/order/status/<int:order_id>")
@login_required
def order_status(order_id):
    orders = db.get_orders(user_id=session["user_id"])
    status = None
    for o in orders:
        if o[0] == order_id:
            status = o[4]
            break
    return render_template("order_status.html", order_id=order_id, status=status)

# ------ REVIEWS ------
@app.route("/review/<int:dish_id>", methods=["POST"])
@login_required
def add_review(dish_id):
    rating = int(request.form.get("rating", 5))
    text = request.form.get("text", "")
    db.add_review(session["user_id"], dish_id, rating, text)
    flash("Спасибо за отзыв!")
    return redirect(url_for("dish_detail", dish_id=dish_id))

@app.route("/dish/<int:dish_id>")
def dish_detail(dish_id):
    dish = db.get_dish_by_id(dish_id)
    reviews = db.get_reviews_for_dish(dish_id)
    return render_template("dish_detail.html", dish=dish, reviews=reviews)

# ------ ADMIN PANEL ------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/manage_menu')
@admin_required
def admin_manage_menu():
    dishes = db.get_dishes()
    categories = db.get_categories()
    return render_template('admin/manage_menu.html', dishes=dishes, categories=categories)

@app.route('/admin/add_dish', methods=['GET', 'POST'])
@admin_required
def admin_add_dish():
    categories = db.get_categories()
    if request.method == "POST":
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        category_id = int(request.form['category_id'])
        image = request.files.get('image')
        is_veg = int(request.form.get('is_veg', 0))
        is_spicy = int(request.form.get('is_spicy', 0))
        image_filename = None
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
        conn = db.connect()
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
    dish = db.get_dish_by_id(dish_id)
    categories = db.get_categories()
    if not dish:
        return "Нет такого блюда"
    if request.method == "POST":
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        category_id = int(request.form['category_id'])
        is_veg = int(request.form.get('is_veg', 0))
        is_spicy = int(request.form.get('is_spicy', 0))
        image = request.files.get('image')
        image_filename = dish.image
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
        conn = db.connect()
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
    conn = db.connect()
    c = conn.cursor()
    c.execute("DELETE FROM dishes WHERE id=?", (dish_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_manage_menu'))

@app.route('/admin/manage_orders')
@admin_required
def admin_manage_orders():
    conn = db.connect()
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = c.fetchall()
    conn.close()
    return render_template('admin/manage_orders.html', orders=orders)

@app.route('/admin/order_status/<int:order_id>', methods=['POST'])
@admin_required
def admin_order_status(order_id):
    new_status = request.form.get("status")
    conn = db.connect()
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_manage_orders'))

# ------ STATIC FOR JS ------
@app.route('/static/js/<path:filename>')
def static_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'js'), filename)

# ------ START ------
if __name__ == "__main__":
    app.run(debug=True, port=8088)