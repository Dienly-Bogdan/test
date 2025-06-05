# database.py

import sqlite3
import hashlib
from models import User, Category, Dish

DB_PATH = "pasta_pizza.db"
SCHEMA_PATH = "schema.sql"

def connect():
    return sqlite3.connect(DB_PATH)

def create_tables():
    with open(SCHEMA_PATH) as f:
        sql = f.read()
    conn = connect()
    conn.executescript(sql)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def register_user(email, name, password, is_admin=False):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO users (email, name, password_hash, is_admin) VALUES (?, ?, ?, ?)",
              (email, name, hash_password(password), int(is_admin)))
    conn.commit()
    conn.close()
    return True

def login_user(email, password):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND blocked=0", (email,))
    row = c.fetchone()
    conn.close()
    if row and row[3] == hash_password(password):
        return User(id=row[0], email=row[1], name=row[2], is_admin=bool(row[4]), blocked=bool(row[5]))
    return None

def get_user_by_id(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(id=row[0], email=row[1], name=row[2], is_admin=bool(row[4]), blocked=bool(row[5]))
    return None

def get_categories():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM categories")
    cats = [Category(*row) for row in c.fetchall()]
    conn.close()
    return cats

def get_category_by_id(cat_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM categories WHERE id=?", (cat_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return Category(*row)
    return None

def get_dishes(category_id=None):
    conn = connect()
    c = conn.cursor()
    if category_id:
        c.execute("SELECT * FROM dishes WHERE category_id=?", (category_id,))
    else:
        c.execute("SELECT * FROM dishes")
    dishes = [Dish(*row) for row in c.fetchall()]
    conn.close()
    return dishes

def get_dish_by_id(dish_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM dishes WHERE id=?", (dish_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return Dish(*row)
    return None

# Остальные методы (для заказов и отзывов) можно добавить по аналогии